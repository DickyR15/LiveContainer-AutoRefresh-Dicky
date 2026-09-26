#!/usr/bin/env python3
from pathlib import Path
import sys

AUTH_MARKER = "DPORT_AUTH_SESSION_RECOVERY_IOS27_V6"
PROXY_MARKER = "DPORT_PROXY_SESSION_RECOVERY_IOS27_V1"


def fail(message: str) -> None:
    raise SystemExit("patch_auth_session_recovery: " + message)


def patch_auth_manager(root: Path) -> None:
    path = root / "SideStore/Core/Auth/AuthManager.swift"
    if not path.exists():
        fail(f"missing AuthManager.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if AUTH_MARKER in text:
        print("AuthManager session recovery V6: already patched")
        return

    if "DPORT_AUTH_SESSION_RECOVERY_IOS27_V4" in text or "DPORT_AUTH_SESSION_RECOVERY_IOS27_V5" in text:
        fail("stale custom AuthManager recovery patch is present; start from the pinned clean SideStore source")

    anchor = """    public func getAuthenticatedTeam() async throws -> ALTTeam {
"""
    if text.count(anchor) != 1:
        fail(f"expected one getAuthenticatedTeam anchor, found {text.count(anchor)}")

    insertion = '''    // DPORT_AUTH_SESSION_RECOVERY_IOS27_V6
    // Re-authenticate once in the background when Apple rejects a cached
    // Developer Services session. This uses credentials already stored by
    // SideStore; it does not present UI and does not alter the normal sign-in
    // flow.
    @discardableResult
    public func reauthenticateForRefresh() async throws -> ALTAppleAPISession {
        try await TaskChainCoalescer.shared.coalesce(key: "apple_auth_refresh_recovery") {
            guard let appleID = self.currentAppleID, !appleID.isEmpty,
                  let password = self.password, !password.isEmpty else {
                debugLog("[AuthManager] Refresh session recovery unavailable: stored Apple ID/password missing.")
                throw OperationError.notAuthenticated
            }

            debugLog("[AuthManager] Refresh session recovery: requesting fresh Anisette data...")
            let anisetteData = try await AnisetteProvider.fetch()
            let xcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()

            debugLog("[AuthManager] Refresh session recovery: re-authenticating Apple account...")
            let (_, freshSession) = try await self.portalProxy.signIn(
                appleID: appleID,
                password: password,
                anisetteData: anisetteData,
                xcodeVersion: xcodeVersion,
                accountRepairHandler: DeveloperPortal.defaultAccountRepairHandler,
                verificationHandler: nil
            )

            self.adsid = freshSession.dsid
            self.xcodeToken = freshSession.authToken
            self.currentAppleID = appleID
            self.password = password
            self.session = freshSession

            debugLog("[AuthManager] Refresh session recovery: fresh Apple session acquired.")
            return freshSession
        }
    }

'''
    text = text.replace(anchor, insertion + anchor, 1)
    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (
        AUTH_MARKER,
        "reauthenticateForRefresh()",
        "self.portalProxy.signIn(",
        "self.xcodeToken = freshSession.authToken",
    ):
        if required not in verify:
            fail("AuthManager verification missing: " + required)
    print("AuthManager session recovery V6: PASS")


def find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    in_string = False
    in_multiline = False
    escape = False
    i = open_index
    while i < len(text):
        ch = text[i]
        nxt = text[i:i + 3]
        if in_multiline:
            if text.startswith('"""', i):
                in_multiline = False
                i += 3
                continue
            i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if text.startswith('"""', i):
            in_multiline = True
            i += 3
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def wrap_proxy_method(text: str, func_start: int, body_open: int) -> str:
    body_close = find_matching_brace(text, body_open)
    if body_close < 0:
        fail("could not find matching brace for DeveloperPortalProxy method")

    needle = "let session = try await self.getSession()"
    needle_at = text.find(needle, body_open, body_close)
    if needle_at < 0:
        fail("expected getSession() line inside DeveloperPortalProxy method")

    before = text[:needle_at]
    after = text[needle_at + len(needle):]
    replacement = 'return try await self.withRecoveredSession { session in'
    text = before + replacement + after

    # body_close moved by the replacement length delta
    delta = len(replacement) - len(needle)
    body_close += delta
    text = text[:body_close] + "\n    }" + text[body_close:]
    return text


def patch_proxy(root: Path) -> None:
    path = root / "SideStore/Core/Auth/DeveloperPortalProxy.swift"
    if not path.exists():
        fail(f"missing DeveloperPortalProxy.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if PROXY_MARKER in text:
        print("DeveloperPortalProxy session recovery V1: already patched")
        return

    # Insert helper directly before the first public API method.
    anchor = "    public func fetchTeams(for account: ALTAccount) async throws -> [ALTTeam] {"
    if text.count(anchor) != 1:
        fail(f"expected one fetchTeams anchor, found {text.count(anchor)}")

    helper = '''    // DPORT_PROXY_SESSION_RECOVERY_IOS27_V1
    // Run one Apple API request with the currently cached session. When Apple
    // explicitly reports an expired session, re-authenticate once using the
    // credentials already stored by SideStore and retry that same request.
    private func withRecoveredSession<T: Sendable>(
        _ operation: @escaping @Sendable (ALTAppleAPISession) async throws -> T
    ) async throws -> T {
        let session = try await self.getSession()

        do {
            return try await operation(session)
        } catch {
            guard Self.isExpiredSessionError(error) else {
                throw error
            }

            debugLog("[DeveloperPortalProxy] Apple session expired; attempting one background re-authentication before retry.")
            let freshSession = try await AuthManager.shared.reauthenticateForRefresh()
            return try await operation(freshSession)
        }
    }

    private static func isExpiredSessionError(_ error: Error) -> Bool {
        let nsError = error as NSError
        var messages = [String]()
        messages.append(nsError.localizedDescription)
        messages.append(String(describing: error))

        if let value = nsError.userInfo[NSLocalizedDescriptionKey] as? String {
            messages.append(value)
        }
        if let value = nsError.userInfo[NSLocalizedFailureReasonErrorKey] as? String {
            messages.append(value)
        }

        let message = messages.joined(separator: " ").lowercased()

        if message.contains("session has expired")
            || message.contains("your session has expired")
            || message.contains("session expired")
            || message.contains("please log in") {
            return true
        }

        // Developer Services commonly uses result code 1100 for an expired
        // authentication session. Keep the numeric check narrow to this code.
        return nsError.code == 1100
    }

'''
    text = text.replace(anchor, helper + anchor, 1)

    # Restrict edits to the DeveloperPortalProxy base class so the authenticated
    # signIn implementation below is never wrapped.
    subclass_at = text.find("class DeveloperPortalProxyWithAuth")
    if subclass_at < 0:
        fail("DeveloperPortalProxyWithAuth anchor not found")

    base = text[:subclass_at]
    tail = text[subclass_at:]
    needle = "let session = try await self.getSession()"

    method_ranges = []
    # Start scanning at the first real public API method. The recovery helper
    # itself also contains getSession(), so it must never be wrapped recursively.
    cursor = base.find(anchor)
    if cursor < 0:
        fail("fetchTeams anchor disappeared before API method scan")
    while True:
        at = base.find(needle, cursor)
        if at < 0:
            break

        func_pos = base.rfind("\n    public func ", 0, at)
        if func_pos < 0:
            func_pos = base.rfind("\n    func ", 0, at)
        if func_pos < 0:
            fail("could not locate function declaration for getSession() usage")

        body_open = base.find("{", func_pos, at)
        if body_open < 0:
            fail("could not locate function body for getSession() usage")

        body_close = find_matching_brace(base, body_open)
        if body_close < 0:
            fail("could not locate function end for getSession() usage")

        method_ranges.append((func_pos, body_open, body_close))
        cursor = body_close + 1

    if not method_ranges:
        fail("no DeveloperPortalProxy API methods use getSession()")

    # Work backwards so source offsets stay valid.
    for func_pos, body_open, body_close in reversed(method_ranges):
        base = wrap_proxy_method(base, func_pos, body_open)

    # Verify every wrapped method now contains the recovery closure and no
    # unwrapped self.getSession() call remains before the subclass declaration.
    remaining = base.count(needle)
    if remaining != 0:
        fail(f"unwrapped getSession() usage remains in DeveloperPortalProxy base class: {remaining}")

    if base.count("return try await self.withRecoveredSession { session in") != len(method_ranges):
        fail("unexpected number of recovery wrappers after patch")

    text = base + tail
    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (PROXY_MARKER, "withRecoveredSession", "isExpiredSessionError", "reauthenticateForRefresh"):
        if required not in verify:
            fail("DeveloperPortalProxy verification missing: " + required)

    print(f"DeveloperPortalProxy session recovery V1: PASS ({len(method_ranges)} API methods wrapped)")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_auth_session_recovery.py <sidestore-root>")

    root = Path(sys.argv[1]).resolve()
    patch_auth_manager(root)
    patch_proxy(root)
    print("Apple session-expiry recovery: PASS")


if __name__ == "__main__":
    main()
