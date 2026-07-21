# -*- coding: utf-8 -*-
import re
from pathlib import Path

root = Path(r'E:\neepu\frontend\src')
exts = {'.vue', '.js', '.css', '.ts'}
issues = {}

for p in sorted(root.rglob('*')):
    if p.suffix not in exts:
        continue
    try:
        text = p.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        issues[str(p.relative_to(root))] = [('read-error', str(e))]
        continue
    file_issues = []
    if p.suffix == '.vue':
        if '<template' in text and '</template>' not in text:
            file_issues.append((0, 'truncated', 'missing </template>'))
        if '<script' in text and '</script>' not in text:
            file_issues.append((0, 'truncated', 'missing </script>'))
    for i, line in enumerate(text.splitlines(), 1):
        if '\ufffd' in line:
            file_issues.append((i, 'replacement', line.strip()[:120]))
        elif re.search(r'Ã.|â€|锟斤拷|ï¿½|Â©|Â®|â€™|â€œ', line):
            file_issues.append((i, 'mojibake', line.strip()[:120]))
        elif re.search(r'[^<]/[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff-]*>', line) and '</' not in line:
            file_issues.append((i, 'broken-tag', line.strip()[:120]))
        elif re.search(r"['\"]\?{2,}['\"]", line):
            file_issues.append((i, 'qmark-text', line.strip()[:120]))
        elif re.search(r'>\?{2,}<', line):
            file_issues.append((i, 'qmark-ui', line.strip()[:120]))
        elif re.search(r'label:\s*["\']\?{2,}', line):
            file_issues.append((i, 'qmark-label', line.strip()[:120]))
    if file_issues:
        issues[str(p.relative_to(root))] = file_issues

out = Path(r'E:\neepu\frontend\tmp-full-scan.txt')
with out.open('w', encoding='utf-8') as f:
    f.write('TOTAL FILES WITH ISSUES: %d\n\n' % len(issues))
    for rel, items in sorted(issues.items()):
        f.write('=== %s (%d issues) ===\n' % (rel, len(items)))
        for item in items:
            f.write('  L%d [%s] %s\n' % (item[0], item[1], item[2]))
        f.write('\n')
print('done:', len(issues), 'files')
