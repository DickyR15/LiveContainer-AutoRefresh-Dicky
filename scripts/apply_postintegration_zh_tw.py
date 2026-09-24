#!/usr/bin/env python3
from pathlib import Path
import sys

ROOTS = [Path(p) for p in sys.argv[1:]] or [Path("work/LiveContainer"), Path("work/EmbeddedSideStore")]

REPLACEMENTS = {
    "SideStore scheduled refresh": "SideStore 排程重新整理",
    "Scheduled refresh": "排程重新整理",
    "Refresh Schedule": "SideStore 排程重新整理",
    "Background Refresh": "背景重新整理",
    "Background App Refresh": "背景 App 重新整理",
    "Target time (local)": "目標時間（當地時間）",
    "Preferred Time (Local)": "偏好時間（當地時間）",
    "Frequency": "頻率",
    "Every six hours": "每 6 小時",
    "Allow refresh notifications": "允許重新整理通知",
    "Enable optional deadline alarm": "啟用期限提醒",
    "Notification Permission": "通知權限",
    "Notification Settings": "通知設定",
    "No refresh history": "尚未有重新整理記錄",
    "No refreshes recorded": "尚未記錄重新整理",
    "Clear History": "清除歷史記錄",
    "Clear all refresh history?": "要清除所有重新整理歷史記錄嗎？",
    "Clear All": "全部清除",
    "Delete Selected": "刪除選取項目",
    "Delete": "刪除",
    "History": "歷史記錄",
    "Last result": "上次結果",
    "Refresh Failed": "重新整理失敗",
    "Refresh Succeeded": "重新整理成功",
    "Refresh Pending": "重新整理等待中",
    "Refresh Running": "重新整理執行中",
    "Refresh Unknown": "重新整理狀態未知",
    "Failure": "失敗",
    "Failed": "失敗",
    "Success": "成功",
    "Permission required": "需要授權",
    "Permission denied": "授權遭拒",
    "Not configured": "尚未設定",
    "VPN Connection Error:": "VPN 連線錯誤：",
    "No utun interface detected — LocalDevVPN is not connected": "未偵測到 utun 介面 — LocalDevVPN 尚未連線",
    "Please make sure LocalDevVPN is connected and running properly.": "請確認 LocalDevVPN 已連線並正常執行。",
    "Open LiveContainer and enable LocalDevVPN to continue refresh.": "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。",
    "LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.": "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。",
    "Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.": "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。",
    "Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.": "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。",
    "The previous refresh result is uncertain. Automatic retries are paused. Review app status and expiration before explicitly retrying.": "上次重新整理的結果不確定。自動重試已暫停。請先檢查 App 狀態與有效期限，再手動重試。",
    "Background execution remains best-effort. A scheduled request is not a completed refresh.": "背景執行會盡力進行。排程請求不代表重新整理已完成。",
}

changed_files = 0
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*.swift"):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        old = text
        for source, target in REPLACEMENTS.items():
            text = text.replace(source, target)
        if text != old:
            path.write_text(text, encoding="utf-8")
            changed_files += 1
            print(f"localized: {path}")

print(f"Post-integration zh-TW localization: PASS ({changed_files} files changed)")
