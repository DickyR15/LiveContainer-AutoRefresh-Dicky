#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

REPLACEMENTS = {
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
        ('Section("Status")', 'Section("狀態")'),
        ('Text("Protection: \\(protection)")', 'Text("保護：\\(localizedProtection(protection))")'),
        ('Toggle("Scheduled refresh"', 'Toggle("排程重新整理"'),
        ('Picker("Frequency"', 'Picker("頻率"'),
        ('Picker("Weekday"', 'Picker("星期"'),
        ('DatePicker("Target time (local)"', 'DatePicker("目標時間（當地時間）"'),
        ('"Auto Refresh: \\(enabled ? "Enabled" : "Disabled")"', '"自動重新整理：\\(enabled ? "已啟用" : "已停用")"'),
        ('"Protection: \\(protection)"', '"保護：\\(protection)"'),
        ('"Refresh: \\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)"', '"重新整理：\\(localizedRefreshState(healthState))"'),
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
        ('Text(result.replacingOccurrences(of: "_", with: " ").capitalized)', 'Text(localizedRefreshHistoryValue(result))'),
        ('Button("Select")', 'Button("選取")'),
        ('"\\(selectedHistoryIDs.count) selected"', '"已選取 \\(selectedHistoryIDs.count) 筆"'),
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
        ('if !lastError.isEmpty { Text(lastError)', 'if !lastError.isEmpty { Text(localizedRefreshError(lastError))'),
        ('Text(localizedRefreshState(result))', 'Text(localizedRefreshState(result))'),
        ('"\\(entry.values["source"]?.capitalized ?? "Unknown") - \\(entry.values["result"]?.capitalized ?? "Unknown")"', '"\\(localizedRefreshHistoryValue(entry.values["source"] ?? "Unknown")) - \\(localizedRefreshHistoryValue(entry.values["result"] ?? "Unknown"))"'),
        ('Text("Refresh: \\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)")', 'Text("重新整理：\\(localizedRefreshState(healthState))")'),
    ],
}

def patch_navigation_generator():
    generator = ROOT / "patch_livecontainer_autorefresh.py"
    if not generator.exists():
        return
    text = generator.read_text(encoding="utf-8")
    before = text
    generator_replacements = [
        ('Text("SideStore scheduled refresh")', 'Text("SideStore 排程重新整理")'),
        ('Toggle("Scheduled refresh"', 'Toggle("排程重新整理"'),
        ('Picker("Frequency"', 'Picker("頻率"'),
        ('Picker("Weekday"', 'Picker("星期"'),
        ('DatePicker("Target time (local)"', 'DatePicker("目標時間（當地時間）"'),
    ]
    for old, new in generator_replacements:
        text = text.replace(old, new)
    if text != before:
        generator.write_text(text, encoding="utf-8")
        print(f"localized: {generator.name} refresh UI labels")

def add_runtime_helpers(text: str) -> str:
    marker = "    private func notifyScheduleChanged() {"
    if "private func localizedRefreshError" in text:
        start = text.index("    private func localizedRefreshError")
        end = text.index(marker, start)
        text = text[:start] + text[end:]
    helpers = '''    private func localizedRefreshState(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").lowercased() {
        case "success", "succeeded", "completed", "verified", "refresh succeeded", "refresh_success": return "成功"
        case "failure", "failed", "refresh failed", "refresh_failure": return "失敗"
        case "pending": return "等待中"
        case "running", "in_progress": return "執行中"
        case "started": return "已開始"
        case "disabled": return "已停用"
        case "enabled": return "已啟用"
        case "unknown": return "未知"
        case "expired": return "已逾期"
        case "cancelled", "canceled": return "已取消"
        default: return raw.replacingOccurrences(of: "_", with: " ")
        }
    }

    private func localizedProtection(_ raw: String) -> String {
        switch raw.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
        case "enhanced": return "增強"
        case "standard": return "標準"
        case "limited": return "有限制"
        case "unknown": return "未知"
        default: return raw
        }
    }

    private func localizedRefreshHistoryValue(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").lowercased() {
        case "success", "succeeded", "completed", "verified": return "成功"
        case "failure", "failed": return "失敗"
        case "pending": return "等待中"
        case "running", "in_progress": return "執行中"
        case "started": return "已開始"
        case "coalesced": return "已合併"
        case "cancelled", "canceled": return "已取消"
        case "manual": return "手動"
        case "automatic", "scheduled", "background": return "自動"
        case "unknown": return "未知"
        default: return raw.replacingOccurrences(of: "_", with: " ")
        }
    }

    private func localizedRefreshError(_ raw: String) -> String {
        var value = raw
        let replacements: [(String, String)] = [
            ("LNPerformActionErrorCodeLocalizedStringResource: VPN Connection Error:", "VPN 連線錯誤："),
            ("LNPerformActionErrorCode.localizedStringResource:", ""),
            ("LNPerformActionErrorCodeLocalizedStringResource:", ""),
            ("VPN Connection Error:", "VPN 連線錯誤："),
            ("No utun interface detected — LocalDevVPN is not connected", "未偵測到 utun 介面 — LocalDevVPN 尚未連線"),
            ("Please make sure LocalDevVPN is connected and running properly.", "請確認 LocalDevVPN 已連線並正常執行。"),
            ("Open LiveContainer and enable LocalDevVPN to continue refresh.", "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"),
            ("LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.", "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。"),
            ("Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.", "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。"),
            ("Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.", "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。"),
            ("Refresh Failed", "重新整理失敗"),
            ("REFRESH FAILED", "重新整理失敗"),
            ("Refresh Succeeded", "重新整理成功"),
            ("Refresh Pending", "重新整理等待中"),
            ("Refresh Running", "重新整理執行中"),
            ("Refresh failed", "重新整理失敗"),
            ("Refresh Failed", "重新整理失敗"),
            ("Failure", "失敗"),
            ("FAILURE", "失敗"),
            ("Failed", "失敗"),
            ("FAILED", "失敗"),
            ("ADI native error", "ADI 原生錯誤"),
            ("ADIOTPRequest failed", "ADIOTPRequest 要求失敗"),
            ("Device not provisioned", "裝置尚未完成佈建"),
            ("A refresh is already running. Wait for it to finish before retrying.", "重新整理正在執行中，請等待完成後再重試。"),
            ("Unknown", "未知"),
            ("UNKNOWN", "未知"),
            ("Standard", "標準"),
            ("STANDARD", "標準"),
            ("Limited", "有限制"),
            ("LIMITED", "有限制")
        ]
        for (source, target) in replacements {
            value = value.replacingOccurrences(of: source, with: target)
        }
        return value.trimmingCharacters(in: .whitespacesAndNewlines)
    }

'''
    if marker not in text:
        raise SystemExit("runtime helper anchor not found in livecontainer_refresh_settings.swift")
    return text.replace(marker, helpers + marker, 1)

def main():
    patch_navigation_generator()
    for name, replacements in REPLACEMENTS.items():
        path = TEMPLATES / name
        if not path.exists():
            raise SystemExit(f"missing localization template: {path}")
        text = path.read_text(encoding="utf-8")
        before = text
        for old, new in replacements:
            text = text.replace(old, new)
        if name == "livecontainer_refresh_settings.swift":
            text = add_runtime_helpers(text)
        if text == before:
            raise SystemExit(f"no localization changes made: {name}")
        path.write_text(text, encoding="utf-8")
        print(f"localized template: {name}")

    settings = (TEMPLATES / "livecontainer_refresh_settings.swift").read_text(encoding="utf-8")
    forbidden = [
        'Toggle("Scheduled refresh"', 'Picker("Frequency"',
        'Picker("Weekday"', 'DatePicker("Target time (local)"',
        'Text("Protection: ', 'Text("SideStore scheduled refresh")'
    ]
    leaked = [item for item in forbidden if item in settings]
    if leaked:
        raise SystemExit("English UI strings remain in refresh settings: " + ", ".join(leaked))

    print("Taiwan Traditional Chinese AutoRefresh UI localization: PASS")

if __name__ == "__main__":
    main()
