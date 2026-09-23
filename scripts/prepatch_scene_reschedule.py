#!/usr/bin/env python3
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepatch_scene_reschedule.py SIDESTORE_ROOT")
    root=Path(sys.argv[1])
    p=root/"AltStore/SceneDelegate.swift"
    s=p.read_text(encoding="utf-8")
    marker="(UIApplication.shared.delegate as? AppDelegate)?.scheduleAutomaticRefresh()"
    if marker in s:
        print("SceneDelegate reschedule: already present")
        return
    needle='        // Make sure to update AppDelegate.applicationDidEnterBackground() as well.\n'
    if needle not in s:
        raise SystemExit("SceneDelegate: stable background anchor not found")
    replacement=needle+"        (UIApplication.shared.delegate as? AppDelegate)?.scheduleAutomaticRefresh()\n\n"
    s=s.replace(needle,replacement,1)
    p.write_text(s,encoding="utf-8")
    print("SceneDelegate reschedule: applied")

if __name__=="__main__":
    main()
