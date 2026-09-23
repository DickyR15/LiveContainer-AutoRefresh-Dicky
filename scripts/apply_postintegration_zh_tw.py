#!/usr/bin/env python3
from pathlib import Path
import sys

ROOTS = [Path(p) for p in sys.argv[1:]] or [Path("work/LiveContainer"), Path("work/EmbeddedSideStore")]

# Only UI phrases used by the AutoRefresh / SideStore scheduled-refresh feature.
REPLACEMENTS = {
    'Text("Scheduled refresh")': 'Text("排程重新整理")',
    'Text("Frequency")': 'Text("頻率")',
    'Text("SideStore scheduled refresh")': 'Text("SideStore 排程重新整理")',
    'Text("Limited")': 'Text("有限制")',
    'Text("Unknown")': 'Text("未知")',
    'Label("Scheduled refresh"': 'Label("排程重新整理"',
    'Label("Frequency"': 'Label("頻率"',
    'Label("SideStore scheduled refresh"': 'Label("SideStore 排程重新整理"',
    'Label("Limited"': 'Label("有限制"',
    'Label("Unknown"': 'Label("未知"',
    '"Scheduled refresh"': '"排程重新整理"',
    '"Frequency"': '"頻率"',
    '"SideStore scheduled refresh"': '"SideStore 排程重新整理"',
}

changed = 0
files = 0
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*.swift"):
        try:
            s = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        old = s
        for a, b in REPLACEMENTS.items():
            s = s.replace(a, b)
        if s != old:
            path.write_text(s, encoding="utf-8")
            files += 1
            changed += sum(old.count(a) - s.count(a) for a in REPLACEMENTS)
            print(f"localized: {path}")

print(f"Post-integration zh-TW AutoRefresh localization: PASS ({files} files changed)")
