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

    old = """    // call this when no IntentContext exists (when sidestore is loaded in LiveProcess)
    func callRefreshIntent2(identifier: String, mangledTypeName: String, progressCallback: (Progress)->Void ) async throws {
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
    }
"""
    new = """    // iOS 27 workaround: execute RefreshAllAppsIntent directly inside the
    // SideStore/LiveProcess context instead of routing through LinkServices'
    // private LNAction executor. The latter is the path that can return
    // ADI -45061 while the same refresh succeeds from the SideStore UI.
    //
    // Older iOS versions keep the upstream PrivateIntentRunner path.
    func callRefreshIntent2(identifier: String, mangledTypeName: String, progressCallback: (Progress)->Void ) async throws {
        if #available(iOS 27.0, *) {
            let resolvedType = try resolveType(mangledTypeName)
            guard let intentType = resolvedType as? any ProgressReportingIntent.Type else {
                throw SideStoreIntentError.typeIsNotAppIntent(mangledTypeName)
            }
            let intent = intentType.init()
            progressCallback(intent.progress)
            _ = try await intent.perform()
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
    }
"""
    if text.count(old) != 1:
        fail(f"expected exactly one callRefreshIntent2 block, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    verify = path.read_text(encoding="utf-8")
    for required in (
        MARKER,
        "if #available(iOS 27.0, *)",
        "let intent = intentType.init()",
        "progressCallback(intent.progress)",
        "_ = try await intent.perform()",
        "PrivateIntentRunner.run("
    ):
        if required not in verify:
            fail(f"verification missing: {required}")
    print("iOS 27 direct refresh execution: PASS")
    print(path)

if __name__ == "__main__":
    main()
