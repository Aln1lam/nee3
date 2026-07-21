# -*- coding: utf-8 -*-
"""Global theme + golden-ratio cleanup — UTF-8 safe batch patches."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def patch(path, old, new, label=None):
    p = ROOT / path if not str(path).startswith('/') else Path(path)
    if not p.exists():
        print(f'MISSING {path}')
        return
    text = p.read_text(encoding='utf-8')
    if old not in text:
        print(f'SKIP {path}: {label or old[:48]!r}')
        return
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print(f'ok {path}: {label or "patched"}')


def regex_patch(path, pattern, repl, label=None):
    p = ROOT / path
    if not p.exists():
        print(f'MISSING {path}')
        return
    text = p.read_text(encoding='utf-8')
    new_text, n = re.subn(pattern, repl, text, flags=re.MULTILINE)
    if n == 0:
        print(f'SKIP {path}: {label or pattern}')
        return
    p.write_text(new_text, encoding='utf-8', newline='\n')
    print(f'ok {path}: {label or f"{n} replacements"}')


def bulk_theme_colors(directory='.'):
    """Replace hardcoded white card backgrounds with theme tokens."""
    base = ROOT / directory
    patterns = [
        (r'background:\s*white\s*;', 'background: var(--gradient-card-bg, var(--card-bg));'),
        (r'background:\s*#fff\s*;', 'background: var(--gradient-card-bg, var(--card-bg));'),
        (r'background:\s*#ffffff\s*;', 'background: var(--gradient-card-bg, var(--card-bg));'),
    ]
    skip_gradient_keep = (
        'challenge-item', 'badge', 'hint', 'target-', 'submission-item',
        'solved-badge', 'info-tips', 'description', 'value-input:focus',
    )
    for p in sorted(base.rglob('*.vue')):
        text = p.read_text(encoding='utf-8')
        orig = text
        for pat, repl in patterns:
            def _sub(m, _repl=repl):
                line_start = text.rfind('\n', 0, m.start()) + 1
                line = text[line_start:m.end()]
                if any(k in line for k in skip_gradient_keep):
                    return m.group(0)
                return _repl
            text = re.sub(pat, _sub, text)
        if text != orig:
            p.write_text(text, encoding='utf-8', newline='\n')
            print(f'ok {p.relative_to(ROOT)}: theme colors')


# ── CTFCompetitions ──
patch('CTFCompetitions.vue',
      '<div class="competitions-container">',
      '<div class="competitions-container page-wrap competition-page">',
      'competition root classes')

patch('CTFCompetitions.vue',
      '''.competitions-container {
  padding: 20px;
}

.header-title''',
      '''.header-title''',
      'remove competitions padding')

patch('CTFCompetitions.vue',
      '''.games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}''',
      '''.games-grid {
  display: grid;
  margin-top: var(--fib-21);
}''',
      'games-grid golden')

patch('CTFCompetitions.vue',
      '''.challenges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 20px;
}''',
      '''.challenges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(calc(var(--card-grid-min-golden) / var(--phi)), 1fr));
  gap: var(--space-gutter);
  margin-top: var(--fib-21);
}''',
      'challenges-grid golden')

for block in ('.challenge-detail {\n  padding: 20px;\n}\n',
              '.container-info {\n  padding: 20px;\n}\n',
              '.stats-section {\n  padding: 20px 0;\n}\n',
              '.scoreboard-section {\n  padding: 20px 0;\n}\n'):
    patch('CTFCompetitions.vue', block, '', f'remove {block.split("{")[0].strip()}')

patch('CTFCompetitions.vue',
      '.game-info {\n  font-size: 14px;\n  line-height: 1.8;\n  color: #666;\n}',
      '.game-info {\n  font-size: var(--text-sm);\n  line-height: 1.8;\n  color: var(--muted);\n}')

patch('CTFCompetitions.vue',
      '.label {\n  font-weight: bold;\n  min-width: 100px;\n  color: #333;\n}',
      '.label {\n  font-weight: bold;\n  min-width: 100px;\n  color: var(--text);\n}')

patch('CTFCompetitions.vue',
      '.value {\n  color: #666;\n  font-family: monospace;\n}',
      '.value {\n  color: var(--muted);\n  font-family: monospace;\n}')

patch('CTFCompetitions.vue',
      '''.value-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  background: #f5f5f5;
  color: #333;
  cursor: text;
}''',
      '''.value-input {
  flex: 1;
  padding: var(--fib-8) var(--fib-13);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  font-family: monospace;
  font-size: var(--text-sm);
  background: var(--code-bg, var(--hover));
  color: var(--text);
  cursor: text;
}''')

patch('CTFCompetitions.vue',
      '''.value-input:focus {
  outline: none;
  border-color: #1890ff;
  background: white;
}''',
      '''.value-input:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--card-bg);
}''')

patch('CTFCompetitions.vue',
      '''.description {
  margin: 20px 0;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}''',
      '''.description {
  margin: var(--fib-21) 0;
  padding: var(--fib-13);
  background: var(--hover);
  border-radius: var(--card-radius);
  border: 1px solid var(--border);
}''')

# ── ProfileEdit ──
patch('ProfileEdit.vue',
      '<div class="page-wrap">\n    <n-card>',
      '<div class="page-wrap profile-edit-page">\n    <n-card class="matrix-panel" :bordered="false">',
      'profile matrix panel')

patch('ProfileEdit.vue',
      '.avatar-preview {\n  width: 140px;\n  height: 140px;\n  border-radius: 12px;\n  overflow: hidden;\n  border: 2px solid rgba(0, 0, 0, 0.08);\n  background: #f5f5f5;',
      '.avatar-preview {\n  width: 140px;\n  height: 140px;\n  border-radius: var(--card-radius);\n  overflow: hidden;\n  border: 2px solid var(--border);\n  background: var(--hover);')

patch('ProfileEdit.vue',
      '.upload-hint {\n  font-size: 12px;\n  color: #999;',
      '.upload-hint {\n  font-size: var(--text-xs);\n  color: var(--muted);')

patch('ProfileEdit.vue',
      '.profile-edit-container {\n  display: flex;\n  gap: 32px;',
      '.profile-edit-container {\n  display: flex;\n  gap: var(--fib-34);')

# ── ArticleView ──
patch('ArticleView.vue',
      '''.article-panel {
  background: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(14,30,37,0.06);
  max-width: var(--prose-max-golden);
  margin: 0 auto;
}''',
      '''.article-panel {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: var(--card-padding-y-golden) var(--card-padding-x-golden);
  border-radius: var(--card-radius);
  border: 1px solid var(--gradient-card-border, var(--border));
  box-shadow: var(--gradient-card-shadow);
  max-width: var(--prose-max-golden);
  margin: 0 auto;
}''',
      'article panel theme')

patch('ArticleView.vue',
      '.article-content {\n  font-size: 16px;\n  line-height: 1.8;\n  color: #333;\n}',
      '.article-content {\n  font-size: var(--text-base);\n  line-height: 1.8;\n  color: var(--text);\n}')

patch('ArticleView.vue',
      '''.pdf-toolbar {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #f5f5f5;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}''',
      '''.pdf-toolbar {
  display: flex;
  gap: var(--fib-13);
  padding: var(--fib-13) var(--fib-21);
  background: var(--hover);
  border-bottom: 1px solid var(--border);
}''')

patch('ArticleView.vue',
      '''.pdf-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;''',
      '''.pdf-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: var(--fib-8) var(--fib-13);
  background: var(--card-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);''')

# ── ArticleUpload ──
patch('ArticleUpload.vue',
      'style="border: 1px solid #ddd; border-radius: 4px; margin-top:0; background:#fff;"',
      'class="vditor-host"',
      'vditor inline style')

patch('ArticleUpload.vue',
      ':deep(#vditor-edit .vditor) {\n  background: #fff;\n  border-radius: 4px;\n}',
      ':deep(#vditor-edit .vditor) {\n  background: var(--card-bg);\n  border-radius: var(--card-radius);\n}')

patch('ArticleUpload.vue',
      ':deep(#vditor-edit .vditor-toolbar) {\n  border-bottom: 1px solid #eef0f2;\n  background: #fafafa;\n}',
      ':deep(#vditor-edit .vditor-toolbar) {\n  border-bottom: 1px solid var(--border);\n  background: var(--hover);\n}')

patch('ArticleUpload.vue',
      '  border: 1px solid #e9e9e9;\n  background: rgba(255,255,255,0.95);',
      '  border: 1px solid var(--border);\n  background: var(--gradient-card-bg, var(--card-bg));')

patch('ArticleUpload.vue',
      '  background: #ffffff;\n  min-height: 680px;',
      '  background: var(--card-bg);\n  min-height: 680px;')

# ── GamesHub ──
patch('GamesHub.vue',
      '.empty-panel {\n  margin-top: 20px;\n  padding: 20px;',
      '.empty-panel {\n  margin-top: var(--fib-21);\n  padding: var(--card-padding-y-golden) var(--card-padding-x-golden);')

patch('GamesHub.vue',
      '  .games-poster-pane { padding: 20px 16px 32px; }',
      '  .games-poster-pane { padding: var(--space-gutter-lg) var(--fib-13) var(--fib-34); }')

patch('GamesHub.vue',
      '.other-games {\n  padding: 24px 28px;',
      '.other-games {\n  padding: var(--space-gutter-lg);')

# ── Admin scoped padding ──
admin_files = [
    'admin/CtfManagement.vue',
    'admin/ContentManagement.vue',
    'admin/LogAudit.vue',
    'admin/UserManagement.vue',
    'admin/SystemSettings.vue',
    'admin/CarouselManagement.vue',
    'admin/PlatformDashboard.vue',
    'admin/MetricCard.vue',
    'admin/DynamicPackageManager.vue',
    'templates/CheatDetectionDetail.vue',
    'ContainerChallenge.vue',
    'CTFChallengeAdmin.vue',
    'ChallengeCard.vue',
    'Admin.vue',
    'Games.vue',
]
for f in admin_files:
    regex_patch(f, r'padding:\s*20px\s*;', 'padding: var(--fib-21);', 'padding fib-21')

bulk_theme_colors('.')
bulk_theme_colors('admin')
bulk_theme_colors('templates')

print('patch_global_theme.py done')
