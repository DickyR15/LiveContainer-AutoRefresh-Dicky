#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_IOS27_ODA_FIRST_V2_REVERTED"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_ios27_oda_first.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Anisette/AnisetteProvider.swift"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("iOS 27 ODA-first: reverted/preserved upstream Anisette selection")
        return

    # IMPORTANT:
    # Recent iOS 27 SideStore reports show that forcing On-Device Anisette
    # can produce ADI -45061 during Shortcut/automatic refresh. Keep the
    # upstream user-controlled selection instead. In particular, do not
    # force ODA on iOS 27.
    start = text.find("enum AnisetteProvider {")
    if start < 0:
        raise SystemExit("AnisetteProvider enum anchor not found")
    fetch_start = text.find("    static func fetch(handler:", start)
    if fetch_start < 0:
        raise SystemExit("AnisetteProvider.fetch anchor not found")
    body_start = text.find("{", fetch_start)
    if body_start < 0:
        raise SystemExit("AnisetteProvider.fetch body start not found")
    depth = 0
    end = None
    for i in range(body_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit("AnisetteProvider.fetch body end not found")

    original = '''    static func fetch(handler: AnisetteServerHandler? = nil) async throws -> ALTAnisetteData {
        if UserDefaults.standard.useOnDeviceAnisette {
            debugLog("[AnisetteProvider] Fetching anisette via On-Device Anisette (ODA)...")
            return try await OnDeviceAnisetteManager.shared.fetchAnisetteData()
        } else {
            debugLog("[AnisetteProvider] Fetching anisette via remote server...")
            return try await fetchRemote(handler: handler)
        }
    }'''
    actual = text[fetch_start:end].strip()
    if "useOnDeviceAnisette" not in actual and "fetchRemote(handler: handler)" not in actual:
        raise SystemExit("unexpected AnisetteProvider.fetch implementation; refusing blind rewrite")

    text = text[:fetch_start] + original + "\n\n    // " + MARKER + "\n" + text[end:]
    path.write_text(text, encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    for required in (MARKER, "useOnDeviceAnisette", "fetchRemote(handler: handler)"):
        if required not in verify:
            raise SystemExit("verification failed: " + required)
    if "if #available(iOS 27.0, *)" in verify and "OnDeviceAnisetteManager.shared.fetchAnisetteData()" in verify:
        # ODA is still allowed by the user's setting, but there must not be a
        # forced iOS 27 branch.
        forced = verify[verify.find("static func fetch"):verify.find("private static func fetchRemote")]
        if "#available(iOS 27.0, *)" in forced:
            raise SystemExit("forced iOS 27 ODA branch still present")
    print("iOS 27 ODA-first: reverted; upstream user-controlled Anisette selection preserved")

if __name__ == "__main__":
    main()
