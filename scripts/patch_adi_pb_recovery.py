#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_ADI_PB_AUTO_RECOVERY_IOS27_V1"

def fail(message: str) -> None:
    raise SystemExit("patch_adi_pb_recovery: " + message)

def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_adi_pb_recovery.py <sidestore-root>")

    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Anisette/AnisetteProvider.swift"
    if not path.exists():
        fail(f"missing AnisetteProvider.swift: {path}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("ADI pb automatic recovery V1: already patched")
        return

    old = """    static func fetch(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        if UserDefaults.standard.useOnDeviceAnisette {
            debugLog("[AnisetteProvider] Fetching anisette via On-Device Anisette (ODA)...")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        } else {
            debugLog("[AnisetteProvider] Fetching anisette via remote server...")
            return try await fetchRemote(handler: handler)
        }
    }
"""

    if text.count(old) != 1:
        fail(f"expected exactly one original fetch() body, found {text.count(old)}")

    new = """    // DPORT_ADI_PB_AUTO_RECOVERY_IOS27_V1
    // iOS 27 may return ADIOTPRequest failed / Device not provisioned (-45061)
    // when the cached adi.pb is stale. Mirror SideStore's manual Reset adi.pb
    // action automatically once, without touching Apple ID or certificates.
    static func fetch(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        do {
            return try await fetchOnce(handler: handler)
        } catch {
            guard isAdiNotProvisionedError(error) else {
                throw error
            }

            debugLog("[AnisetteProvider] ADI -45061 detected. Clearing cached adi.pb and retrying provisioning once.")

            AnisetteConfigManager.shared.anisetteAdiBlob = nil
            SideSign.AnisetteDataManager.shared.clearCache()

            return try await fetchOnce(handler: handler)
        }
    }

    private static func fetchOnce(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        if UserDefaults.standard.useOnDeviceAnisette {
            debugLog("[AnisetteProvider] Fetching anisette via On-Device Anisette (ODA)...")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        } else {
            debugLog("[AnisetteProvider] Fetching anisette via remote server...")
            return try await fetchRemote(handler: handler)
        }
    }

    private static func isAdiNotProvisionedError(_ error: Error) -> Bool {
        let nsError = error as NSError
        let message = ([String(describing: error), nsError.localizedDescription]
            .joined(separator: " ")
            .lowercased())

        return nsError.code == -45061
            || message.contains("-45061")
            || message.contains("device not provisioned")
            || message.contains("adiotprequest failed")
    }
"""

    text = text.replace(old, new, 1)

    for required in (
        MARKER,
        "fetchOnce(handler: handler)",
        "isAdiNotProvisionedError",
        "anisetteAdiBlob = nil",
        "SideSign.AnisetteDataManager.shared.clearCache()",
    ):
        if required not in text:
            fail("verification missing: " + required)

    path.write_text(text, encoding="utf-8")
    print("ADI pb automatic recovery V1: PASS")

if __name__ == "__main__":
    main()
