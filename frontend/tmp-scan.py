# -*- coding: utf-8 -*-
import re
from pathlib import Path

root = Path(r'E:\neepu\frontend\src\components')
bad = []
for p in sorted(root.rglob('*.vue')):
    t = p.read_text(encoding='utf-8', errors='replace')
    issues = []
    if '\ufffd' in t:
        issues.append('U+FFFD')
    if re.search(r"['\"]\\?\\?['\"]", t):
        issues.append('?? strings')
    if re.search(r'[\u4e00-\u9fff]\?/', t):
        issues.append('broken tag')
    if issues:
        bad.append((str(p), issues))
for path, issues in bad:
    print(path, issues)
print('TOTAL', len(bad))
