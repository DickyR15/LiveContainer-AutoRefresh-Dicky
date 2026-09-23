#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "templates"

def replace_once(path, old, new, label):
    p = T / path
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, got {n} in {path}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched:", label)

# 1) LocalDevVPN: after returning from the LocalDevVPN app, allow the utun
# interface a short bounded window to appear. The previous build checked once
# immediately and could race the VPN connection.
replace_once(
    "livecontainer_network_preflight.swift",
    '''        guard hasTunnelInterface() else {
            if !allowForegroundActivation { print("[AUTO_REFRESH] VPN_UNAVAILABLE_BACKGROUND") }
            print("[AUTO_REFRESH] LOCALDEVVPN_VERIFY_FAIL reason=no_utun_interface")
            throw failure(2, "Open LiveContainer and enable LocalDevVPN to continue refresh.")
        }''',
    '''        var tunnelReady = hasTunnelInterface()
        if !tunnelReady {
            // LocalDevVPN can return control before its utun interface is fully
            // published. Wait once, bounded, instead of declaring failure on a race.
            for _ in 0..<40 {
                try Task.checkCancellation()
                try await Task.sleep(nanoseconds: 500_000_000)
                if hasTunnelInterface() {
                    tunnelReady = true
                    break
                }
            }
        }
        guard tunnelReady else {
            if !allowForegroundActivation { print("[AUTO_REFRESH] VPN_UNAVAILABLE_BACKGROUND") }
            print("[AUTO_REFRESH] LOCALDEVVPN_VERIFY_FAIL reason=no_utun_interface_after_wait")
            throw failure(2, allowForegroundActivation
                ? "LocalDevVPN 未連線。請確認 LocalDevVPN 已啟用，然後再試一次。"
                : "背景重新整理無法啟用 LocalDevVPN。請在執行排程前保持 LocalDevVPN 已連線。")
        }''',
    "bounded LocalDevVPN readiness wait"
)

# 2) Notifications: when permission was already denied, requestAuthorization()
# intentionally shows no prompt. Make the UI open the correct iOS notification
# settings instead of appearing to do nothing.
replace_once(
    "livecontainer_refresh_scheduler.swift",
    '''    static func requestNotificationPermission() async {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        guard settings.authorizationStatus == .notDetermined else { return }
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound])
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION granted=\\(granted)")
        } catch {
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION_FAIL error=\\(error.localizedDescription)")
        }
    }''',
    '''    static func requestNotificationPermission() async {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        if settings.authorizationStatus == .denied {
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION_DENIED action=open_settings")
            return
        }
        guard settings.authorizationStatus == .notDetermined else {
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION_ALREADY_AUTHORIZED")
            return
        }
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION granted=\\(granted)")
        } catch {
            print("[LIVE_CONTAINER_REFRESH] NOTIFICATION_PERMISSION_FAIL error=\\(error.localizedDescription)")
        }
    }

    static func notificationAuthorizationStatus() async -> UNAuthorizationStatus {
        await UNUserNotificationCenter.current().notificationSettings().authorizationStatus
    }

    static func openNotificationSettings() async {
        guard let url = URL(string: UIApplication.openNotificationSettingsURLString) else { return }
        _ = await UIApplication.shared.open(url)
    }''',
    "notification permission status/settings helpers"
)

# 3) AlarmKit: surface denied authorization and send the user to Settings.
replace_once(
    "livecontainer_refresh_alarm.swift",
    '''import Foundation
import UserNotifications''',
    '''import Foundation
import UserNotifications
import UIKit''',
    "AlarmKit UIKit import"
)
replace_once(
    "livecontainer_refresh_alarm.swift",
    '''    static func requestAuthorization() async {
        do { _ = try await AlarmManager.shared.requestAuthorization() }
        catch { print("[LIVE_CONTAINER_REFRESH] ALARM_AUTHORIZATION_FAIL error=\\(error.localizedDescription)") }
        LiveContainerAutoRefreshScheduler.schedule()
    }''',
    '''    static func requestAuthorization() async {
        do {
            let state = try await AlarmManager.shared.requestAuthorization()
            print("[LIVE_CONTAINER_REFRESH] ALARM_AUTHORIZATION state=\\(String(describing: state))")
            if state == .denied {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    _ = await UIApplication.shared.open(url)
                }
            }
        } catch {
            print("[LIVE_CONTAINER_REFRESH] ALARM_AUTHORIZATION_FAIL error=\\(error.localizedDescription)")
        }
        // Always reschedule so the normal local-notification deadline fallback
        // remains active even when AlarmKit is unavailable or denied.
        LiveContainerAutoRefreshScheduler.schedule()
    }''',
    "AlarmKit denied-state handling"
)

# 4) Refresh settings: replace silent buttons with status-aware actions and a
# visible current notification/alarm state. This is intentionally UI-only.
replace_once(
    "livecontainer_refresh_settings.swift",
    "import SwiftUI\nimport Foundation",
    "import SwiftUI\nimport Foundation\nimport UIKit\nimport UserNotifications",
    "refresh settings notification imports"
)
# AlarmKit is only available on iOS 26.1+; keep the generated settings view parseable on older SDK paths.
p=T/"livecontainer_refresh_settings.swift"
s=p.read_text(encoding="utf-8")
if "import AlarmKit" not in s:
    s=s.replace("import UserNotifications\n", "import UserNotifications\n#if canImport(AlarmKit)\nimport AlarmKit\n#endif\n", 1)
p.write_text(s, encoding="utf-8")
replace_once(
    "livecontainer_refresh_settings.swift",
    '''    @State private var showClearHistoryConfirmation = false
    @AppStorage''',
    '''    @State private var showClearHistoryConfirmation = false
    @State private var notificationStatus = "檢查中"
    @State private var alarmStatus = "檢查中"
    @AppStorage''',
    "refresh settings permission state"
)
replace_once(
    "livecontainer_refresh_settings.swift",
    '''            Section("Warnings") {
                Button("Allow refresh notifications") {
                    Task { @MainActor in await LiveContainerAutoRefreshScheduler.requestNotificationPermission(); LiveContainerAutoRefreshScheduler.schedule() }
                }
                if #available(iOS 26.1, *) {
                    Button("Enable optional deadline alarm") {
                        Task { @MainActor in await LiveContainerAutoRefreshAlarmProvider.requestAuthorization() }
                    }
                }
                Text("Warnings require permission. A deadline warning asks you to check an unconfirmed refresh; it cannot diagnose a task that never ran.")
                    .font(.caption).foregroundColor(.secondary)
            }''',
    '''            Section("警告") {
                Button("允許重新整理通知") {
                    Task { @MainActor in
                        let status = await LiveContainerAutoRefreshScheduler.notificationAuthorizationStatus()
                        if status == .denied {
                            await LiveContainerAutoRefreshScheduler.openNotificationSettings()
                        } else {
                            await LiveContainerAutoRefreshScheduler.requestNotificationPermission()
                            LiveContainerAutoRefreshScheduler.schedule()
                        }
                        await refreshPermissionStatus()
                    }
                }
                Text("通知狀態：\\(notificationStatus)")
                    .font(.caption).foregroundColor(.secondary)
                if #available(iOS 26.1, *) {
                    Button("啟用期限提醒") {
                        Task { @MainActor in
                            await LiveContainerAutoRefreshAlarmProvider.requestAuthorization()
                            LiveContainerAutoRefreshScheduler.schedule()
                            await refreshPermissionStatus()
                        }
                    }
                    Text("期限提醒：\\(alarmStatus)")
                        .font(.caption).foregroundColor(.secondary)
                }
                Text("期限提醒會在尚未確認重新整理成功時提醒你；它不會取代自動重新整理。")
                    .font(.caption).foregroundColor(.secondary)
            }''',
    "refresh warning controls"
)
replace_once(
    "livecontainer_refresh_settings.swift",
    '''        .navigationTitle("SideStore refresh")
        .onAppear { reloadHistory() }''',
    '''        .navigationTitle("SideStore 重新整理")
        .onAppear {
            reloadHistory()
            Task { @MainActor in await refreshPermissionStatus() }
        }''',
    "refresh settings title/status refresh"
)
replace_once(
    "livecontainer_refresh_settings.swift",
    '''    private func reloadHistory() {
        history = LiveContainerRefreshHistoryStore.entries(in: defaults)''',
    '''    private func refreshPermissionStatus() async {
        let status = await LiveContainerAutoRefreshScheduler.notificationAuthorizationStatus()
        switch status {
        case .authorized: notificationStatus = "已允許"
        case .provisional: notificationStatus = "暫時允許"
        case .denied: notificationStatus = "已拒絕（點擊按鈕可前往設定）"
        case .notDetermined: notificationStatus = "尚未設定"
        @unknown default: notificationStatus = "未知"
        }
        if #available(iOS 26.1, *) {
            let alarm = AlarmManager.shared.authorizationState
            switch alarm {
            case .authorized: alarmStatus = "已允許"
            case .denied: alarmStatus = "已拒絕（可至設定開啟）"
            case .notDetermined: alarmStatus = "尚未設定"
            @unknown default: alarmStatus = "未知"
            }
        }
    }

    private func reloadHistory() {
        history = LiveContainerRefreshHistoryStore.entries(in: defaults)''',
    "permission status updater"
)

# 5) Final remaining UI strings.
p=T/"livecontainer_refresh_settings.swift"
s=p.read_text(encoding="utf-8")
for a,b in {
    '"Standard"':'"標準"',
    '"Limited"':'"有限制"',
    '"Unknown"':'"未知"',
    '"REFRESH_FAILED"':'"重新整理失敗"',
    '"Refresh Failed"':'"重新整理失敗"',
    '"Scheduled refresh"':'"排程重新整理"',
    '"Frequency"':'"頻率"',
    '"Target time (local)"':'"目標時間（當地時間）"',
}.items():
    s=s.replace(a,b)
p.write_text(s,encoding="utf-8")

# Also translate the v3 Settings navigation label and notification prompt.
p=T/"v3_unified_shell.swift"
s=p.read_text(encoding="utf-8")
for a,b in {
    'Text("SideStore scheduled refresh")':'Text("SideStore 排程重新整理")',
    'Button("Allow Notifications")':'Button("允許通知")',
    'Button("Later", role: .cancel)':'Button("稍後", role: .cancel)',
    'Text("Stay Informed About Refreshes")':'Text("重新整理通知")',
    'Text("LiveContainer can notify you when a refresh starts, completes, or needs attention. Nothing runs differently if you skip this.")':'Text("重新整理開始、完成或需要注意時，LiveContainer 可以通知你。略過此設定不會影響重新整理功能。")',
}.items():
    s=s.replace(a,b)
p.write_text(s,encoding="utf-8")

print("AutoRefresh behavior fixes: PASS")
