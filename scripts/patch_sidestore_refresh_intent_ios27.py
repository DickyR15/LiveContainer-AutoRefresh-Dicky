#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_MAIN_PROCESS_REFRESH_V2"

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

    anchor = '''    public static let intentClassName = "RefreshAllIntent"
    
    public static var title: LocalizedStringResource = "Refresh All Apps"
'''
    if anchor not in text:
        anchor = '''    public static let intentClassName = "RefreshAllIntent"
    
    public static var title: LocalizedStringResource = "Refresh All Apps"
'''
    replacement = '''    public static let intentClassName = "RefreshAllIntent"
    
    // DPORT_IOS27_MAIN_PROCESS_REFRESH_V2
    // iOS 27 introduced execution-target selection for App Intents. The
    // default target may execute the intent outside SideStore's main process,
    // where its authenticated/provisioned state is unavailable and ADI can
    // return -45061. Manual refresh runs in the main SideStore process.
    // Pin this intent to the main app process on iOS 27+ so the automatic
    // refresh uses the same process-owned signing state as manual refresh.
    @available(iOS 27.0, *)
    public static var allowedExecutionTargets: IntentExecutionTargets {
        .main
    }

    public static var title: LocalizedStringResource = "Refresh All Apps"
'''
    if text.count(anchor) != 1:
        raise SystemExit(f"expected one RefreshAllAppsIntent anchor, found {text.count(anchor)}")
    text = text.replace(anchor, replacement, 1)
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in (
        "DPORT_IOS27_MAIN_PROCESS_REFRESH_V2",
        "@available(iOS 27.0, *)",
        "public static var allowedExecutionTargets: IntentExecutionTargets",
        ".main",
    ):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    if "supportedModes" in verify and "DPORT_IOS27_REFRESH_FOREGROUND_V1" in verify:
        raise SystemExit("old foreground workaround is still present; start from a clean source")
    print("iOS 27 main-process refresh target: PASS")

if __name__ == "__main__":
    main()
