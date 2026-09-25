#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_MANUAL_PIPELINE_V3"


def patch_manual_pipeline(root: Path) -> None:
    path = root / "AltStore/Intents/App Intents/RefreshAllAppsIntent.swift"
    text = path.read_text(encoding="utf-8")
    marker = "DPORT_IOS27_MANUAL_PIPELINE_V3"
    if marker in text:
        print("already patched:", marker)
        return

    # Use the same AppManager.refresh() pipeline as the manual SideStore
    # Refresh button. The manual pipeline returns RefreshGroup, not
    # BackgroundRefreshAppsOperation, so do not use background-refresh-only
    # properties such as presentsFinishedNotification.
    old = """@available(iOS 17.0, tvOS 17.0, *)
extension RefreshAllAppsIntent
{
    private actor OperationActor
    {
        private(set) var operation: BackgroundRefreshAppsOperation?
        
        func set(_ operation: BackgroundRefreshAppsOperation?)
        {
            self.operation = operation
        }
    }
}"""
    new = """@available(iOS 17.0, tvOS 17.0, *)
extension RefreshAllAppsIntent
{
}"""
    if text.count(old) != 1:
        raise SystemExit(f"operation actor anchor: expected one match, found {text.count(old)}")
    text = text.replace(old, new, 1)

    old2 = """        try await withCheckedThrowingContinuation { continuation in
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
    new2 = """        try await withCheckedThrowingContinuation { continuation in
            // DPORT_IOS27_MANUAL_PIPELINE_V3
            // Reuse the exact AppManager.refresh() pipeline used by the
            // manual SideStore Refresh button. This avoids the separate
            // backgroundRefresh/ADI execution path used by the original
            // App Intent on iOS 27.
            let group = AppManager.shared.refresh(
                installedApps,
                presentingViewController: nil
            )

            group.completionHandler = { results in
                for (_, result) in results
                {
                    switch result
                    {
                    case .success:
                        continue
                    case .failure(let error):
                        continuation.resume(throwing: error)
                        return
                    }
                }

                continuation.resume()
            }

            self.progress.addChild(group.progress, withPendingUnitCount: 1)
        }"""
    if text.count(old2) != 1:
        raise SystemExit(f"refresh anchor: expected one match, found {text.count(old2)}")
    text = text.replace(old2, new2, 1)

    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (
        marker,
        "AppManager.shared.refresh(",
        "group.completionHandler = { results in",
        "presentingViewController: nil",
    ):
        if required not in verify:
            raise SystemExit("manual pipeline verification failed: " + required)
    if "AppManager.shared.backgroundRefresh(installedApps" in verify:
        raise SystemExit("backgroundRefresh path still present in RefreshAllAppsIntent")
    if "presentsFinishedNotification" in verify:
        raise SystemExit("background-refresh-only presentsFinishedNotification still present")
    if "operationActor" in verify:
        raise SystemExit("obsolete OperationActor reference still present")
    print("iOS 27 manual SideStore refresh pipeline V3: PASS")


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
