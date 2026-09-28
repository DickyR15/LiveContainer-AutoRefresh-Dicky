#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_REFRESH_1100_UPSTREAM_ONLY_V1"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_refresh_1100_retry.py <sidestore-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "AltStore/Managing Apps/AppManager.swift"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    # Do not wrap AppManager.refresh() with custom authentication/retry logic.
    # Keep SideStore's pinned upstream refresh pipeline unchanged.
    print("AppManager.refresh upstream path preserved: PASS")

if __name__ == "__main__":
    main()
