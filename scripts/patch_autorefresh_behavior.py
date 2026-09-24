#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "templates"

def patch_ios27_intent_runner(root: Path) -> None:
    """Open SideStore before the iOS 27 automatic refresh action."""
    path = root / "SideStoreSupport/PrivateIntentRunner.m"
    if not path.exists():
        raise SystemExit(f"missing PrivateIntentRunner source: {path}")
    text = path.read_text(encoding="utf-8")
    if "IOS27_OPEN_APP_BEFORE_REFRESH" in text:
        return

    old = '''    LNAction* action = [[actionClass alloc] initWithIdentifier:identifier
                                                    mangledTypeName:mangledTypeName
                                                      openAppWhenRun:NO
                                                         parameters:@[]];
'''
    new = '''    BOOL openAppBeforeRefresh = NO;
    if (@available(iOS 27.0, *)) {
        // iOS 27: initialize SideStore before Refresh All Apps.
        // This mirrors the known-good sidestore:// -> refresh sequence.
        openAppBeforeRefresh = YES; // IOS27_OPEN_APP_BEFORE_REFRESH
    }

    LNAction* action = [[actionClass alloc] initWithIdentifier:identifier
                                                    mangledTypeName:mangledTypeName
                                                      openAppWhenRun:openAppBeforeRefresh
                                                         parameters:@[]];
'''
    if text.count(old) != 1:
        raise SystemExit(f"iOS27 open-app patch: expected one anchor, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in ("IOS27_OPEN_APP_BEFORE_REFRESH", "openAppWhenRun:openAppBeforeRefresh", "openAppBeforeRefresh = YES"):
        if required not in verify:
            raise SystemExit("iOS27 open-app verification failed: " + required)


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

# The localization step runs before this script in the CI pipeline, so the
# notification section may already be in its zh-TW form. Accept either form.
_settings_path = T / "livecontainer_refresh_settings.swift"
_settings_text = _settings_path.read_text(encoding="utf-8")
_upstream_warning = '''            Section("Warnings") {
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
            }'''
_localized_warning = '''            Section("Warnings") {
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
            }'''
if _localized_warning not in _settings_text:
    if _upstream_warning not in _settings_text:
        raise SystemExit("functional warning controls: neither upstream nor localized block found")
    _settings_text = _settings_text.replace(_upstream_warning, _localized_warning, 1)
    _settings_path.write_text(_settings_text, encoding="utf-8")
    print("patched: functional warning controls")
else:
    print("already patched: functional warning controls")

# Apply the iOS 27 executor change to the actual LiveContainer checkout.
if len(__import__("sys").argv) == 2:
    patch_ios27_intent_runner(Path(__import__("sys").argv[1]).resolve())
    print("patched: iOS 27 private intent executor")


print("AutoRefresh behavior fixes: PASS")
