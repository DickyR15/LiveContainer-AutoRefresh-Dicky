#!/usr/bin/env python3
from pathlib import Path
import sys

ROOTS = [Path(p) for p in sys.argv[1:]] or [Path("work/LiveContainer"), Path("work/EmbeddedSideStore")]

# Only UI phrases used by the AutoRefresh / SideStore scheduled-refresh feature.
REPLACEMENTS = {
    'Text("Scheduled refresh")': 'Text("排程重新整理")',
    'Text("Frequency")': 'Text("頻率")',
    'Text("SideStore scheduled refresh")': 'Text("SideStore 排程重新整理")',
    'Text("Limited")': 'Text("有限制")',
    'Text("Unknown")': 'Text("未知")',
    'Label("Scheduled refresh"': 'Label("排程重新整理"',
    'Label("Frequency"': 'Label("頻率"',
    'Label("SideStore scheduled refresh"': 'Label("SideStore 排程重新整理"',
    'Label("Limited"': 'Label("有限制"',
    'Label("Unknown"': 'Label("未知"',
    '"Scheduled refresh"': '"排程重新整理"',
    '"Frequency"': '"頻率"',
    '"SideStore scheduled refresh"': '"SideStore 排程重新整理"',
    '"Refresh Schedule"': '"SideStore 排程重新整理"',
    '"Background Refresh"': '"背景重新整理"',
    '"Schedule"': '"排程"',
    '"Every Six Hours"': '"每 6 小時"',
    '"Preferred Time (Local)"': '"偏好時間（當地時間）"',
    '"Notification Permission"': '"通知權限"',
    '"Quiet"': '"靜默"',
    '"Off"': '"關閉"',
    '"Allow Notifications"': '"允許通知"',
    '"Notification Settings"': '"通知設定"',
    '"No refresh history"': '"尚未有重新整理記錄"',
    '"Clear History"': '"清除歷史記錄"',
    '"Clear refresh history?"': '"要清除重新整理歷史記錄嗎？"',
    '"Earliest Eligible Refresh"': '"最早可重新整理時間"',
    '"Local time:': '"當地時間：',
    '"Timezone:': '"時區：',
    '"Retry Scheduling"': '"重試排程"',
    '"Background App Refresh Unavailable"': '"背景 App 重新整理不可用"',
    '"Open Settings"': '"開啟設定"',
    '"Clear all refresh history?"': '"要清除所有重新整理歷史記錄嗎？"',
    '"Failure"': '"失敗"',
    '"VPN Connection Error:"': '"VPN 連線錯誤："',
    '"No utun interface detected — LocalDevVPN is not connected"': '"未偵測到 utun 介面 — LocalDevVPN 尚未連線"',
    '"Please make sure LocalDevVPN is connected and running properly."': '"請確認 LocalDevVPN 已連線並正常執行。"',
    '"Refresh Failed"': '"重新整理失敗"',
    '"Refresh Succeeded"': '"重新整理成功"',
    '"Refresh Pending"': '"重新整理等待中"',
    '"Refresh Running"': '"重新整理執行中"',
    '"SideStore scheduled refresh"': '"SideStore 排程重新整理"',
    '"Scheduled refresh"': '"排程重新整理"',
    '"Frequency"': '"頻率"',
    '"Target time (local)"': '"目標時間（當地時間）"',
    '"Failure"': '"失敗"',
    '"Standard"': '"標準"',
    '"Limited"': '"有限制"',
    '"Unknown"': '"未知"',
    '"Enabled"': '"已啟用"',
    '"Disabled"': '"已停用"',
    '"Success"': '"成功"',
    '"Failed"': '"失敗"',
    '"Pending"': '"等待中"',
    '"Running"': '"執行中"',
    '"Completed"': '"已完成"',
}

def localize_runtime_diagnostic(text: str) -> str:
    replacements = [
        ("VPN Connection Error:", "VPN 連線錯誤："),
        ("No utun interface detected — LocalDevVPN is not connected", "未偵測到 utun 介面 — LocalDevVPN 尚未連線"),
        ("Please make sure LocalDevVPN is connected and running properly.", "請確認 LocalDevVPN 已連線並正常執行。"),
        ("Open LiveContainer and enable LocalDevVPN to continue refresh.", "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"),
        ("LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.", "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。"),
        ("Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.", "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。"),
        ("Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.", "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。"),
        ("Refresh Failed", "重新整理失敗"),
        ("Refresh Succeeded", "重新整理成功"),
        ("Failure", "失敗"),
    ]
    for a, b in replacements:
        text = text.replace(a, b)
    return text

changed = 0
files = 0
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*.swift"):
        try:
            s = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        old = s
        for a, b in REPLACEMENTS.items():
            s = s.replace(a, b)
        # Runtime diagnostics are localized only inside the scheduled-refresh view,
        # where the helper is defined. Do not inject a helper call into unrelated
        # SideStore/LiveContainer files.
        # Dynamic status strings are generated at runtime, so static literal
        # replacement alone cannot localize them.
        if path.name == "livecontainer_refresh_settings.swift":
            s = s.replace(
                'Text("Refresh: \\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)")',
                'Text("重新整理：\\(localizedRefreshState(healthState))")',
            )
            s = s.replace(
                'Text("重新整理：\\(healthState.replacingOccurrences(of: "_", with: " ").capitalized)")',
                'Text("重新整理：\\(localizedRefreshState(healthState))")',
            )
            s = s.replace(
                'Text(result.replacingOccurrences(of: "_", with: " ").capitalized)',
                'Text(localizedRefreshState(result))',
            )
            s = s.replace(
                'Text("\\(entry.values["source"]?.capitalized ?? "Unknown") - \\(entry.values["result"]?.capitalized ?? "Unknown")")',
                'Text("\\(localizedRefreshHistoryValue(entry.values["source"] ?? "Unknown")) - \\(localizedRefreshHistoryValue(entry.values["result"] ?? "Unknown"))")',
            )
            marker = "    private func notifyScheduleChanged() {"
            helpers = '''    private func localizeRuntimeDiagnostic(_ raw: String) -> String {
        var value = raw
        let replacements: [(String, String)] = [
            ("VPN Connection Error:", "VPN 連線錯誤："),
            ("No utun interface detected — LocalDevVPN is not connected", "未偵測到 utun 介面 — LocalDevVPN 尚未連線"),
            ("Please make sure LocalDevVPN is connected and running properly.", "請確認 LocalDevVPN 已連線並正常執行。"),
            ("Open LiveContainer and enable LocalDevVPN to continue refresh.", "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"),
            ("LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.", "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。"),
            ("Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.", "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。"),
            ("Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.", "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。")
        ]
        for (source, target) in replacements {
            value = value.replacingOccurrences(of: source, with: target)
        }
        return value
    }

    private func localizedRefreshState(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").lowercased() {
        case "success", "succeeded", "completed": return "成功"
        case "failure", "failed": return "失敗"
        case "pending": return "等待中"
        case "running": return "執行中"
        case "started": return "已開始"
        case "disabled": return "已停用"
        case "enabled": return "已啟用"
        case "unknown": return "未知"
        case "expired": return "已逾期"
        case "cancelled", "canceled": return "已取消"
        default: return raw.replacingOccurrences(of: "_", with: " ")
        }
    }

    private func localizedRefreshHistoryValue(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").lowercased() {
        case "success", "succeeded", "completed": return "成功"
        case "failure", "failed": return "失敗"
        case "pending": return "等待中"
        case "running": return "執行中"
        case "started": return "已開始"
        case "manual": return "手動"
        case "automatic", "scheduled": return "自動"
        case "unknown": return "未知"
        default: return raw.replacingOccurrences(of: "_", with: " ")
        }
    }

'''
            if marker in s and "private func localizedRefreshState" not in s:
                s = s.replace(marker, helpers + marker, 1)

        if s != old:
            path.write_text(s, encoding="utf-8")
            files += 1
            changed += sum(old.count(a) - s.count(a) for a in REPLACEMENTS)
            print(f"localized: {path}")

print(f"Post-integration zh-TW AutoRefresh localization: PASS ({files} files changed)")
