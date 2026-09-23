#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil, subprocess, tempfile, zipfile
from pathlib import Path

def run(*args, cwd=None):
    subprocess.run(list(args), cwd=cwd, check=True)

def pb(path, cmd):
    run("/usr/libexec/PlistBuddy","-c",cmd,str(path))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--host",type=Path,required=True)
    ap.add_argument("--side",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    a.output=a.output.resolve()
    root=a.source.resolve()
    payload=root/"Payload"
    if payload.exists(): raise SystemExit("fresh packaging workspace required")
    payload.mkdir()

    app=payload/"LiveContainer.app"
    shutil.copytree(a.host,app,symlinks=True)

    framework=app/"Frameworks"/"SideStoreApp.framework"
    if framework.exists(): shutil.rmtree(framework)
    shutil.copytree(a.side,framework,symlinks=True)

    dylibify=root/"dylibify"
    run("curl","-fsSL","https://github.com/LiveContainer/dylibify/releases/download/1.0/dylibify","-o",str(dylibify))
    run("chmod","+x",str(dylibify))
    exe=framework/"SideStore"
    out=framework/"SideStore.dylib"
    run(str(dylibify),str(exe),str(out))
    exe.unlink(); out.rename(exe)
    run("ldid","-S",str(exe))
    shutil.copy2(root/".github/sidelc/LCAppInfo.plist",framework/"LCAppInfo.plist")

    for n in ("Intents.intentdefinition","ViewApp.intentdefinition"):
        if (framework/n).exists(): shutil.copy2(framework/n,app/n)
    md=framework/"Metadata.appintents"
    if md.exists():
        dst=app/"Metadata.appintents"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(md,dst)
        f=dst/"extract.actionsdata"
        if f.exists():
            t=f.read_text()
            t=t.replace("9SideStore20RefreshAllAppsIntentV","16SideStoreSupport20RefreshAllAppsIntentV")
            t=t.replace("9SideStore26RefreshAllAppsWidgetIntentV","16SideStoreSupport26RefreshAllAppsWidgetIntentV")
            f.write_text(t)

    widget=framework/"PlugIns"/"AltWidgetExtension.appex"
    dst=app/"PlugIns"/"LiveWidgetExtension.appex"
    if widget.exists():
        if dst.exists(): shutil.rmtree(dst)
        widget.rename(dst)
        pb(dst/"Info.plist","Set :CFBundleIdentifier com.kdt.livecontainer.LiveWidget")
        pb(dst/"Info.plist","Set :CFBundleExecutable LiveWidgetExtension")
        (dst/"AltWidgetExtension").rename(dst/"LiveWidgetExtension")
        run("ldid","-S"+str(root/".github/sidelc/LiveWidgetExtension_adhoc.xml"),str(dst/"LiveWidgetExtension"))

    hi=app/"Info.plist"
    cmds=[
        "Add :ALTAppGroups array",
        "Add :ALTAppGroups: string group.com.SideStore.SideStore",
        "Add :CFBundleURLTypes:1 dict",
        "Add :CFBundleURLTypes:1:CFBundleURLName string com.kdt.livecontainer.sidestoreurlscheme",
        "Add :CFBundleURLTypes:1:CFBundleURLSchemes array",
        "Add :CFBundleURLTypes:1:CFBundleURLSchemes:0 string sidestore",
        "Add :CFBundleURLTypes:2 dict",
        "Add :CFBundleURLTypes:2:CFBundleURLName string com.kdt.livecontainer.sidestorebackupurlscheme",
        "Add :CFBundleURLTypes:2:CFBundleURLSchemes array",
        "Add :CFBundleURLTypes:2:CFBundleURLSchemes:0 string sidestore-com.kdt.livecontainer",
        "Add :INIntentsSupported array",
        "Add :INIntentsSupported:0 string RefreshAllIntent",
        "Add :INIntentsSupported:1 string ViewAppIntent",
        "Add :NSUserActivityTypes array",
        "Add :NSUserActivityTypes:0 string RefreshAllIntent",
        "Add :NSUserActivityTypes:1 string ViewAppIntent",
    ]
    for c in cmds: pb(hi,c)

    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        stage=Path(td)
        shutil.copytree(payload,stage/"Payload",symlinks=True)
        run("zip","-qry",str(a.output),"Payload",cwd=stage)

if __name__=="__main__":
    main()
