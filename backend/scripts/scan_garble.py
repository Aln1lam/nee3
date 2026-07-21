#!/usr/bin/env python3
"""Scan frontend for invalid UTF-8 and replacement characters."""
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
bad = []
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        if not f.endswith((".vue", ".js", ".ts")):
            continue
        p = os.path.join(dp, f)
        try:
            t = open(p, "r", encoding="utf-8").read()
        except UnicodeDecodeError:
            bad.append(("invalid utf8", p))
            continue
        if "\ufffd" in t or "\uFFFD" in t:
            bad.append(("replacement char", p))
        # single '?' used as corrupted emoji/symbol in UI strings
        for i, line in enumerate(t.splitlines(), 1):
            if re.search(r"'\\?'[^?]", line) or re.search(r">'\\?<'", line):
                if "??" in line or "?" in line and "placeholder" in line.lower():
                    continue
                if "'?'" in line or ">'?<'" in line or "'?' :" in line:
                    bad.append((f"symbol L{i}", p))

print(f"Found {len(bad)} issues:")
for kind, p in bad:
    rel = os.path.relpath(p, ROOT)
    print(f"  [{kind}] {rel}")
