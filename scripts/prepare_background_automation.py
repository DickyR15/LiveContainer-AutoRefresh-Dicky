#!/usr/bin/env python3
from pathlib import Path

SCRIPT = Path("builder/patch_background_automation.py")

def replace_manual_patch(s: str) -> str:
    start = s.index("def patch_manual_refresh(sidestore: Path) -> None:")
    end = s.index("\ndef patch_info_plist", start)
    new_func = r'''def patch_manual_refresh(sidestore: Path) -> None:
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
    for required in ("manualHistoryRunID", "recordManualHistory: Bool = true",
                     "AutomaticRefreshHistory.finishManual", "source: .manual"):
        if required not in section:
            die(f"manual history verification failed: {required}")

def main():
    s = SCRIPT.read_text(encoding="utf-8")

    # Patch the upstream AppDelegate anchor to locate the method structurally.
    label = '        "application background reschedule",'
    pos = s.find(label)
    if pos >= 0:
        start = s.rfind("    text = replace_once(", 0, pos)
        close = s.find("\n    )", pos)
        if start >= 0 and close >= 0:
            close += len("\n    )")
            replacement = r'''    method_marker = "func applicationDidEnterBackground"
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

    s = replace_manual_patch(s)
    SCRIPT.write_text(s, encoding="utf-8")

if __name__ == "__main__":
    main()
