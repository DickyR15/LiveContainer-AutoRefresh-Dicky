#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_ODA_FIRST_V1"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_ios27_oda_first.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Anisette/AnisetteProvider.swift"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("iOS 27 ODA-first: already patched")
        return

    old = '''enum AnisetteProvider {
    static func fetch(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        if UserDefaults.standard.useOnDeviceAnisette {
            debugLog("[AnisetteProvider] Fetching anisette via On-Device Anisette (ODA)...")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        } else {
            debugLog("[AnisetteProvider] Fetching anisette via remote server...")
            return try await fetchRemote(handler: handler)
        }
    }
'''
    new = '''enum AnisetteProvider {
    static func fetch(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        // DPORT_IOS27_ODA_FIRST_V1
        // Apple authentication on iOS 27 is sensitive to the device-local ADI/
        // Anisette state. Prefer ODA on iOS 27 even when the legacy UI toggle
        // is off; retain the toggle behavior on older iOS versions.
        if #available(iOS 27.0, *) {
            debugLog("[AnisetteProvider] iOS 27+: using On-Device Anisette (ODA) for Apple authentication.")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        }

        if UserDefaults.standard.useOnDeviceAnisette {
            debugLog("[AnisetteProvider] Fetching anisette via On-Device Anisette (ODA)...")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        } else {
            debugLog("[AnisetteProvider] Fetching anisette via remote server...")
            return try await fetchRemote(handler: handler)
        }
    }
'''
    if old not in text:
        raise SystemExit("expected AnisetteProvider.fetch anchor not found")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (MARKER, "iOS 27+: using On-Device Anisette", "OnDeviceAnisetteManager.shared.fetchAnisetteData()"):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    print("iOS 27 ODA-first: PASS")

if __name__ == "__main__":
    main()
