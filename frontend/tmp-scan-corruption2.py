# -*- coding: utf-8 -*-
from pathlib import Path

root = Path(r'E:\neepu\frontend\src\components')
results = []

for p in sorted(root.rglob('*.vue')):
    text = p.read_text(encoding='utf-8', errors='replace')
    rep = text.count('\ufffd')
    qm = 0
    broken = 0
    qm_samples = []
    for i, l in enumerate(text.splitlines(), 1):
        if "'??'" in l or '"??"' in l or '>??<' in l or '????' in l:
            qm += 1
            if len(qm_samples) < 3:
                qm_samples.append((i, l.strip()[:80]))
        if '?/span>' in l or '?/n-' in l:
            broken += 1
    if rep or qm or broken:
        rel = str(p.relative_to(root))
        results.append((rel, rep, qm, broken, text.count('\n') + 1, qm_samples))

for r in sorted(results, key=lambda x: (-x[1], -x[2], -x[3])):
    print(f'{r[0]}: lines={r[4]} replacement={r[1]} qmark_lines={r[2]} broken_tags={r[3]}')
    for ln, sample in r[5]:
        print(f'  L{ln}: {sample}')
print('TOTAL', len(results))
