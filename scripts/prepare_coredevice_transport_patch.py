#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

UPSTREAM = Path("builder/scripts/patch_combined_transport.py")
UPSTREAM_DIR = UPSTREAM.parent.resolve()
if str(UPSTREAM_DIR) not in sys.path:
    sys.path.insert(0, str(UPSTREAM_DIR))
MUX = Path("work/EmbeddedSideStore/Dependencies/minimuxer")

def load_focused_module():
    source = UPSTREAM.read_text(encoding="utf-8")
    # Keep the official SideStore 12a496ca operation/pipeline layers unchanged.
    # The upstream v3.0.2 operation patches target a different SideStore revision.
    source = source[:start] + "    return\\n\\n\\n" + source[source.find("def verify(root):"):]
    verify_start = source.find("def verify(root):")
    if verify_start < 0:
        raise SystemExit("focused transport: verify function not found")
    verify_end = source.find("\n\nif __name__ == \"__main__\":", verify_start)
    if verify_end < 0:
        raise SystemExit("focused transport: verify function end not found")
    verify = '''def verify(root):
    checks = {
        "DeviceGateway/idevice/IdeviceGateway.swift": [
            "tunnel_create_usb(provider, &adapter, &handshake)",
            "COMBINED_COREDEVICE_BATCH_V1",
            "usesCoreDevice",
            "afc_client_connect_rsd",
            "installation_proxy_connect_rsd",
            "STAGED_FILE_SIZE_MATCH",
            "[SIDESTORE_COREDEVICE] FETCH_UDID_START",
        ],
        "Common/PairingFile.swift": ["Composite records must use Lockdown/CoreDevice"],
        "Sources/MinimuxerImpl.swift": ["configureRefreshTransport", "hasActiveTransportBatch", "deviceUDID_present="],
    }
    for name, needles in checks.items():
        text = (root / name).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                raise SystemExit(f"Incomplete focused CoreDevice transport: {name}: {needle}")
'''
    source = source[:verify_start] + verify + source[verify_end:]

    path = Path("/tmp/patch_combined_transport_focused.py")
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("focused_transport", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    verify_only = "--verify-only" in sys.argv[1:]
    mod = load_focused_module()
    if verify_only:
        mod.verify(MUX)
        print("Focused CoreDevice transport verification: PASS")
        return
    mod.patch(MUX)
    print("Focused CoreDevice transport patch: PASS")

if __name__ == "__main__":
    main()
