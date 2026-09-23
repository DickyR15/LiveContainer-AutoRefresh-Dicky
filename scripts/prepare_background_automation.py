#!/usr/bin/env python3
from pathlib import Path

SCRIPT=Path("builder/patch_background_automation.py")

OLD='''    text = replace_once(
        text,
        \'\'\'    func applicationDidEnterBackground(_ application: UIApplication)
    {
        // Make sure to update SceneDelegate.sceneDidEnterBackground() as well.
\'\'\',
        \'\'\'    func applicationDidEnterBackground(_ application: UIApplication)
    {
        self.scheduleAutomaticRefresh()
        // Make sure to update SceneDelegate.sceneDidEnterBackground() as well.
\'\'\',
        "application background reschedule",
    )
'''

NEW='''    method_marker = "func applicationDidEnterBackground"
    if method_marker not in text:
        die("application background reschedule: method not found")
    method_start = text.index(method_marker)
    body_start = text.index("{", method_start) + 1
    next_method = text.find("func applicationWillEnterForeground", body_start)
    if next_method < 0:
        next_method = len(text)
    body = text[body_start:next_method]
    if "scheduleAutomaticRefresh()" not in body:
        text = text[:body_start] + "\\n        self.scheduleAutomaticRefresh()\\n" + text[body_start:]
'''

def main():
    s=SCRIPT.read_text(encoding="utf-8")
    if NEW in s:
        print("background automation compatibility shim already installed")
        return
    if OLD not in s:
        # Find the unique diagnostic label and replace its complete replace_once call.
        label='        "application background reschedule",'
        end=s.find(label)
        if end<0:
            raise SystemExit("background automation compatibility: label not found")
        start=s.rfind("    text = replace_once(",0,end)
        close=s.find("\n    )",end)
        if start<0 or close<0:
            raise SystemExit("background automation compatibility: call bounds not found")
        close += len("\n    )")
        s=s[:start]+NEW+s[close:]
    else:
        s=s.replace(OLD,NEW,1)
    SCRIPT.write_text(s,encoding="utf-8")
    print("background automation compatibility shim installed")

if __name__=="__main__":
    main()
