#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_AUTH_SESSION_RECOVERY_IOS27_V4"

def fail(message: str) -> None:
    raise SystemExit("patch_auth_session_recovery: " + message)

def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_auth_session_recovery.py <sidestore-root>")

    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Auth/AuthManager.swift"
    if not path.exists():
        fail(f"missing AuthManager.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("Apple API session recovery V4: already patched")
        return

    start = text.find("    @discardableResult\n    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {")
    if start < 0:
        fail("getAuthenticatedSession anchor not found")

    end = text.find("\n    public func getAuthenticatedTeam()", start)
    if end < 0:
        fail("getAuthenticatedTeam anchor not found")

    replacement = r'''    // DPORT_AUTH_SESSION_RECOVERY_IOS27_V2
    @discardableResult
    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {
        return try await TaskChainCoalescer.shared.coalesce(key: "apple_auth_session") {
            guard let adsid = self.adsid,
                  let xcodeToken = self.xcodeToken else {
                debugLog("[AuthManager] No stored tokens found.")
                throw OperationError.notAuthenticated
            }

            let anisetteData = try await AnisetteProvider.fetch()
            let xcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()

            var session = ALTAppleAPISession(
                dsid: adsid,
                authToken: xcodeToken,
                anisetteData: anisetteData,
                xcodeVersion: xcodeVersion
            )

            // A token can pass the account endpoint while still being rejected by
            // Developer Services with result code 1100. Validate against the same
            // Developer Services endpoint used by refresh before returning it.
            do {
                let accountInfo = try await DatabaseManager.shared.persistentContainer.performBackgroundTask { context -> ALTAccount in
                    guard let dbAccount = DatabaseManager.shared.activeAccount(in: context) else {
                        throw OperationError.notAuthenticated
                    }
                    return ALTAccount(
                        appleID: dbAccount.appleID,
                        identifier: dbAccount.identifier
                    )
                }

                _ = try await ALTAppleAPI.shared.fetchTeams(for: accountInfo, session: session)
                self.session = session
                debugLog("[AuthManager] Developer Services session validation: PASS")
                return session
            } catch {
                let nsError = error as NSError
                let message = error.localizedDescription.lowercased()
                let isExpired = nsError.code == 1100
                    || message.contains("session has expired")
                    || message.contains("please log in")
                    || message.contains("lnperrorcodelocalizedstringresource")

                guard isExpired,
                      let appleID = self.currentAppleID,
                      let password = self.password,
                      !password.isEmpty else {
                    debugLog("[AuthManager] Developer Services validation failed: \(error)")
                    throw error
                }

                debugLog("[AuthManager] Developer Services session expired (1100); performing fresh Apple sign-in.")

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

                self.adsid = freshSession.dsid
                self.xcodeToken = freshSession.authToken
                session = freshSession
                self.session = freshSession

                // Verify the newly issued token against Developer Services too.
                let accountInfo = try await DatabaseManager.shared.persistentContainer.performBackgroundTask { context -> ALTAccount in
                    guard let dbAccount = DatabaseManager.shared.activeAccount(in: context) else {
                        throw OperationError.notAuthenticated
                    }
                    return ALTAccount(
                        appleID: dbAccount.appleID,
                        identifier: dbAccount.identifier
                    )
                }
                _ = try await ALTAppleAPI.shared.fetchTeams(for: accountInfo, session: freshSession)

                debugLog("[AuthManager] Fresh Developer Services session validation: PASS")
                return freshSession
            }
        }
    }
'''
    text = text[:start] + replacement + text[end:]

    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (
        MARKER,
        "ALTAppleAPI.shared.fetchTeams(for: accountInfo, session: session)",
        "Developer Services session expired (1100)",
        "self.portalProxy.signIn(",
        "Fresh Developer Services session validation: PASS",
    ):
        if required not in verify:
            fail("verification missing: " + required)
    print("Apple API session recovery V4: PASS")

if __name__ == "__main__":
    main()
