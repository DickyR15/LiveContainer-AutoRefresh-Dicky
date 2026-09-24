#!/usr/bin/env python3
from pathlib import Path
import re
import sys

def fail(msg: str) -> None:
    raise SystemExit("force_autorefresh_runtime_localization: " + msg)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)

def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: force_autorefresh_runtime_localization.py <livecontainer-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "LiveContainerSwiftUI/Views/Settings/LCEmbeddedSideStoreRefreshView.swift"
    if not path.exists():
        fail(f"missing generated settings view: {path}")
    text = path.read_text(encoding="utf-8")

    # Patch the actual SwiftUI calls. Whitespace/line breaks around these
    # calls are irrelevant, so replace the exact expression itself.
    error_token = "Text(lastError)"
    error_localized = "Text(localizedRefreshError(lastError))"
    if error_token in text:
        text = text.replace(error_token, error_localized, 1)
    elif error_localized not in text:
        fail("runtime error display: neither raw nor localized Text(lastError) exists")

    history_old = 'Text("\\(entry.values["source"]?.capitalized ?? "Unknown") - \\(entry.values["result"]?.capitalized ?? "Unknown")")'
    history_new = 'Text("\\(localizedRefreshHistoryValue(entry.values["source"] ?? "Unknown")) - \\(localizedRefreshHistoryValue(entry.values["result"] ?? "Unknown"))")'
    if history_old in text:
        text = text.replace(history_old, history_new, 1)
    elif history_new not in text:
        fail("history result display: neither raw nor localized history Text(...) exists")

    marker = "    private func notifyScheduleChanged() {"
    if "private func localizedRefreshError" not in text:
        if marker not in text:
            fail("runtime helper insertion anchor missing")
        helpers = r'''    private func localizedRefreshHistoryValue(_ raw: String) -> String {
        switch raw.replacingOccurrences(of: "_", with: " ").trimmingCharacters(in: .whitespacesAndNewlines).lowercased() {
        case "success", "succeeded", "completed", "verified": return "成功"
        case "failure", "failed", "refresh failed", "refresh_failure": return "失敗"
        case "pending": return "等待中"
        case "running", "in_progress": return "執行中"
        case "started": return "已開始"
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
            ("LNPerformActionErrorCodeLocalizedStringResource:", ""),
            ("LNPerformActionErrorCode.localizedStringResource:", ""),
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
            ("Failure", "失敗"),
            ("FAILURE", "失敗"),
            ("Failed", "失敗"),
            ("FAILED", "失敗"),
            ("Unknown", "未知"),
            ("UNKNOWN", "未知"),
            ("Limited", "有限制"),
            ("LIMITED", "有限制")
        ]
        for (source, target) in replacements {
            value = value.replacingOccurrences(of: source, with: target)
        }
        return value.trimmingCharacters(in: .whitespacesAndNewlines)
    }

'''
        text = text.replace(marker, helpers + marker, 1)

    path.write_text(text, encoding="utf-8")

    required = [
        'Text(localizedRefreshError(lastError))',
        'localizedRefreshHistoryValue(entry.values["result"] ?? "Unknown")',
        'private func localizedRefreshError',
        'private func localizedRefreshHistoryValue',
        'VPN 連線錯誤：',
        '未偵測到 utun 介面',
        '請確認 LocalDevVPN 已連線並正常執行。'
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail("generated source is still missing: " + ", ".join(missing))

    print("Forced runtime AutoRefresh zh-TW localization: PASS")
    print(path)

if __name__ == "__main__":
    main()
