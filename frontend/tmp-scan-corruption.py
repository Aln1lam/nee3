# -*- coding: utf-8 -*-
import re
from pathlib import Path

root = Path(r'E:\neepu\frontend\src\components')
results = []

NULLISH = re.compile(r'\?\?\s*[\'"0-9a-zA-Z_$(\[]')
QMARK = re.compile(r"'??'|\"??\"|>??<|\?\?\?\?")
BROKEN = re.compile(r'\?/(span|n-|router|Ui|button|div|a|p|h\d)>')

for p in sorted(root.rglob('*.vue')):
    text = p.read_text(encoding='utf-8', errors='replace')
    rep = text.count('\ufffd')
    qm = 0
    broken = 0
    qm_lines = []
    for i, l in enumerate(text.splitlines(), 1):
        if QMARK.search(l) and not NULLISH.search(l):
            qm += 1
            qm_lines.append(i)
        if BROKEN.search(l):
            broken += 1
    if rep or qm or broken:
        rel = str(p.relative_to(root))
        results.append((rel, rep, qm, broken, text.count('\n') + 1, qm_lines[:5]))

for r in sorted(results, key=lambda x: (-x[1], -x[2], -x[3])):
    print(f'{r[0]}: lines={r[4]} replacement={r[1]} qmark_lines={r[2]} broken_tags={r[3]} sample_lines={r[5]}')
print('TOTAL', len(results))
