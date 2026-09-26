#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_AUTH_SESSION_RECOVERY_V2_VALIDATE_ACCOUNT"


def fail(message: str) -> None:
    raise SystemExit("patch_auth_session_recovery_v2: " + message)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_auth_session_recovery_v2.py <sidestore-root>")

    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Auth/AuthManager.swift"
    if not path.exists():
        fail(f"missing AuthManager.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("AuthManager session recovery V2: already patched")
        return

    start_anchor = """    @discardableResult
    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {
"""
    end_anchor = """
    public func getAuthenticatedTeam() async throws -> ALTTeam {
"""
    start = text.find(start_anchor)
    end = text.find(end_anchor, start)
    if start < 0 or end < 0:
        fail("getAuthenticatedSession anchors not found")

    replacement = r'''    // DPORT_AUTH_SESSION_RECOVERY_V2_VALIDATE_ACCOUNT
    @discardableResult
    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {
        return try await TaskChainCoalescer.shared.coalesce(key: "apple_auth_session") {
            // Reuse a session only after a lightweight Developer Services
            // account request confirms that Apple's current session is valid.
            if let cachedSession = self.session {
                do {
                    _ = try await self.portalProxy.fetchAccount(session: cachedSession)
                    debugLog("[AuthManager] Cached Apple session validation: PASS")
                    return cachedSession
                } catch {
                    guard Self.isExpiredSessionError(error) else {
                        throw error
                    }
                    debugLog("[AuthManager] Cached Apple session expired; starting background recovery.")
                    self.session = nil
                }
            }

            guard let adsid = self.adsid,
                  let xcodeToken = self.xcodeToken else {
                debugLog("[AuthManager] No stored tokens found.")
                throw OperationError.notAuthenticated
            }

            let anisetteData = try await AnisetteProvider.fetch()
            let xcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()

            let candidateSession = ALTAppleAPISession(
                dsid: adsid,
                authToken: xcodeToken,
                anisetteData: anisetteData,
                xcodeVersion: xcodeVersion
            )

            do {
                _ = try await self.portalProxy.fetchAccount(session: candidateSession)
                self.session = candidateSession
                debugLog("[AuthManager] Stored Apple session validation: PASS")
                return candidateSession
            } catch {
                guard Self.isExpiredSessionError(error) else {
                    throw error
                }

                debugLog("[AuthManager] Stored Apple session expired; performing fresh Apple sign-in.")

                guard let appleID = self.currentAppleID, !appleID.isEmpty,
                      let password = self.password, !password.isEmpty else {
                    debugLog("[AuthManager] Session recovery unavailable: stored Apple ID/password missing.")
                    throw error
                }

                let freshAnisette = try await AnisetteProvider.fetch()
                let freshXcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()

                let (_, freshSession) = try await self.portalProxy.signIn(
                    appleID: appleID,
                    password: password,
                    anisetteData: freshAnisette,
                    xcodeVersion: freshXcodeVersion,
                    accountRepairHandler: DeveloperPortal.defaultAccountRepairHandler,
                    verificationHandler: nil
                )

                // Persist the newly issued session exactly as the normal sign-in
                // flow does, then validate it through the same account endpoint.
                self.adsid = freshSession.dsid
                self.xcodeToken = freshSession.authToken
                self.currentAppleID = appleID
                self.password = password
                self.session = freshSession

                _ = try await self.portalProxy.fetchAccount(session: freshSession)
                debugLog("[AuthManager] Fresh Apple session validation: PASS")
                return freshSession
            }
        }
    }

    private static func isExpiredSessionError(_ error: Error) -> Bool {
        let nsError = error as NSError
        var messages = [String(describing: error), nsError.localizedDescription]

        if let value = nsError.userInfo[NSLocalizedDescriptionKey] as? String {
            messages.append(value)
        }
        if let value = nsError.userInfo[NSLocalizedFailureReasonErrorKey] as? String {
            messages.append(value)
        }

        let message = messages.joined(separator: " ").lowercased()
        return nsError.code == 1100
            || message.contains("session has expired")
            || message.contains("your session has expired")
            || message.contains("session expired")
            || message.contains("please log in")
    }

'''
    text = text[:start] + replacement + text[end:]
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    required = (
        MARKER,
        "fetchAccount(session: cachedSession)",
        "fetchAccount(session: candidateSession)",
        "self.portalProxy.signIn(",
        "Fresh Apple session validation: PASS",
        "isExpiredSessionError",
    )
    for item in required:
        if item not in verify:
            fail("verification missing: " + item)

    print("AuthManager session recovery V2: PASS")


if __name__ == "__main__":
    main()
