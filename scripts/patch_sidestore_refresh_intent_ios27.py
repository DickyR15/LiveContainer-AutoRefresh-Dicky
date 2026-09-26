#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_OPEN_APP_REFRESH_V10"


def patch_manual_pipeline(root: Path) -> None:
    # Keep SideStore's upstream RefreshAllAppsIntent implementation intact.
    # The latest develop/nightly contains the session-level delegate fix that
    # is important for iOS 27 ADI/Anisette requests. Our customization only
    # selects the main SideStore process; replacing backgroundRefresh() with
    # AppManager.refresh() creates a different execution/signing path and can
    # reproduce -45061 even when manual refresh works.
    path = root / "AltStore/Intents/App Intents/RefreshAllAppsIntent.swift"
    text = path.read_text(encoding="utf-8")
    if "AppManager.shared.backgroundRefresh(installedApps" not in text:
        raise SystemExit("upstream RefreshAllAppsIntent backgroundRefresh path is missing")
    if "DPORT_IOS27_MANUAL_PIPELINE_V8" in text:
        raise SystemExit("obsolete manual-pipeline V8 patch is present")
    print("iOS 27 upstream refresh pipeline preserved: PASS")


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

    anchors = (
        '''    static let intentClassName = "RefreshAllIntent"
    
    static var title: LocalizedStringResource = "Refresh All Apps"
''',
        '''    public static let intentClassName = "RefreshAllIntent"
    
    public static var title: LocalizedStringResource = "Refresh All Apps"
''',
    )

    anchor = next((candidate for candidate in anchors if candidate in text), None)
    if anchor is None:
        raise SystemExit(
            "expected one RefreshAllAppsIntent anchor, found 0; "
            "inspect the pinned SideStore source before changing this patch"
        )

    if text.count(anchor) != 1:
        raise SystemExit(
            f"expected one RefreshAllAppsIntent anchor, found {text.count(anchor)}"
        )

    access = "public " if anchor.startswith("    public ") else ""
    replacement = f'''    {access}static let intentClassName = "RefreshAllIntent"
    
    // DPORT_IOS27_MAIN_PROCESS_REFRESH_V3
    // Force the containing SideStore process to be opened before the intent
    // executes. iOS 27 has reports where Refresh All Apps launched from
    // Shortcuts cannot access the same authenticated/provisioned runtime state
    // unless SideStore is already alive.
    static var openAppWhenRun = true

    // DPORT_IOS27_OPEN_APP_REFRESH_V10
    // iOS 27: ensure the SideStore main process is initialized before the
    // Refresh All Apps intent runs. Keep Apple's normal AppIntent execution
    // target selection untouched; forcing .main can produce
    // LNPerformActionErrorCodeMalformedResponse in Shortcuts.
    static var openAppWhenRun = true

    {access}static var title: LocalizedStringResource = "Refresh All Apps"
'''

    text = text.replace(anchor, replacement, 1)
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in (
        "DPORT_IOS27_OPEN_APP_REFRESH_V10",
        "static var openAppWhenRun = true",
    ):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    if "supportedModes" in verify and "DPORT_IOS27_REFRESH_FOREGROUND_V1" in verify:
        raise SystemExit("old foreground workaround is still present; start from a clean source")
    patch_manual_pipeline(root)
    print("iOS 27 main-process refresh target: PASS")


if __name__ == "__main__":
    main()
