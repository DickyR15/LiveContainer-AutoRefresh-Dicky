#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("ipa", type=Path)
    a=ap.parse_args()
    with zipfile.ZipFile(a.ipa) as z:
        names=set(z.namelist())
        host="Payload/LiveContainer.app/Frameworks/LiveContainerSwiftUI.framework/LiveContainerSwiftUI"
        assert host in names, "missing compiled LiveContainerSwiftUI framework"
        assert "Payload/LiveContainer.app/Frameworks/SideStoreApp.framework/SideStore" in names, "missing embedded SideStore"
        data=z.read(host)
        markers=[
            "localizedRefreshError",
            "localizedRefreshHistoryValue",
            "VPN 連線錯誤：",
            "未偵測到 utun 介面",
            "請確認 LocalDevVPN 已連線並正常執行。",
        ]
        for marker in markers:
            assert marker.encode("utf-8") in data, f"compiled host missing localization marker: {marker}"
    print("IPA localization/package audit: PASS")

if __name__=="__main__":
    main()
