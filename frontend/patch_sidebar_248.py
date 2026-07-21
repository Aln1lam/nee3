# -*- coding: utf-8 -*-
from pathlib import Path

files = [
    'src/components/shared/MatrixShell.vue',
    'src/components/Training.vue',
    'src/components/KnowledgeList.vue',
    'src/components/Bulletin.vue',
    'src/components/Home.vue',
    'src/components/AdminPanel.vue',
]
root = Path(__file__).resolve().parent
old = 'style="--sidebar-width: var(--phi-side, 38.2%)"'
new = 'style="--sidebar-width: 248px"'
for rel in files:
    p = root / rel
    text = p.read_text(encoding='utf-8')
    if old not in text:
        print('skip', rel)
        continue
    p.write_text(text.replace(old, new), encoding='utf-8', newline='\n')
    print('ok', rel)
