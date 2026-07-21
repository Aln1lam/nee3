# -*- coding: utf-8 -*-
"""Remove scoped layout/theme conflicts; patch wrappers for golden-ratio.css."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def patch(path, old, new, label=None):
    p = ROOT / path if not str(path).startswith('/') else Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        print(f'SKIP {path}: {label or old[:40]!r}')
        return
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print(f'ok {path}: {label or "patched"}')


# AdminSetup — matrix 壳
patch('AdminSetup.vue',
      '<div class="admin-setup">\n    <div class="setup-card">',
      '<div class="admin-setup-shell">\n    <div class="matrix-panel setup-card">',
      'admin root classes')
patch('AdminSetup.vue',
      '.admin-setup {\n  min-height: 100vh;\n  background: var(--light-page-bg);\n  padding: 40px 20px;\n}\n\n.setup-card {\n  max-width: 600px;\n  margin: 0 auto;\n  background: white;\n  border-radius: 12px;\n  padding: 30px;\n  box-shadow: var(--card-shadow);\n}',
      '.setup-card h2 {\n  margin-top: 0;\n}',
      'admin setup styles')
patch('AdminSetup.vue', '.section h3 {\n  margin-top: 0;\n  margin-bottom: 15px;\n  color: #333;\n  font-size: 16px;\n}',
      '.section h3 {\n  margin-top: 0;\n  margin-bottom: 15px;\n  color: var(--text);\n  font-size: var(--text-base);\n}')
patch('AdminSetup.vue',
      '.user-info {\n  background: #f5f5f5;',
      '.user-info {\n  background: var(--hover);')
patch('AdminSetup.vue', '.info-item .value {\n  color: #333;\n}', '.info-item .value {\n  color: var(--text);\n}')
patch('AdminSetup.vue', '.info-box h4 {\n  margin-top: 0;\n  margin-bottom: 10px;\n  color: #333;\n}', '.info-box h4 {\n  margin-top: 0;\n  margin-bottom: 10px;\n  color: var(--text);\n}')
patch('AdminSetup.vue', '.info-box li {\n  margin-bottom: 6px;\n  color: #666;\n  font-size: 13px;\n}', '.info-box li {\n  margin-bottom: 6px;\n  color: var(--muted);\n  font-size: var(--text-sm);\n}')

# Article editors
patch('ArticleUpload.vue',
      '<div style="padding:16px; width:100%;">',
      '<div class="wiki-editor-page page-wrap">')
patch('ArticleEdit.vue',
      '<div style="padding:16px;max-width:900px;">',
      '<div class="article-editor-page page-wrap">')

# Events — layout 交给 golden-ratio
patch('Events.vue', '.events-root { padding: var(--events-padding, 16px); }\n', '')
patch('Events.vue',
      '.events-layout { display:flex; gap: var(--events-gap, 20px); align-items:flex-start }\n.events-main { width: var(--events-main-width, 720px) }\n',
      '')
patch('Events.vue',
      '.cal-cell { min-height: var(--cal-cell-min-height, 96px); border: var(--cal-cell-border, 1px solid #eee); padding: var(--cal-cell-padding, 6px); background: var(--cal-cell-bg, #fff) }\n.cal-cell.head { background: var(--cal-head-bg, #fafafa); font-weight:700; text-align:center }\n',
      '')

# ProfileEdit
patch('ProfileEdit.vue', '.page-wrap { padding: 16px }\n', '')

# Bulletin
patch('Bulletin.vue',
      '.bulletin-main {\n  padding: var(--page-gutter-lg-y, 24px) var(--page-gutter-lg-x, 24px);\n  overflow: auto;\n}\n',
      '.bulletin-main {\n  overflow: auto;\n}\n')
patch('Bulletin.vue',
      '  padding: 20px 16px;\n  display: flex;\n  flex-direction: column;\n  backdrop-filter: blur(8px);\n}',
      '  display: flex;\n  flex-direction: column;\n  backdrop-filter: blur(8px);\n}')
patch('Bulletin.vue', '.bulletin-item {\n  padding: 16px 18px;\n', '.bulletin-item {\n')

# GameTeams
patch('GameTeams.vue',
      '.teams-main {\n  flex: 1;\n  min-width: 0;\n  padding: 24px 28px;\n}\n',
      '.teams-main {\n  flex: 1;\n  min-width: 0;\n}\n')
patch('GameTeams.vue',
      '.matrix-panel {\n  padding: 14px 16px;\n}\n',
      '')
patch('GameTeams.vue',
      '.choose-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(var(--card-grid-min, 320px), 1fr));\n  gap: 16px;\n}\n',
      '.choose-grid {\n  display: grid;\n}\n')

# GamesHub
patch('GamesHub.vue',
      '  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));',
      '  grid-template-columns: repeat(auto-fill, minmax(var(--card-grid-min-golden), 1fr));')

# DevComponents
patch('DevComponents.vue',
      '.dev-components {\n  padding: 24px 28px 48px;\n}\n',
      '')

# Training
patch('Training.vue', '.welcome-panel {\n  max-width: 1080px;\n}\n', '')
patch('Training.vue',
      '.empty-panel {\n  padding: 24px;\n',
      '.empty-panel {\n')

# ChallengeDetailPage
patch('ChallengeDetailPage.vue',
      '''.challenge-page {
  min-height: 100%;
  padding: 20px;
}

.challenge-shell {
  max-width: 1320px;
  margin: 0 auto;
}
''',
      '''.challenge-page {
  min-height: 100%;
}

.challenge-shell {
  width: 100%;
  margin: 0;
}
''')
patch('ChallengeDetailPage.vue',
      '''.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}
''',
      '')

# ArticleView
patch('ArticleView.vue',
      '''.page-wrap {
  padding: 24px 40px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}
''',
      '''.page-wrap {
  width: 100%;
  margin: 0;
  box-sizing: border-box;
}
''')
patch('ArticleView.vue', '  max-width: 1000px;\n  margin: 0 auto;', '  max-width: var(--prose-max-golden);\n  margin: 0;')

# Account pages
for f in ('AccountPassword.vue', 'AccountOAuth.vue', 'AccountDelete.vue'):
    patch(f, '  padding: 16px 18px;\n', '')
    patch(f, '  padding: 20px 18px;\n', '')

# Orphan legacy
patch('Games.vue',
      '<div class="page-container">',
      '<div class="page-container legacy-page">\n    <p class="legacy-page-notice">Legacy 组件 · 请使用 /games (GamesHub)</p>')

print('patch_theme_scoped.py done')
