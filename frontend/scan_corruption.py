# -*- coding: utf-8 -*-
from pathlib import Path
import re

root = Path(__file__).resolve().parent / 'src' / 'components'
bad = []
for p in sorted(root.rglob('*.vue')):
    t = p.read_text(encoding='utf-8', errors='replace')
    if '\ufffd' in t:
        bad.append(f'{p.name}: U+FFFD')
    for i, line in enumerate(t.splitlines(), 1):
        if "'??'" in line or '">??<' in line or 'aria-label="??' in line:
            bad.append(f'{p.name}:{i}: {line.strip()[:100]}')

print('\n'.join(bad) if bad else 'OK: no visible ?? corruption')
print('count', len(bad))
