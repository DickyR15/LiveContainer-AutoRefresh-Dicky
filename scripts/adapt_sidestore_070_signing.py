#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "SIDESTORE_SIGN_PASS"

def die(message: str) -> None:
    raise SystemExit(message)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)

def patch(root: Path) -> None:
    path = root / "SideStore" / "Core" / "Operations" / "PipelineOperations" / "ResignAppOperation.swift"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        if text.count(MARKER) != 1 or "provisioningProfile != nil" not in text:
            die("existing signing marker is incomplete")
        print("SideStore signing adaptation already present")
        return

    old = '''        let resignedAppURL = try await self.resignAppBundle(at: appBundleURL, team: team, certificate: certificate, profiles: Array(profiles.values))
        guard let resignedAppBundle = ALTApplication(fileURL: resignedAppURL) else {
            throw OperationError.invalidApp(reason: "Could not load resigned app bundle at '\(resignedAppURL.lastPathComponent)'")
        }
'''
    new = old + '''        #if !targetEnvironment(simulator)
        guard resignedAppBundle.provisioningProfile != nil else {
            throw OperationError.invalidApp(reason: "Resigned app bundle has no provisioning profile")
        }
        #endif

        if appBundle.isAltStoreApp {
            self.debugLog("[SELF_REFRESH] SIDESTORE_SIGN_PASS bundle_id=\(resignedAppBundle.bundleIdentifier)")
        }
'''
    text = replace_once(text, old, new, "SideStore 0.7.0 resign flow")
    if text.count(MARKER) != 1 or "provisioningProfile != nil" not in text:
        die("signing adaptation verification failed")
    path.write_text(text, encoding="utf-8")
    print("SideStore 0.7.0 resign flow adapted for self-refresh verification")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        die("usage: adapt_sidestore_070_signing.py SIDESTORE_ROOT")
    patch(Path(sys.argv[1]))
