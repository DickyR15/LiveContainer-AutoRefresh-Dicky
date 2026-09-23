#!/usr/bin/env python3
"""Source-matched SideStore 0.7.0 signing verification adapter."""
from pathlib import Path
import sys

MARKER = "SIDESTORE_SIGN_PASS"
ANCHOR = '        self.debugLog("[ResignAppOperation] Resigned app \\(self.context.bundleIdentifier) to \\(resignedAppBundle.bundleIdentifier).")'

def die(message: str) -> None:
    raise SystemExit(message)

def patch(root: Path) -> None:
    path = root / "SideStore" / "Core" / "Operations" / "PipelineOperations" / "ResignAppOperation.swift"
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        if text.count(MARKER) != 1 or "provisioningProfile != nil" not in text:
            die("existing signing marker is incomplete")
        print("SideStore 0.7.0 signing adaptation already present")
        return

    if text.count(ANCHOR) != 1:
        die(f"ResignAppOperation completion anchor: expected 1, found {text.count(ANCHOR)}")

    insertion = '''        #if !targetEnvironment(simulator)
        guard resignedAppBundle.provisioningProfile != nil else {
            throw OperationError.invalidApp(reason: "Resigned app bundle has no provisioning profile")
        }
        #endif

        if appBundle.isAltStoreApp {
            self.debugLog("[SELF_REFRESH] SIDESTORE_SIGN_PASS bundle_id=\\(resignedAppBundle.bundleIdentifier)")
        }

'''
    text = text.replace(ANCHOR, insertion + ANCHOR, 1)
    if text.count(MARKER) != 1:
        die("signing marker insertion failed")
    path.write_text(text, encoding="utf-8")
    print("SideStore 0.7.0 signing adaptation applied")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        die("usage: adapt_sidestore_070_signing.py SIDESTORE_ROOT")
    patch(Path(sys.argv[1]))
