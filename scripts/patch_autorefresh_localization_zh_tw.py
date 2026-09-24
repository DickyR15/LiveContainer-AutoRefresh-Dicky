#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

REPLACEMENTS = {
    "combined_failure.swift": [
        ('"The \\(operation) request was cancelled. Its result may need reconciliation."', '"\\(operation) 請求已取消。可能需要重新確認結果。"'),
        ('"The \\(operation) request timed out during \\(stage.rawValue)."', '"\\(operation) 請求在 \\(stage.rawValue) 階段逾時。"'),
        ('"Could not connect to the device through CoreDevice."', '"無法透過 CoreDevice 連線至裝置。"'),
        ('"The CoreDevice tunnel could not be established."', '"無法建立 CoreDevice 通道。"'),
        ('"Refresh completion could not be verified from the installation results."', '"無法從安裝結果驗證重新整理是否完成。"'),
        ('"SideStore could not sign the application."', '"SideStore 無法簽名此 App。"'),
        ('"Check LocalDevVPN and the device connection, then retry explicitly. This failure alone does not prove invalid pairing."', '"請檢查 LocalDevVPN 與裝置連線後再手動重試。僅憑此錯誤無法判定配對無效。"'),
    ],
    "livecontainer_network_preflight.swift": [
        ('"LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh."', '"LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。"'),
        ('"Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry."', '"啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。"'),
        ('"Open LiveContainer and enable LocalDevVPN to continue refresh."', '"請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"'),
    ],
    "v3_unified_shell.swift": [
        ('Button("Retry Connection")', 'Button("重新連線")'),
        ('Text("LiveContainer can notify you when a refresh starts, completes, or needs attention. Nothing runs differently if you skip this.")', 'Text("LiveContainer 可以在重新整理開始、完成或需要注意時通知你。略過此設定不會影響其他功能。")'),
        ('Button("Refresh All")', 'Button("全部重新整理")'),
        ('Button("Refresh")', 'Button("重新整理")'),
        ('Button("Retry")', 'Button("重試")'),
        ('Section("Account and Signing")', 'Section("帳號與簽名")'),
        ('Label("Signing", systemImage: "signature")', 'Label("簽名", systemImage: "signature")'),
        ('Label("Refresh " + app.name, systemImage: "arrow.clockwise")', 'Label("重新整理 " + app.name, systemImage: "arrow.clockwise")'),
        ('Button("Clear Selection")', 'Button("清除選取")'),
        ('Label("Add Source and Retry", systemImage: "plus.circle.fill")', 'Label("加入來源並重試", systemImage: "plus.circle.fill")'),
        ('Section("Signing")', 'Section("簽名")'),
        ('Button("Test Reachability")', 'Button("測試連線")'),
        ('Text("Experimental options can change or disappear. Current signing state is never reset by toggling them.")', 'Text("實驗性選項可能變更或移除。切換這些選項不會重設目前的簽名狀態。")'),
        ('.navigationTitle("Refresh")', '.navigationTitle("重新整理")'),
        ('Section("Background Refresh")', 'Section("背景重新整理")'),
        ('Text("Refresh start, completion and deadline warnings arrive as notifications.")', 'Text("重新整理開始、完成及期限警告會以通知方式送達。")'),
        ('Label("Allow Refresh Notifications", systemImage: "bell.fill")', 'Label("允許重新整理通知", systemImage: "bell.fill")'),
        ('Section("Automatic Refresh")', 'Section("自動重新整理")'),
        ('Button("Cancel Test", role: .cancel)', 'Button("取消測試", role: .cancel)'),
        ('Label("Run Test Refresh", systemImage: "arrow.clockwise")', 'Label("執行重新整理測試", systemImage: "arrow.clockwise")'),
        ('Text("Account, pairing and a verified refresh are all in place.")', 'Text("帳號、配對及已驗證的重新整理皆已完成設定。")'),
        ('Label("Signing Status", systemImage: "signature")', 'Label("簽名狀態", systemImage: "signature")'),
        ('Label("Refresh Deadline", systemImage: "hourglass")', 'Label("重新整理期限", systemImage: "hourglass")'),
        ('Label("Last Refresh Warning", systemImage: "exclamationmark.triangle")', 'Label("上次重新整理警告", systemImage: "exclamationmark.triangle")'),
        ('Label("Open Refresh Manager", systemImage: "arrow.clockwise")', 'Label("開啟重新整理管理工具", systemImage: "arrow.clockwise")'),
        ('"Background App Refresh: available"', '"背景 App 重新整理：可用"'),
        ('"Background App Refresh: denied"', '"背景 App 重新整理：已拒絕"'),
        ('"Background App Refresh: restricted"', '"背景 App 重新整理：受限制"'),
        ('"Background App Refresh: unknown"', '"背景 App 重新整理：未知"'),
        ('"Refresh schedule: "', '"重新整理排程："'),
        ('"Last verified refresh: "', '"上次驗證的重新整理："'),
        ('"Last verified refresh: none"', '"尚未有驗證成功的重新整理"'),
        ('setupRow(icon: "clock.arrow.circlepath", title: "Background App Refresh",', 'setupRow(icon: "clock.arrow.circlepath", title: "背景 App 重新整理",'),
        ('setupRow(icon: "calendar.badge.clock", title: "Schedule",', 'setupRow(icon: "calendar.badge.clock", title: "排程",'),
        ('setupRow(icon: "checkmark.seal", title: "Test Refresh",', 'setupRow(icon: "checkmark.seal", title: "測試重新整理",'),
        ('"Verified by successful refresh"', '"已透過成功的重新整理驗證"'),
        ('"Checked after a successful refresh"', '"成功重新整理後檢查"'),
    ],
    "livecontainer_refresh_settings.swift": [
        ('if !lastError.isEmpty { Text(lastError).font(.caption).foregroundColor(.red) }',
         'if !lastError.isEmpty { Text(localizedRefreshError(lastError)).font(.caption).foregroundColor(.red) }'),
        ('Section("Status")', 'Section("狀態")'),
        ('"Auto Refresh: \\(enabled ? "Enabled" : "Disabled")"', '"自動重新整理：\\(enabled ? "已啟用" : "已停用")"'),
        ('"Protection: \\(protection)"', '"保護：\\(protection)"'),
        ('"Refresh: \\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)"', '"重新整理：\\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)"'),
        ('"Background execution remains best-effort. A scheduled request is not a completed refresh."', '"背景執行會盡力進行。排程請求不代表重新整理已完成。"'),
        ('Button("Copy Refresh Diagnostics")', 'Button("複製重新整理診斷資訊")'),
        ('"The previous refresh result is uncertain. Automatic retries are paused. Review app status and expiration before explicitly retrying."', '"上次重新整理的結果不確定。自動重試已暫停。請先檢查 App 狀態與有效期限，再手動重試。"'),
        ('Button("Refresh SideStore now", action: notifyManualRefresh)', 'Button("立即重新整理 SideStore", action: notifyManualRefresh)'),
        ('Text("Every six hours")', 'Text("每 6 小時")'),
        ('Text("Daily")', 'Text("每天")'),
        ('Text("Weekly")', 'Text("每週")'),
        ('"A weekly schedule can be too late for free-account signing. Prefer daily refresh."', '"每週排程對免費帳號簽名可能太晚，建議使用每日重新整理。"'),
        ('"Refresh can start before the target time to allow for iOS scheduling delays."', '"重新整理可能會在目標時間之前開始，以因應 iOS 排程延遲。"'),
        ('Section("Warnings")', 'Section("警告")'),
        ('Button("Allow refresh notifications")', 'Button("允許重新整理通知")'),
        ('Button("Enable optional deadline alarm")', 'Button("啟用期限提醒")'),
        ('"Warnings require permission. A deadline warning asks you to check an unconfirmed refresh; it cannot diagnose a task that never ran."', '"警告需要通知權限。期限提醒會要求你確認尚未驗證的重新整理；它無法判斷未執行的背景工作。"'),
        ('Section("Last result")', 'Section("上次結果")'),
        ('.navigationTitle("SideStore refresh")', '.navigationTitle("SideStore 重新整理")'),
        ('Button("Clear All", role: .destructive)', 'Button("全部清除", role: .destructive)'),
        ('Button("Cancel", role: .cancel)', 'Button("取消", role: .cancel)'),
        ('"This deletes history entries only. Refresh settings and the current signing status are not changed."', '"這只會刪除歷史記錄，不會變更重新整理設定或目前的簽名狀態。"'),
        ('"\\(selectedHistoryIDs.count) selected"', '"已選取 \\(selectedHistoryIDs.count) 筆"'),
        ('Button("Delete Selected", role: .destructive, action: deleteSelectedHistory)', 'Button("刪除選取項目", role: .destructive, action: deleteSelectedHistory)'),
        ('"No refreshes recorded"', '"尚未記錄重新整理"'),
        ('Text("History")', 'Text("歷史記錄")'),
        ('"Swipe right to reveal Delete, or use Select to delete several entries. Deleting history does not change refresh status or scheduled tasks."', '"向右滑動即可顯示刪除選項，也可以使用選取功能一次刪除多筆記錄。刪除歷史記錄不會變更重新整理狀態或排程工作。"'),
        ('Label("Delete", systemImage: "trash")', 'Label("刪除", systemImage: "trash")'),
        ('.accessibilityAction(named: Text("Delete"))', '.accessibilityAction(named: Text("刪除"))'),
        ('"Refresh Failed"', '"重新整理失敗"'),
        ('"Refresh Succeeded"', '"重新整理成功"'),
        ('"Refresh Pending"', '"重新整理等待中"'),
        ('"Refresh Running"', '"重新整理執行中"'),
        ('"Refresh Unknown"', '"重新整理狀態未知"'),
        ('"Scheduled refresh"', '"排程重新整理"'),
        ('"Frequency"', '"頻率"'),
        ('"Target time (local)"', '"目標時間（當地時間）"'),
        ('"Standard"', '"標準"'),
        ('"Limited"', '"有限制"'),
        ('"Unknown"', '"未知"'),
        ('"Enabled"', '"已啟用"'),
        ('"Disabled"', '"已停用"'),
        ('"Success"', '"成功"'),
        ('"Failed"', '"失敗"'),
        ('"Pending"', '"等待中"'),
        ('"Running"', '"執行中"'),
        ('"Completed"', '"已完成"'),
        ('"Error"', '"錯誤"'),
        ('"Permission required"', '"需要授權"'),
        ('"Permission denied"', '"授權遭拒"'),
        ('"Not configured"', '"尚未設定"'),
        ('"Failure"', '"失敗"'),
        ('"VPN Connection Error:"', '"VPN 連線錯誤："'),
        ('"No utun interface detected — LocalDevVPN is not connected"', '"未偵測到 utun 介面 — LocalDevVPN 尚未連線"'),
        ('"Please make sure LocalDevVPN is connected and running properly."', '"請確認 LocalDevVPN 已連線並正常執行。"'),
        ('"Refresh Failed"', '"重新整理失敗"'),
        ('"Refresh Succeeded"', '"重新整理成功"'),
        ('"Refresh Pending"', '"重新整理等待中"'),
        ('"Refresh Running"', '"重新整理執行中"'),
        ('"LocalDevVPN"', '"LocalDevVPN"'),
        ('"SideStore scheduled refresh"', '"SideStore 排程重新整理"'),

    ],
}

def main():
    # The upstream integration script injects this navigation label after the
    # template localization pass. Patch that exact source before integration.
    generator = ROOT / "patch_livecontainer_autorefresh.py"
    if generator.exists():
        text = generator.read_text(encoding="utf-8")
        before = text
        text = text.replace(
            'NavigationLink { LCEmbeddedSideStoreRefreshView() } label: { Text("SideStore scheduled refresh") }',
            'NavigationLink { LCEmbeddedSideStoreRefreshView() } label: { Text("SideStore 排程重新整理") }',
        )
        if text != before:
            generator.write_text(text, encoding="utf-8")
            print("localized: patch_livecontainer_autorefresh.py injected label")

    for name, replacements in REPLACEMENTS.items():
        path = TEMPLATES / name
        text = path.read_text(encoding="utf-8")
        before = text
        for old, new in replacements:
            text = text.replace(old, new)

        # Dynamic refresh status and diagnostics are generated at runtime.
        if name == "livecontainer_refresh_settings.swift":
            text = text.replace(
                '"Refresh: \\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)"',
                '"重新整理：\\(localizedRefreshState(healthState))"',
            )
            text = text.replace(
                'Text(result.replacingOccurrences(of: "_", with: " ").capitalized)',
                'Text(localizedRefreshState(result))',
            )
            marker = "    private func notifyScheduleChanged() {"
            helpers = '''    private func localizedRefreshError(_ raw: String) -> String {
        var value = raw
        let replacements: [(String, String)] = [
            ("LNPerformActionErrorCode.localizedStringResource:", ""),
            ("VPN Connection Error:", "VPN 連線錯誤："),
            ("No utun interface detected — LocalDevVPN is not connected", "未偵測到 utun 介面 — LocalDevVPN 尚未連線"),
            ("Please make sure LocalDevVPN is connected and running properly.", "請確認 LocalDevVPN 已連線並正常執行。"),
            ("Open LiveContainer and enable LocalDevVPN to continue refresh.", "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"),
            ("Refresh Failed", "重新整理失敗"),
            ("Refresh Succeeded", "重新整理成功"),
            ("Refresh Pending", "重新整理等待中"),
            ("Refresh Running", "重新整理執行中"),
            ("Failure", "失敗"),
            ("Failed", "失敗"),
            ("Unknown", "未知"),
            ("Standard", "標準"),
            ("Limited", "有限制")
        ]
        for (source, target) in replacements {
            value = value.replacingOccurrences(of: source, with: target)
        }
        return value.trimmingCharacters(in: .whitespacesAndNewlines)
    }

            marker = "    private func notifyScheduleChanged() {"
            helpers = '''    private func localizedRefreshState(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").lowercased() {
        case "success", "succeeded", "completed": return "成功"
        case "failure", "failed": return "失敗"
        case "pending": return "等待中"
        case "running": return "執行中"
        case "started": return "已開始"
        case "disabled": return "已停用"
        case "enabled": return "已啟用"
        case "unknown": return "未知"
        default: return raw.replacingOccurrences(of: "_", with: " ")
        }
    }

'''
            if marker in text and "private func localizedRefreshState" not in text:
                text = text.replace(marker, helpers + marker, 1)

        if text == before:
            raise SystemExit(f"no changes made: {name}")
        path.write_text(text, encoding="utf-8")
        print(f"localized: {name}")
    # Final generated-source sweep: some strings are emitted by the pinned
    # SideStore/minimuxer sources after the template pass. These are user-visible
    # diagnostics, so patch the generated Swift too. Keep identifiers such as
    # LocalDevVPN unchanged.
    generated_replacements = {
        '"Refresh Failed"': '"重新整理失敗"',
        '"Refresh Succeeded"': '"重新整理成功"',
        '"Refresh Pending"': '"重新整理等待中"',
        '"Refresh Running"': '"重新整理執行中"',
        '"Refresh Unknown"': '"重新整理狀態未知"',
        '"Failure"': '"失敗"',
        '"Failed"': '"失敗"',
        '"Success"': '"成功"',
        '"Completed"': '"已完成"',
        '"Pending"': '"等待中"',
        '"Running"': '"執行中"',
        '"Unknown"': '"未知"',
        '"VPN Connection Error:"': '"VPN 連線錯誤："',
        '"No utun interface detected — LocalDevVPN is not connected"': '"未偵測到 utun 介面 — LocalDevVPN 尚未連線"',
        '"Please make sure LocalDevVPN is connected and running properly."': '"請確認 LocalDevVPN 已連線並正常執行。"',
        '"SideStore scheduled refresh"': '"SideStore 排程重新整理"',
        '"Scheduled refresh"': '"排程重新整理"',
        '"Frequency"': '"頻率"',
        '"Target time (local)"': '"目標時間（當地時間）"',
        '"Standard"': '"標準"',
        '"Limited"': '"有限制"',
        '"Enabled"': '"已啟用"',
        '"Disabled"': '"已停用"',
    }
    for swift in ROOT.rglob("*.swift"):
        if ".git" in swift.parts:
            continue
        try:
            text = swift.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        before = text
        for old, new in generated_replacements.items():
            text = text.replace(old, new)
        if text != before:
            swift.write_text(text, encoding="utf-8")
            print(f"localized generated Swift: {swift.relative_to(ROOT)}")

    print("Taiwan Traditional Chinese AutoRefresh localization: PASS")

if __name__ == "__main__":
    main()
