#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_REFRESH_1100_RETRY_V1"

def fail(message: str) -> None:
    raise SystemExit("patch_refresh_1100_retry: " + message)

def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_refresh_1100_retry.py <sidestore-root>")

    root = Path(sys.argv[1]).resolve()
    path = root / "AltStore/Managing Apps/AppManager.swift"
    if not path.exists():
        fail(f"missing AppManager.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("Refresh 1100 retry V1: already patched")
        return

    old = """        actualGroup.activeTask = Task.detached {
            do {
                try await self.pipelineRunner.perform(installedApps.map { .refresh($0) }, handler: pipelineHandler, group: actualGroup)
            } catch {
                actualGroup.error = error
                let results = Dictionary(uniqueKeysWithValues: installedApps.map { ($0.bundleIdentifier, Result<InstalledApp, Error>.failure(error)) })
                actualGroup.completionHandler?(results)
            }
        }
"""
    new = """        actualGroup.activeTask = Task.detached {
            do {
                // DPORT_REFRESH_1100_RETRY_V1
                do {
                    try await AuthManager.shared.getAuthenticatedSession()
                    try await self.pipelineRunner.perform(installedApps.map { .refresh($0) }, handler: pipelineHandler, group: actualGroup)
                } catch {
                    let nsError = error as NSError
                    let message = error.localizedDescription.lowercased()
                    let isSessionExpired = nsError.code == 1100
                        || message.contains("your session has expired")
                        || message.contains("session has expired")
                        || message.contains("please log in")
                        || message.contains("lnperrorcodelocalizedstringresource")

                    guard isSessionExpired else {
                        throw error
                    }

                    debugLog("[AppManager] Apple API 1100 detected during refresh; forcing fresh authentication and retrying once.")
                    _ = try await AuthManager.shared.forceReauthenticateForRefresh()
                    try await self.pipelineRunner.perform(installedApps.map { .refresh($0) }, handler: pipelineHandler, group: actualGroup)
                    debugLog("[AppManager] Refresh retry after Apple API 1100 completed.")
                }
            } catch {
                actualGroup.error = error
                let results = Dictionary(uniqueKeysWithValues: installedApps.map { ($0.bundleIdentifier, Result<InstalledApp, Error>.failure(error)) })
                actualGroup.completionHandler?(results)
            }
        }
"""
    if old not in text:
        fail("refresh task anchor not found")

    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in (
        MARKER,
        "AuthManager.shared.getAuthenticatedSession()",
        "AuthManager.shared.forceReauthenticateForRefresh()",
        "Apple API 1100 detected during refresh",
        "Refresh retry after Apple API 1100 completed.",
    ):
        if required not in verify:
            fail("verification missing: " + required)

    print("Refresh 1100 retry V1: PASS")

if __name__ == "__main__":
    main()
