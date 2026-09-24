#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = "IOS27_DIRECT_REFRESH_INTENT"

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
    if MARKER in text:
        print("iOS 27 direct refresh execution: already patched")
        return

    start = text.find("    // call this when no IntentContext exists (when sidestore is loaded in LiveProcess)")
    if start < 0:
        fail("callRefreshIntent2 anchor not found")

    end = text.find("\n    }\n}", start)
    if end < 0:
        fail("callRefreshIntent2 end anchor not found")
    end += len("\n    }")

    old = text[start:end]
    if "func callRefreshIntent2(" not in old:
        fail("callRefreshIntent2 function not found in selected block")
    if "PrivateIntentRunner.run(" not in old:
        fail("expected upstream PrivateIntentRunner path not found")

    new = '''    // IOS27_DIRECT_REFRESH_INTENT
    // iOS 27: reuse SideStore's existing in-process AppIntent.perform() path.
    // That is the same path used when SideStore already has an IntentContext,
    // while the original LiveProcess path goes through PrivateIntentRunner.
    func callRefreshIntent2(identifier: String, mangledTypeName: String, progressCallback: (Progress)->Void ) async throws {
        if #available(iOS 27.0, *) {
            try await callRefreshIntent(mangledTypeName: mangledTypeName)
            return
        }

        try await withUnsafeThrowingContinuation { (c: UnsafeContinuation<(), any Error>) in
            let parent = PrivateIntentRunner.run(
                        identifier: identifier,
                        mangledTypeName: mangledTypeName
                    ) { result, error in
                        print("performAction result=\\(String(describing: result)), " +
                              "error=\\(String(describing: error))")
                        if let error {
                            c.resume(throwing: error)
                        } else {
                            c.resume()
                        }
                    }
            if let parent {
                progressCallback(parent)
            }
        }
    }'''

    path.write_text(text[:start] + new + text[end:], encoding="utf-8")

    verify = path.read_text(encoding="utf-8")
    required = [
        MARKER,
        "if #available(iOS 27.0, *)",
        "try await callRefreshIntent(mangledTypeName: mangledTypeName)",
        "PrivateIntentRunner.run("
    ]
    missing = [item for item in required if item not in verify]
    if missing:
        fail("verification missing: " + ", ".join(missing))

    print("iOS 27 direct refresh execution: PASS")
    print(path)

if __name__ == "__main__":
    main()
