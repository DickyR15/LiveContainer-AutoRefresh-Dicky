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

# Keep the proven upstream AlarmKit implementation untouched. Only patch the
# VPN readiness race and the user-facing notification control.
replace_once(
    "livecontainer_network_preflight.swift",
    '''        guard hasTunnelInterface() else {
            if !allowForegroundActivation { print("[AUTO_REFRESH] VPN_UNAVAILABLE_BACKGROUND") }
            print("[AUTO_REFRESH] LOCALDEVVPN_VERIFY_FAIL reason=no_utun_interface")
            throw failure(2, "Open LiveContainer and enable LocalDevVPN to continue refresh.")
        }''',
    '''        var tunnelReady = hasTunnelInterface()
        if !tunnelReady {
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
    }''',
    "notification permission status"
)

replace_once(
    "livecontainer_refresh_settings.swift",
    "import SwiftUI\nimport Foundation",
    "import SwiftUI\nimport Foundation\nimport UIKit\nimport UserNotifications",
    "refresh settings notification imports"
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
    '''            Section("Warnings") {
                Button("Allow refresh notifications") {
                    Task { @MainActor in
                        let status = await LiveContainerAutoRefreshScheduler.notificationAuthorizationStatus()
                        if status == .denied {
                            if let url = URL(string: UIApplication.openNotificationSettingsURLString) {
                                _ = await UIApplication.shared.open(url)
                            }
                        } else {
                            await LiveContainerAutoRefreshScheduler.requestNotificationPermission()
                            LiveContainerAutoRefreshScheduler.schedule()
                        }
                    }
                }
                if #available(iOS 26.1, *) {
                    Button("Enable optional deadline alarm") {
                        Task { @MainActor in
                            await LiveContainerAutoRefreshAlarmProvider.requestAuthorization()
                            LiveContainerAutoRefreshScheduler.schedule()
                        }
                    }
                }
                Text("Warnings require permission. A deadline warning asks you to check an unconfirmed refresh; it cannot diagnose a task that never ran.")
                    .font(.caption).foregroundColor(.secondary)
            }''',
    "functional warning controls"
)

print("AutoRefresh behavior fixes: PASS")
