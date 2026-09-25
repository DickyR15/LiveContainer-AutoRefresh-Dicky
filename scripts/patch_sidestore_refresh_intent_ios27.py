#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_MANUAL_PIPELINE_V1"


def patch_manual_pipeline(root: Path) -> None:
    path = root / "AltStore/Intents/App Intents/RefreshAllAppsIntent.swift"
    text = path.read_text(encoding="utf-8")
    marker = "DPORT_IOS27_MANUAL_PIPELINE_V1"
    if marker in text:
        print("already patched:", marker)
        return

    old = """        try await withCheckedThrowingContinuation { continuation in
            let operation = try? AppManager.shared.backgroundRefresh(installedApps, presentsNotifications: self.presentsNotifications) { (result) in
                do
                {
                    let results = try result.get()
                    
                    for (_, result) in results
                    {
                        guard case let .failure(error) = result else { continue }
                        throw error
                    }
                    
                    continuation.resume()
                }
                catch OperationError.noInstalledApps
                {
                    continuation.resume()
                }
                catch
                {
                    continuation.resume(throwing: error)
                }
            }
            
            guard let operation else {
                debugLog("[RefreshAllAppsIntent] backgroundRefresh instance is nil")
                return 
            }
            
            operation.ignoresServerNotFoundError = false
            
            self.progress.addChild(operation.progress, withPendingUnitCount: 1)
            
            Task {
                await self.operationActor.set(operation)
            }
        }"""
    new = """        try await withCheckedThrowingContinuation { continuation in
            // DPORT_IOS27_MANUAL_PIPELINE_V1
            // iOS 27 returns ADI -45061 from the AppIntent/backgroundRefresh
            // path even when the same account/device refreshes successfully
            // from inside SideStore. Reuse AppManager.refresh(), which is the
            // authenticated pipeline used by the manual Refresh button.
            let group = AppManager.shared.refresh(
                installedApps,
                presentingViewController: nil
            ) { results in
                for (_, result) in results
                {
                    guard case let .failure(error) = result else { continue }
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume()
            }

            group.ignoresServerNotFoundError = false
            self.progress.addChild(group.progress, withPendingUnitCount: 1)

            Task {
                await self.operationActor.set(nil)
            }
        }"""
    if text.count(old) != 1:
        raise SystemExit(f"manual pipeline anchor: expected one match, found {text.count(old)}")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (marker, "AppManager.shared.refresh(", "presentingViewController: nil"):
        if required not in verify:
            raise SystemExit("manual pipeline verification failed: " + required)
    print("iOS 27 manual SideStore refresh pipeline: PASS")

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

    # SideStore 0.7.0 uses internal static members here. Older revisions used
    # public static members. Accept both exact forms, but patch only once.
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

    // DPORT_IOS27_MAIN_PROCESS_REFRESH_V2
    // iOS 27 introduced execution-target selection for App Intents. Keep the
    // Refresh All Apps intent eligible for the main application execution
    // target so its authenticated/provisioned SideStore state is available.
    @available(iOS 27.0, *)
    {access}static var allowedExecutionTargets: IntentExecutionTargets {{
        .main
    }}

    {access}static var title: LocalizedStringResource = "Refresh All Apps"
'''

    text = text.replace(anchor, replacement, 1)
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in (
        "DPORT_IOS27_MAIN_PROCESS_REFRESH_V2",
        "DPORT_IOS27_MAIN_PROCESS_REFRESH_V3",
        "static var openAppWhenRun = true",
        "@available(iOS 27.0, *)",
        "allowedExecutionTargets: IntentExecutionTargets",
        ".main",
    ):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    if "supportedModes" in verify and "DPORT_IOS27_REFRESH_FOREGROUND_V1" in verify:
        raise SystemExit("old foreground workaround is still present; start from a clean source")
    patch_manual_pipeline(root)
    print("iOS 27 main-process refresh target: PASS")

if __name__ == "__main__":
    main()
