#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_REFRESH_FOREGROUND_V1"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_sidestore_refresh_intent_ios27.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "AltStore/Intents/App Intents/RefreshAllAppsIntent.swift"
    if not path.exists():
        raise SystemExit(f"missing RefreshAllAppsIntent.swift: {path}")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("already patched:", MARKER)
        return

    anchor = '''    static let intentClassName = "RefreshAllIntent"

    static var title: LocalizedStringResource = "Refresh All Apps"
'''
    replacement = '''    static let intentClassName = "RefreshAllIntent"

    // DPORT_IOS27_REFRESH_FOREGROUND_V1
    // On iOS 27, the Shortcut/AppIntent can run while SideStore is completely
    // suspended. In that state the refresh path can lack the authenticated
    // SideStore process context and return ADI -45061. Opening SideStore first
    // is a known workaround, so make the refresh intent foreground SideStore
    // before perform() on iOS 27. Older iOS keeps the original background mode.
    static var supportedModes: IntentModes {
        if #available(iOS 27.0, *) {
            return .foreground
        }
        return .background
    }

    static var title: LocalizedStringResource = "Refresh All Apps"
'''
    if text.count(anchor) != 1:
        raise SystemExit(f"expected one RefreshAllAppsIntent anchor, found {text.count(anchor)}")
    text = text.replace(anchor, replacement, 1)
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in ("DPORT_IOS27_REFRESH_FOREGROUND_V1", "static var supportedModes: IntentModes", "return .foreground", "return .background"):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    print("iOS 27 SideStore foreground refresh workaround: PASS")

if __name__ == "__main__":
    main()
