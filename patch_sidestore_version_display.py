#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "DPORT_SIDESTORE_COMMIT_DISPLAY_V1"
COMMIT = "0dd743f7"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_sidestore_version_display.py <livecontainer-root>")
    root = Path(sys.argv[1]).resolve()
    path = root / "SideStoreSupport/SideStoreHooks.m"
    if not path.exists():
        raise SystemExit(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("SideStore commit display: already patched")
        return
    old = '''    NSString* SSVersion = [NSBundle.mainBundle objectForInfoDictionaryKey:@"CFBundleShortVersionString"];
    
    NSString *osVersion'''
    new = '''    NSString* SSVersion = [NSBundle.mainBundle objectForInfoDictionaryKey:@"CFBundleShortVersionString"];
    // DPORT_SIDESTORE_COMMIT_DISPLAY_V1: show the exact embedded SideStore source commit.
    SSVersion = [NSString stringWithFormat:@"%@ (%@)", SSVersion, @"0dd743f7"];
    
    NSString *osVersion'''
    if text.count(old) != 1:
        raise SystemExit(f"expected one SideStore version anchor, found {text.count(old)}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")
    print("SideStore commit display: PASS")

if __name__ == "__main__":
    main()
