# -*- coding: utf-8 -*-
"""Remove scoped layout overrides that block golden-ratio.css."""
from pathlib import Path

root = Path(__file__).resolve().parent / 'src' / 'components'

patches = [
    (
        root / 'Training.vue',
        """.training-main {
  padding: 32px 40px 40px;
  overflow: auto;
}""",
        """.training-main {
  overflow: auto;
}""",
    ),
    (
        root / 'Training.vue',
        """.game-quick-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}""",
        """.game-quick-list {
  display: grid;
  margin-bottom: var(--fib-21);
}""",
    ),
    (
        root / 'Training.vue',
        """.quick-card {
  padding: 18px 20px;
  border:""",
        """.quick-card {
  border:""",
    ),
    (
        root / 'KnowledgeList.vue',
        """.wiki-main {
  flex: 1;
  min-width: 0;
  padding: clamp(16px, 2vw, 24px);
}""",
        """.wiki-main {
  flex: 1;
  min-width: 0;
}""",
    ),
]

for path, old, new in patches:
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'mismatch in {path.name}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print(f'patched {path.name}')

print('done')
