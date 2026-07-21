# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'Training.vue'
text = p.read_text(encoding='utf-8')

old = '''          <header class="matrix-page-head">
            <h2 class="matrix-page-title">开始今日份的训练</h2>
            <p class="matrix-page-desc">
              从左侧选择练习场 · 无时间限制 · 无限重试 · 不计入正式赛事积分
            </p>
          </header>'''
new = '''          <header class="matrix-page-head r2s-training-empty">
            <h2 class="matrix-page-title text-section">开始今日份的训练！</h2>
            <p class="matrix-page-desc text-muted">从左侧选择练习场 · 永久开放 · 不计入正式赛事积分</p>
          </header>'''
if old not in text:
    raise SystemExit('training empty header not found')
text = text.replace(old, new, 1)

# Prefer simpler sidebar title like xidian
old2 = '          <p class="sidebar-desc sidebar-rail-sub">TRAINING · LAB</p>'
new2 = '          <p class="sidebar-desc sidebar-rail-sub text-muted">练习场 · 永久开放</p>'
if old2 in text:
    text = text.replace(old2, new2, 1)

p.write_text(text, encoding='utf-8', newline='\n')
print('Training r2s copy ok')
