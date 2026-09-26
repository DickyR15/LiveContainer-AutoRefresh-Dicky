#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "IOS27_DIRECT_REFRESH_INTENT_V2_REVERTED"

def fail(message: str) -> None:
    raise SystemExit("patch_ios27_refresh_execution: " + message)

def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: patch_ios27_refresh_execution.py <livecontainer-root>")

    root = Path(sys.argv[1]).resolve()
    path = root / "SideStoreSupport/SideStoreClient.swift"
    if not path.exists():
        fail(f"missing SideStoreClient.swift: {path}")

    text = path.read_text(encoding="utf-8")

    # IMPORTANT: Do not call RefreshAllAppsIntent.perform() directly on iOS 27.
    # That bypasses the AppIntents execution context. RefreshAllAppsIntent uses
    # ForegroundContinuableIntent and may need requestToContinueInForeground();
    # invoking perform() directly can surface AppIntents.AppIntentError(code: 1).
    # Keep the upstream PrivateIntentRunner path, which supplies the proper
    # AppIntent execution context.
    if "PrivateIntentRunner.run(" not in text:
        fail("upstream PrivateIntentRunner path is missing")

    if "callRefreshIntent(mangledTypeName: mangledTypeName)" in text and "if #available(iOS 27.0, *)" in text:
        fail("obsolete direct perform() iOS 27 workaround is present")

    if MARKER in text:
        print("iOS 27 refresh execution: upstream AppIntent runner preserved")
        return

    # No source rewrite is required. Add a harmless audit marker so CI can
    # verify that this stage intentionally preserves the upstream execution
    # path rather than applying the broken direct-perform workaround.
    path.write_text(
        "// " + MARKER + " — preserve PrivateIntentRunner AppIntent context\n" + text,
        encoding="utf-8",
    )

    verify = path.read_text(encoding="utf-8")
    for required in (MARKER, "PrivateIntentRunner.run("):
        if required not in verify:
            fail("verification missing: " + required)

    print("iOS 27 refresh execution: upstream PrivateIntentRunner preserved")

if __name__ == "__main__":
    main()
