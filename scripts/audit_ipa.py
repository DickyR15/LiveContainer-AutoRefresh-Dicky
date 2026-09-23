#!/usr/bin/env python3
from __future__ import annotations
import argparse, plistlib, struct, zipfile
from pathlib import Path

def macho(z,p):
    b=z.read(p)
    assert b[:4]==b"\xcf\xfa\xed\xfe",f"{p}: expected arm64 Mach-O"
    return b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("ipa",type=Path); a=ap.parse_args()
    with zipfile.ZipFile(a.ipa) as z:
        names=set(z.namelist()); base="Payload/LiveContainer.app/"
        required=[
          base+"Info.plist",
          base+"Frameworks/SideStoreSupport.framework/SideStoreSupport",
          base+"Frameworks/SideStoreApp.framework/Info.plist",
          base+"Frameworks/SideStoreApp.framework/SideStore",
          base+"Frameworks/SideStoreApp.framework/LCAppInfo.plist",
          base+"PlugIns/LiveProcess.appex/LiveProcess",
          base+"PlugIns/ShareExtension.appex/ShareExtension",
          base+"PlugIns/LaunchAppExtension.appex/LaunchAppExtension",
          base+"PlugIns/LiveWidgetExtension.appex/LiveWidgetExtension"]
        for p in required: assert p in names,f"missing {p}"
        h=plistlib.loads(z.read(base+"Info.plist"))
        assert h["CFBundleShortVersionString"]=="3.8.10"
        assert h["CFBundleVersion"]=="3.8.10"
        assert h["ALTAppGroups"]==["group.com.SideStore.SideStore"]
        schemes={s for d in h["CFBundleURLTypes"] for s in d["CFBundleURLSchemes"]}
        assert {"livecontainer","sidestore","sidestore-com.kdt.livecontainer"}<=schemes
        assert {"RefreshAllIntent","ViewAppIntent"}<=set(h["INIntentsSupported"])
        assert "processing" in h.get("UIBackgroundModes",[])
        side=plistlib.loads(z.read(base+"Frameworks/SideStoreApp.framework/Info.plist"))
        assert side["CFBundleIdentifier"]=="com.SideStore.SideStore"
        sb=macho(z,base+"Frameworks/SideStoreApp.framework/SideStore")
        assert struct.unpack_from("<I",sb,12)[0]==6
        assert b"[SIDESTORE_COREDEVICE]" in sb
        assert b"[SELF_REFRESH]" in sb
        support=macho(z,base+"Frameworks/SideStoreSupport.framework/SideStoreSupport")
        assert b"EMBEDDED_SIDESTORE_STARTUP_FIX_V1" in support
        host=macho(z,base+"Frameworks/LiveContainerSwiftUI.framework/LiveContainerSwiftUI")
        assert b"liveContainerAutoRefresh" in host
        meta=z.read(base+"Metadata.appintents/extract.actionsdata")
        assert b"16SideStoreSupport20RefreshAllAppsIntentV" in meta
        assert b"16SideStoreSupport26RefreshAllAppsWidgetIntentV" in meta
        assert b"9SideStore20RefreshAllAppsIntentV" not in meta
        banned=("pairingFile.plist","pairing_file","private_key","RootPrivateKey","HostPrivateKey")
        for n in names: assert not any(x.lower() in n.lower() for x in banned),f"personal material path: {n}"
    print("FINAL STATIC AUDIT: PASS")
if __name__=="__main__": main()
