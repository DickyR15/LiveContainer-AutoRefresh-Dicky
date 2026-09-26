#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_AUTH_SESSION_RECOVERY_UPSTREAM_ONLY_V1"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_auth_session_recovery.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "SideStore/Core/Auth/AuthManager.swift"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    # Deliberately preserve the pinned SideStore AuthManager implementation.
    # Custom session/Anisette recovery was removed because it altered the
    # official refresh authentication path and could itself trigger 1100.
    if "DPORT_AUTH_SESSION_RECOVERY_IOS27_V5" in text or "DPORT_AUTH_SESSION_RECOVERY_IOS27_V4" in text:
        raise SystemExit("stale custom AuthManager patch marker would require a clean SideStore checkout")
    print("AuthManager upstream path preserved: PASS")

if __name__ == "__main__":
    main()
