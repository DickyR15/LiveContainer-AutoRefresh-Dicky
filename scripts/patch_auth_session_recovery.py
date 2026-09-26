#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_AUTH_SESSION_RECOVERY_IOS27_V1"

OLD = """    @discardableResult
    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {
        return try await TaskChainCoalescer.shared.coalesce(key: "apple_auth_session") {
            guard let adsid = self.adsid,                           // directory services id
                  let xcodeToken = self.xcodeToken else             // xcode token
            {
                debugLog("[AuthManager] No stored tokens found.")
                throw OperationError.notAuthenticated
            }
            let anisetteData = try await AnisetteProvider.fetch()   // one time pass
            let xcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()
            
            let session = ALTAppleAPISession(
                dsid: adsid,
                authToken: xcodeToken,
                anisetteData: anisetteData,
                xcodeVersion: xcodeVersion
            )
            self.session = session
            return session
        }
    }
"""

NEW = """    @discardableResult
    public func getAuthenticatedSession() async throws -> ALTAppleAPISession {
        return try await TaskChainCoalescer.shared.coalesce(key: "apple_auth_session") {
            guard let adsid = self.adsid,
                  let xcodeToken = self.xcodeToken else
            {
                debugLog("[AuthManager] No stored tokens found.")
                throw OperationError.notAuthenticated
            }

            let anisetteData = try await AnisetteProvider.fetch()
            let xcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()

            let session = ALTAppleAPISession(
                dsid: adsid,
                authToken: xcodeToken,
                anisetteData: anisetteData,
                xcodeVersion: xcodeVersion
            )

            // iOS 27 AppIntent/background execution can start in a fresh
            // process with a stale cached Apple API session token. Validate
            // the token once before handing it to refresh/signing operations.
            do {
                _ = try await ALTAppleAPI.shared.fetchAccount(session: session)
                self.session = session
                debugLog("[AuthManager] Apple API session validation: PASS")
                return session
            } catch {
                let message = error.localizedDescription.lowercased()
                let isExpired = message.contains("1100")
                    || message.contains("session has expired")
                    || message.contains("please log in")
                    || message.contains("lnperrorcodelocalizedstringresource")

                guard isExpired,
                      let appleID = self.currentAppleID,
                      let password = self.password,
                      !password.isEmpty else
                {
                    debugLog("[AuthManager] Apple API session validation failed: \(error)")
                    throw error
                }

                debugLog("[AuthManager] Apple API session expired; re-authenticating before refresh.")

                let freshAnisette = try await AnisetteProvider.fetch()
                let freshXcodeVersion = await AnisetteConfigManager.shared.resolvedXcodeVersion()
                let (_, freshSession) = try await self.signIn(
                    appleID: appleID,
                    password: password,
                    anisetteData: freshAnisette,
                    xcodeVersion: freshXcodeVersion,
                    verificationHandler: nil
                )

                self.adsid = freshSession.dsid
                self.xcodeToken = freshSession.authToken
                self.session = freshSession
                debugLog("[AuthManager] Apple API session re-authentication: PASS")
                return freshSession
            }
        }
    }
"""
def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_auth_session_recovery.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Auth/AuthManager.swift"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("already patched:", MARKER)
        return
    if OLD not in text:
        raise SystemExit("expected AuthManager.getAuthenticatedSession anchor not found")
    text = text.replace(
        OLD,
        "// " + MARKER + " — validate/re-authenticate stale Apple API sessions\n" + NEW,
        1,
    )
    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (
        MARKER,
        "Apple API session validation",
        "Apple API session expired; re-authenticating",
        "ALTAppleAPI.shared.fetchAccount(session: session)",
        "self.signIn(",
    ):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    print("Apple API session recovery patch: PASS")

if __name__ == "__main__":
    main()
