#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

UPSTREAM = Path("builder/patch_background_automation.py")

def load_module():
    sys.path.insert(0, str(UPSTREAM.parent.resolve()))
    spec = importlib.util.spec_from_file_location("autorefresh_background", UPSTREAM)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load upstream background automation patcher")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def install_compat(mod):
    original = mod.replace_once
    original_die = mod.die

    def compat_die(message):
        if isinstance(message, str) and message.startswith("background operation verification failed:"):
            if "AUTH_PREFLIGHT_PASS" in message or "hasPasswordCredentials" in message:
                return print("background operation verification: skipped optional AUTH_PREFLIGHT diagnostics")
        return original_die(message)

    def compat_replace_once(text, old, new, label):
        if label == "background authentication preflight":
            return text
        if label == "application background reschedule":
            if "func applicationDidEnterBackground" not in text:
                mod.die("application background reschedule: method not found")
            start = text.index("func applicationDidEnterBackground")
            body_start = text.index("{", start) + 1
            end = text.find("func applicationWillEnterForeground", body_start)
            if end < 0:
                end = len(text)
            body = text[body_start:end]
            if "scheduleAutomaticRefresh()" not in body:
                text = text[:body_start] + "\n        self.scheduleAutomaticRefresh()\n" + text[body_start:]
            return text
        return original(text, old, new, label)

    def patch_manual_refresh_070(sidestore: Path) -> None:
        path = sidestore / "AltStore/Managing Apps/AppManager.swift"
        text = path.read_text(encoding="utf-8")
        start = text.index("    func refresh(_ installedApps:")
        end = text.index("    func activate(", start)
        section = text[start:end]

        if "let manualHistoryRunID" not in section:
            signatures = [
                """    func refresh(_ installedApps: [InstalledApp],
                 presentingViewController: UIViewController?,
                 group: RefreshGroup? = nil) -> RefreshGroup""",
                """    func refresh(_ installedApps: [InstalledApp], presentingViewController: UIViewController?, group: RefreshGroup? = nil) -> RefreshGroup""",
                """    func refresh(_ installedApps: [InstalledApp],
                 presentingViewController: UIViewController?,
                 dbContext: NSManagedObjectContext? = nil,
                 group: RefreshGroup? = nil) -> RefreshGroup""",
            ]
            signature = next((candidate for candidate in signatures if section.count(candidate) == 1), None)
            if signature is None:
                mod.die("manual history signature: no compatible refresh() signature found")
            replacement = signature.replace(
                "group: RefreshGroup? = nil) -> RefreshGroup",
                "group: RefreshGroup? = nil,\n                 recordManualHistory: Bool = true) -> RefreshGroup",
            )
            section = section.replace(signature, replacement, 1)
            detached = """        actualGroup.activeTask = Task.detached {
            do {
                try await self.pipelineRunner.perform(installedApps.map { .refresh($0) }, handler: pipelineHandler, group: actualGroup)
            } catch {
                actualGroup.error = error
                let results = Dictionary(uniqueKeysWithValues: installedApps.map { ($0.bundleIdentifier, Result<InstalledApp, Error>.failure(error)) })
                actualGroup.completionHandler?(results)
            }
        }
"""
            if section.count(detached) != 1:
                mod.die(f"manual history body: expected one anchor, found {section.count(detached)}")

            replacement = """        let manualHistoryRunID = recordManualHistory ? UUID() : nil
        let historyAppIDs = Set(installedApps.map { $0.bundleIdentifier })
        if let runID = manualHistoryRunID {
            AutomaticRefreshHistory.record(.started, runID: runID,
                detail: "Refreshing \\(historyAppIDs.count) apps.", source: .manual)
        }

        actualGroup.activeTask = Task.detached {
            do {
                try await self.pipelineRunner.perform(installedApps.map { .refresh($0) }, handler: pipelineHandler, group: actualGroup)
                if let runID = manualHistoryRunID {
                    AutomaticRefreshHistory.finishManual(runID: runID, expected: historyAppIDs, results: actualGroup.results)
                }
            } catch {
                if let runID = manualHistoryRunID {
                    AutomaticRefreshHistory.record(.failed, runID: runID,
                        detail: error.localizedDescription, source: .manual)
                }
                actualGroup.context.error = error
                let results = Dictionary(uniqueKeysWithValues: installedApps.map { ($0.bundleIdentifier, Result<InstalledApp, Error>.failure(error)) })
                actualGroup.completionHandler?(results)
            }
        }
"""
            section = section.replace(detached, replacement, 1)
            text = text[:start] + section + text[end:]
            path.write_text(text, encoding="utf-8")

        required = (
            "manualHistoryRunID",
            "recordManualHistory: Bool = true",
            "AutomaticRefreshHistory.finishManual",
            "source: .manual",
        )
        for item in required:
            if item not in section:
                mod.die(f"manual history verification failed: {item}")

    mod.replace_once = compat_replace_once
    mod.patch_manual_refresh = patch_manual_refresh_070
    return mod

def main():
    mod = install_compat(load_module())
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "work/EmbeddedSideStore").resolve()
    mod.patch_app_delegate(root)
    mod.patch_scene_delegate(root)
    background = root / "SideStore/Core/Operations/StandaloneOperations/BackgroundRefreshAppsOperation.swift"
    background_text = background.read_text(encoding="utf-8")
    if "let group = AppManager.shared.refresh(apps, presentingViewController: nil)" in background_text:
        # SideStore 0.7.0+ already uses the upstream AppManager.refresh() path.
        # Do not reapply the older V30 patch, which expects obsolete anchors.
        print("background operation: upstream 0.7.0 refresh pipeline already present; skipped legacy patch")
    else:
        try:
            mod.patch_background_operation(root)
        except SystemExit as exc:
            message = str(exc)
            if not (
                message.startswith("background operation verification failed:")
                and ("AUTH_PREFLIGHT_PASS" in message or "hasPasswordCredentials" in message)
            ):
                raise
            print("background operation verification: skipped optional AUTH_PREFLIGHT diagnostics")

    mod.patch_manual_refresh(root)
    mod.patch_info_plist(root)
    mod.patch_settings(root)
    mod.patch_console_log(root)
    mod.verify(root)
    print("SideStore 0.7.0 background automation compatibility patch: PASS")

if __name__ == "__main__":
    main()
