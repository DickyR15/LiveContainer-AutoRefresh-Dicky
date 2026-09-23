#!/usr/bin/env python3
from pathlib import Path

SCRIPT = Path("builder/patch_background_automation.py")

def replace_function(text: str, name: str, new_func: str) -> str:
    marker = f"def {name}("
    start = text.index(marker)
    next_marker = text.find("\ndef ", start + len(marker))
    if next_marker < 0:
        next_marker = len(text)
    return text[:start] + new_func.rstrip() + "\n" + text[next_marker+1:]

def main():
    s = SCRIPT.read_text(encoding="utf-8")

    # Make AppDelegate background scheduling source-aware instead of exact-text anchored.
    label = '        "application background reschedule",'
    pos = s.find(label)
    if pos >= 0:
        start = s.rfind("    text = replace_once(", 0, pos)
        close = s.find("\n    )", pos)
        if start >= 0 and close >= 0:
            close += len("\n    )")
            replacement = '''    method_marker = "func applicationDidEnterBackground"
    if method_marker not in text:
        die("application background reschedule: method not found")
    method_start = text.index(method_marker)
    body_start = text.index("{", method_start) + 1
    next_method = text.find("func applicationWillEnterForeground", body_start)
    if next_method < 0:
        next_method = len(text)
    body = text[body_start:next_method]
    if "scheduleAutomaticRefresh()" not in body:
        text = text[:body_start] + "\n        self.scheduleAutomaticRefresh()\n" + text[body_start:]
'''
            s = s[:start] + replacement + s[close:]

    manual = r'''def patch_manual_refresh(sidestore: Path) -> None:
    path = sidestore / "AltStore/Managing Apps/AppManager.swift"
    text = path.read_text(encoding="utf-8")
    start = text.index("    func refresh(_ installedApps:")
    end = text.index("    func activate(", start)
    section = text[start:end]
    marker = "let manualHistoryRunID"

    if marker not in section:
        signature = """    func refresh(_ installedApps: [InstalledApp],
                 presentingViewController: UIViewController?,
                 dbContext: NSManagedObjectContext? = nil,
                 group: RefreshGroup? = nil) -> RefreshGroup"""
        if section.count(signature) != 1:
            die(f"manual history signature: expected one anchor, found {section.count(signature)}")

        section = section.replace(
            signature,
            """    func refresh(_ installedApps: [InstalledApp],
                 presentingViewController: UIViewController?,
                 dbContext: NSManagedObjectContext? = nil,
                 group: RefreshGroup? = nil,
                 recordManualHistory: Bool = true) -> RefreshGroup""",
            1,
        )

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
                actualGroup.error = error
                let results = Dictionary(uniqueKeysWithValues: installedApps.map { ($0.bundleIdentifier, Result<InstalledApp, Error>.failure(error)) })
                actualGroup.completionHandler?(results)
            }
        }
"""
        if section.count(detached) != 1:
            die(f"manual history body: expected one anchor, found {section.count(detached)}")
        section = section.replace(detached, replacement, 1)

        text = text[:start] + section + text[end:]
        path.write_text(text, encoding="utf-8")

    for required in (
        "manualHistoryRunID",
        "recordManualHistory: Bool = true",
        "AutomaticRefreshHistory.finishManual",
        "source: .manual",
    ):
        if required not in section:
            die(f"manual history verification failed: {required}")


def verify(sidestore: Path) -> None:
    verify_app_delegate(
        (sidestore / "AltStore" / "AppDelegate.swift").read_text(encoding="utf-8")
    )
    scene = (sidestore / "AltStore" / "SceneDelegate.swift").read_text(encoding="utf-8")
    if "scheduleAutomaticRefresh()" not in scene:
        die("SceneDelegate verification failed")
    settings = (sidestore / "AltStore/Settings/SettingsViewController.swift").read_text(encoding="utf-8")
    if SCHEDULE_UI not in settings or "#selector(openRefreshSchedule)" not in settings:
        die("Settings schedule verification failed")
    console_log = (sidestore / "SideStore/Utils/iostreams/ConsoleLog.swift").read_text(encoding="utf-8")
    for marker in ("LIVE_REFRESH_LOG_RETENTION_V1", "MAX_LOG_BYTES", "MAX_LOG_FILES", "pruneConsoleLogs"):
        if marker not in console_log:
            die(f"Console log retention verification failed: {marker}")
'''
    s = replace_function(s, "patch_manual_refresh", manual)

    SCRIPT.write_text(s, encoding="utf-8")
    print("background automation patch made source-aware for SideStore 0.7.0 AppManager")

if __name__ == "__main__":
    main()
