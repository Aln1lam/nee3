# -*- coding: utf-8 -*-
"""剩余二次元约束修补：去 LinuxPrompt、Auth 字体、首页 banner。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "components"


def patch(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new[:60] in text:
            print(f"[skip] {label}")
            return
        raise SystemExit(f"[fail] {label}: not found in {path.name}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"[ok] {label}")


def patch_all(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        print(f"[skip] {label}")
        return
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"[ok] {label}")


# ── Auth：去掉 Reverier Mono 主导 ──
auth = SRC / "Auth.vue"
patch_all(
    auth,
    "font-family: 'Reverier Mono', Menlo, monospace !important;",
    "font-family: var(--font-ui) !important;",
    "Auth Reverier → font-ui",
)

# ── GameAdmin：LinuxPrompt → 普通 eyebrow ──
ga = SRC / "GameAdmin.vue"
patch(
    ga,
    """      <header class=\"matrix-page-head\">
        <LinuxPrompt :path=\"`~/games/${gameId}/admin`\" :cmd=\"`admin ${activeSection}`\" extra-class=\"matrix-page-prompt\" />
        <h2 class=\"matrix-page-title\">{{ sectionLabel }}</h2>""",
    """      <header class=\"matrix-page-head\">
        <p class=\"matrix-page-prompt\">赛事管理 · {{ sectionLabel }}</p>
        <h2 class=\"matrix-page-title\">{{ sectionLabel }}</h2>""",
    "GameAdmin eyebrow",
)
patch(
    ga,
    "import { ScoreboardChart, LinuxPrompt } from '@/components/shared'",
    "import { ScoreboardChart } from '@/components/shared'",
    "GameAdmin drop LinuxPrompt import",
)
patch(
    ga,
    "components: { NForm, NFormItem, NInput, NSwitch, NSelect, NDataTable, UiButton, UiLoadingTips, ScoreboardChart, LinuxPrompt },",
    "components: { NForm, NFormItem, NInput, NSwitch, NSelect, NDataTable, UiButton, UiLoadingTips, ScoreboardChart },",
    "GameAdmin drop LinuxPrompt component",
)

# ── GameTeams ──
gt = SRC / "GameTeams.vue"
patch(
    gt,
    """      <header class=\"matrix-page-head\">
        <LinuxPrompt :path=\"`~/games/${gameId}/teams`\" :cmd=\"pageCmd\" extra-class=\"matrix-page-prompt\" />
        <h2 class=\"matrix-page-title\">{{ pageTitle }}</h2>""",
    """      <header class=\"matrix-page-head\">
        <p class=\"matrix-page-prompt\">战队 · {{ pageTitle }}</p>
        <h2 class=\"matrix-page-title\">{{ pageTitle }}</h2>""",
    "GameTeams eyebrow",
)
patch(
    gt,
    "import { LinuxPrompt } from '@/components/shared'\n",
    "",
    "GameTeams drop import",
)
# components array may span lines
text = gt.read_text(encoding="utf-8")
if "LinuxPrompt," in text:
    gt.write_text(text.replace("LinuxPrompt,", "").replace(", LinuxPrompt", ""), encoding="utf-8", newline="\n")
    print("[ok] GameTeams drop component ref")

# ── ForgotPassword / ResetPassword / VerifyEmail ──
for name, eyebrow in [
    ("ForgotPassword.vue", "找回密码 · AUTH"),
    ("ResetPassword.vue", "重置密码 · AUTH"),
    ("VerifyEmail.vue", "邮箱验证 · AUTH"),
]:
    p = SRC / name
    text = p.read_text(encoding="utf-8")
    # replace LinuxPrompt line with plain p
    import re

    text2, n = re.subn(
        r'\s*<LinuxPrompt[^/]*/>\s*',
        f'\n          <p class="matrix-page-prompt">{eyebrow}</p>\n',
        text,
        count=1,
    )
    if n:
        text2 = text2.replace("import { LinuxPrompt } from '@/components/shared'\n", "")
        text2 = text2.replace("components: { LinuxPrompt },", "components: {},")
        text2 = text2.replace("components: { LinuxPrompt, NSpin },", "components: { NSpin },")
        p.write_text(text2, encoding="utf-8", newline="\n")
        print(f"[ok] {name} eyebrow")
    else:
        print(f"[skip] {name}")

# ── 清理未使用的 LinuxPrompt import ──
for name in ("Bulletin.vue", "KnowledgeList.vue", "ChallengeWorkspace.vue"):
    p = SRC / name
    text = p.read_text(encoding="utf-8")
    orig = text
    if name == "ChallengeWorkspace.vue":
        text = text.replace(
            "import { Article, Terminal, HammerPanel, MatrixShell, LinuxPrompt } from '@/components/shared'",
            "import { Article, Terminal, HammerPanel, MatrixShell } from '@/components/shared'",
        )
        text = text.replace(", LinuxPrompt }", " }").replace(", LinuxPrompt,", ",")
    else:
        text = text.replace("import { LinuxPrompt } from '@/components/shared'\n", "")
        text = text.replace(", LinuxPrompt }", " }")
        text = text.replace(", LinuxPrompt,", ",")
        text = text.replace("LinuxPrompt, ", "")
    if text != orig:
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"[ok] {name} clean unused LinuxPrompt")
    else:
        print(f"[skip] {name} clean")

# ── Home banner：改用现有 public 资源 ──
home = SRC / "Home.vue"
patch(
    home,
    """    { src: '/assets/index.webp', alt: 'banner', caption: 'Welcome to NEEPU CTF' },
    { src: '/assets/banner.light.svg', alt: 'banner2', caption: '社区与赛事' }""",
    """    { src: '/assets/index.svg', alt: 'banner', caption: 'Welcome to NEEPU CTF' },
    { src: '/assets/logo.svg', alt: 'banner2', caption: '社区与赛事' }""",
    "Home banner assets",
)

print("done")
