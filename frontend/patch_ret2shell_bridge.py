# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / "src" / "assets" / "ret2shell-v3.css"
t = p.read_text(encoding="utf-8")

old = """:root {
  --r2s-bg: #eef1f6;
  --r2s-primary: #0891ed;
  --r2s-primary-rgb: 8, 145, 237;
  --r2s-error: #e05763;
  --r2s-error-rgb: 224, 87, 99;
  --r2s-text: #000000;
  --r2s-muted: rgba(0, 0, 0, 0.6);
  --r2s-card: rgba(255, 255, 255, 0.6);
  --r2s-header: rgba(0, 0, 0, 0.05);
  --r2s-btn-active: rgba(0, 0, 0, 0.1);
  --r2s-layer: rgba(238, 241, 246, 0.9);
  --r2s-radius-btn: 8px;
  --r2s-radius-card: 12px;
  --r2s-nav-height: 64px;
  --r2s-btn-h: 48px;
  --r2s-input-sm: 32px;
  --r2s-input-md: 48px;
  --r2s-icon: 20px;
  /* 西电同款：拉丁 Reverier Mono；中文无字形时落到系统黑体（非独立中文字库） */
  --font-ui: 'Reverier Mono', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --font-mono: 'Reverier Mono', Menlo, Consolas, monospace;
  --font-hacker: var(--font-mono);

  /* Bridge to existing tokens */
  --primary: var(--r2s-primary);
  --primary-rgb: var(--r2s-primary-rgb);
  --primary-hover: #0678c7;
  --error: var(--r2s-error);
  --info: var(--r2s-primary);
  --text: var(--r2s-text);
  --muted: var(--r2s-muted);
  --page-bg: var(--r2s-bg);
  --card-bg: var(--r2s-card);
  --nav-height: var(--r2s-nav-height);
  --card-radius: var(--r2s-radius-card);
  --radius-sm: var(--r2s-radius-btn);
  --radius-md: var(--r2s-radius-btn);
  --radius-lg: var(--r2s-radius-card);
  --radius-xl: var(--r2s-radius-card);
  --bg-layer: var(--r2s-layer);
  --hover: var(--r2s-btn-active);
  --circuit-color: rgba(0, 0, 0, 0.12);
  --circuit-opacity: 0.1;
}"""

new = """:root {
  /* 服从 themes/*.css 二次元 token；r2s 仅作组件别名，勿覆盖 --font-ui/--primary */
  --r2s-bg: var(--page-bg, #F0FBF6);
  --r2s-primary: var(--color-primary, #2DB58A);
  --r2s-primary-rgb: var(--primary-rgb, 45, 181, 138);
  --r2s-error: var(--error, #E11D48);
  --r2s-error-rgb: 225, 29, 72;
  --r2s-text: var(--text, #0F172A);
  --r2s-muted: var(--muted, #64748B);
  --r2s-card: var(--card-bg, #FFFFFF);
  --r2s-header: rgba(45, 181, 138, 0.06);
  --r2s-btn-active: rgba(45, 181, 138, 0.14);
  --r2s-layer: var(--bg-layer, rgba(240, 251, 246, 0.92));
  --r2s-radius-btn: 10px;
  --r2s-radius-card: var(--card-radius, 12px);
  --r2s-nav-height: var(--nav-height, 72px);
  --r2s-btn-h: 48px;
  --r2s-input-sm: 32px;
  --r2s-input-md: 48px;
  --r2s-icon: 20px;
}"""

if old not in t:
    raise SystemExit("root block not found")
t = t.replace(old, new, 1)
t = t.replace("  --r2s-primary: #3aa6f0;", "  --r2s-primary: var(--color-primary, #5ED9A8);", 1)
# dark also overrides primary-rgb maybe
t = t.replace("  --r2s-primary-rgb: 58, 166, 240;", "  --r2s-primary-rgb: var(--primary-rgb, 94, 217, 168);", 1)

# append reinforce after ret2shell so fonts/primary from themes+global win if something else set r2s
addon = """

/* anime-ui: ensure r2s does not re-assert Reverier / cyber blue */
:root {
  --font-ui: 'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  --font-display: var(--font-ui);
  --font-hacker: var(--font-mono);
}
"""
if "anime-ui: ensure r2s" not in t:
    t += addon

p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
