#!/usr/bin/env python3
from pathlib import Path
import sys
import re

ROOTS = [Path(p) for p in sys.argv[1:]] or [Path("work/LiveContainer"), Path("work/EmbeddedSideStore")]

REPLACEMENTS = {
    "SideStore scheduled refresh": "SideStore 排程重新整理",
    "Scheduled refresh": "排程重新整理",
    "scheduled refresh": "排程重新整理",
    "REFRESH FAILED": "重新整理失敗",
    "REFRESH FAILED:": "重新整理失敗：",
    "Limited": "有限制",
    "LIMITED": "有限制",
    "Frequency": "頻率",
    "Target time (local)": "目標時間（當地時間）",
    "Target time (Local)": "目標時間（當地時間）",
    "Weekday": "星期",
    "Every six hours": "每 6 小時",
    "Daily": "每天",
    "Weekly": "每週",
    "Refresh Schedule": "SideStore 排程重新整理",
    "Background Refresh": "背景重新整理",
    "Background App Refresh": "背景 App 重新整理",
    "Preferred Time (Local)": "偏好時間（當地時間）",
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

    # Runtime/native error text. These are also handled as substrings below
    # because some iOS error descriptions prepend a framework-generated label.
    "LNPerformActionErrorCodeLocalizedStringResource:": "",
    "LNPerformActionErrorCode.localizedStringResource:": "",
    "VPN Connection Error:": "VPN 連線錯誤：",
    "No utun interface detected — LocalDevVPN is not connected": "未偵測到 utun 介面 — LocalDevVPN 尚未連線",
    "Please make sure LocalDevVPN is connected and running properly.": "請確認 LocalDevVPN 已連線並正常執行。",
    "Open LiveContainer and enable LocalDevVPN to continue refresh.": "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。",
    "LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.": "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。",
    "Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.": "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。",
    "Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.": "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。",
    "The previous refresh result is uncertain. Automatic retries are paused. Review app status and expiration before explicitly retrying.": "上次重新整理的結果不確定。自動重試已暫停。請先檢查 App 狀態與有效期限，再手動重試。",
    "Background execution remains best-effort. A scheduled request is not a completed refresh.": "背景執行會盡力進行。排程請求不代表重新整理已完成。",

    # Structured CombinedFailure messages/recovery text.
    "The refresh request was cancelled. Its result may need reconciliation.": "重新整理要求已取消，結果可能需要重新確認。",
    "timed out during": "在以下階段逾時：",
    "SideStore could not start because the authoritative host container is unavailable.": "SideStore 無法啟動，因為主要主機容器目前無法使用。",
    "SideStore could not start because its existing data storage could not be prepared.": "SideStore 無法啟動，因為現有資料儲存空間無法準備。",
    "SideStore could not start because its data bookmark could not be created.": "SideStore 無法啟動，因為無法建立資料書籤。",
    "The embedded LiveProcess extension is missing or unavailable.": "內嵌的 LiveProcess 延伸模組遺失或無法使用。",
    "The embedded SideStore process could not be launched.": "無法啟動內嵌的 SideStore 程序。",
    "The connection to the embedded SideStore service was interrupted or unavailable.": "與內嵌 SideStore 服務的連線已中斷或無法使用。",
    "The SideStore process has not finished preparing its service.": "SideStore 程序尚未完成服務準備。",
    "No usable device transport endpoint was selected.": "沒有選取到可用的裝置傳輸端點。",
    "The device transport heartbeat is inactive.": "裝置傳輸心跳目前未啟用。",
    "Could not connect to the device through CoreDevice.": "無法透過 CoreDevice 連線到裝置。",
    "The CoreDevice tunnel could not be established.": "無法建立 CoreDevice 通道。",
    "Device service discovery through RSD failed.": "透過 RSD 尋找裝置服務失敗。",
    "The requested RSD device service could not be connected.": "無法連線到要求的 RSD 裝置服務。",
    "The device transport opened, but the lockdownd connection failed.": "裝置傳輸已開啟，但 lockdownd 連線失敗。",
    "The device connection opened, but the UniqueDeviceID request failed.": "裝置連線已開啟，但 UniqueDeviceID 要求失敗。",
    "Pairing parsing, validation, or a concrete device trust check failed.": "配對檔解析、驗證或實際裝置信任檢查失敗。",
    "SideStore could not complete account authentication.": "SideStore 無法完成帳號驗證。",
    "SideStore could not sign the application.": "SideStore 無法完成 App 簽名。",
    "SideStore could not complete the application installation.": "SideStore 無法完成 App 安裝。",
    "Refresh completion could not be verified from the installation results.": "無法從安裝結果驗證重新整理是否完成。",
    "SideStore could not complete the requested": "SideStore 無法完成要求的",
    "The embedded SideStore process": "內嵌的 SideStore 程序",
    "Keep existing data intact. Return to the host, check available storage, and use Retry Connection. Copy these diagnostics if it fails again.": "請保留現有資料。返回主機後確認可用儲存空間，再使用「重新連線」。若再次失敗，請複製診斷資訊。",
    "Check that the installed combined package retains LiveProcess and its extension registration. Do not reset SideStore or guest data.": "請確認已安裝的整合套件仍包含 LiveProcess 及其延伸模組註冊。請勿重設 SideStore 或訪客資料。",
    "Review Account and Signing, then explicitly retry. Never share credentials or private keys.": "請檢查「帳號與簽名」後手動重試。請勿分享帳號憑證或私鑰。",
    "Reload authoritative app status and expiration before retrying. Completion may be uncertain.": "重試前請重新載入主要 App 狀態與有效期限。重新整理是否完成可能尚未確認。",
    "Check LocalDevVPN and the device connection, then retry explicitly. This failure alone does not prove invalid pairing.": "請檢查 LocalDevVPN 與裝置連線後手動重試。單憑這次失敗無法判定配對無效。",
    "Reconnect explicitly and reload authoritative status before repeating a mutation.": "請先手動重新連線並重新載入主要狀態，再重試操作。",
}

def replace_in_swift_string_literals(text: str) -> str:
    for source, target in REPLACEMENTS.items():
        pattern = r'(["\'])' + re.escape(source) + r'\1'
        text = re.sub(pattern, lambda m: m.group(1) + target + m.group(1), text)
    return text

def main():
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

            # First pass: exact user-visible Swift string literals only.
            text = replace_in_swift_string_literals(text)

            # Second pass: localize runtime/native descriptions that can contain
            # framework-generated prefixes or be assembled dynamically. This pass
            # operates only on known error-message fragments, never identifiers.
            runtime_replacements = [
                ("LNPerformActionErrorCodeLocalizedStringResource:", ""),
                ("LNPerformActionErrorCode.localizedStringResource:", ""),
                ("VPN Connection Error:", "VPN 連線錯誤："),
                ("No utun interface detected — LocalDevVPN is not connected", "未偵測到 utun 介面 — LocalDevVPN 尚未連線"),
                ("Please make sure LocalDevVPN is connected and running properly.", "請確認 LocalDevVPN 已連線並正常執行。"),
                ("Open LiveContainer and enable LocalDevVPN to continue refresh.", "請開啟 LiveContainer 並啟用 LocalDevVPN，再繼續重新整理。"),
                ("LocalDevVPN activation did not return. Enable LocalDevVPN and retry refresh.", "LocalDevVPN 啟用後未返回。請啟用 LocalDevVPN 後重試重新整理。"),
                ("Wi-Fi is unavailable. Connect to Wi-Fi before refreshing.", "Wi-Fi 無法使用。請先連線 Wi-Fi，再重新整理。"),
                ("Wi-Fi was lost while enabling LocalDevVPN. Reconnect and retry.", "啟用 LocalDevVPN 時 Wi-Fi 已中斷。請重新連線後重試。"),
            ]
            for source, target in runtime_replacements:
                text = text.replace(source, target)

            if text != old:
                path.write_text(text, encoding="utf-8")
                changed_files += 1
                print(f"localized: {path}")

    print(f"Post-integration zh-TW localization: PASS ({changed_files} files changed)")

if __name__ == "__main__":
    main()
