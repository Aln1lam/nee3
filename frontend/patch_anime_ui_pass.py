# -*- coding: utf-8 -*-
"""按 docs/ui-style-guide.md 去终端风、修仪表盘溢出（UTF-8 安全改中文 Vue）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent / "src" / "components"


def patch(path: Path, pairs: list[tuple[str, str]], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in pairs:
        if old not in text:
            print(f"[skip] {label}: not found → {old[:60]!r}")
            continue
        text = text.replace(old, new, 1)
    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"[ok] {label}")
    else:
        print(f"[noop] {label}")


def main() -> None:
    # ── shell 口吻 → 游戏 UI eyebrow ──
    replacements: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "Archive.vue",
            [
                ('page-prompt="ls ~/archive"', 'page-prompt="资料归档 · ARCHIVE"'),
            ],
        ),
        (
            "UserList.vue",
            [
                ('page-prompt="ls /users"', 'page-prompt="用户目录 · USERS"'),
            ],
        ),
        (
            "BulletinCreate.vue",
            [
                ('page-prompt="vim /bulletin/new"', 'page-prompt="发布公告 · NEW"'),
            ],
        ),
        (
            "Submissions.vue",
            [
                ('page-prompt="grep flag /submissions"', 'page-prompt="提交记录 · AUDIT"'),
            ],
        ),
        (
            "Teams.vue",
            [
                ('page-prompt="team status"', 'page-prompt="战队大厅 · TEAM"'),
            ],
        ),
        (
            "DevComponents.vue",
            [
                ('page-prompt="ls /dev/components"', 'page-prompt="组件演示 · DEV"'),
            ],
        ),
        (
            "ChallengeWorkspace.vue",
            [
                (
                    "const shellCmd = computed(() =>\n"
                    "      props.mode === 'training' ? 'ls challenges/' : 'grep -R flag .',\n"
                    "    )\n"
                    "    const shellPagePrompt = computed(() => {\n"
                    "      if (props.embedded) return ''\n"
                    "      return props.mode === 'training'\n"
                    "        ? `cd /training/${props.gameId}`\n"
                    "        : '选择题目开始挑战'\n"
                    "    })",
                    "const shellCmd = computed(() => '')\n"
                    "    const shellPagePrompt = computed(() => {\n"
                    "      if (props.embedded) return ''\n"
                    "      return props.mode === 'training'\n"
                    "        ? '练习场 · TRAINING'\n"
                    "        : '赛事题目 · CHALLENGES'\n"
                    "    })",
                ),
            ],
        ),
        (
            "AdminPanel.vue",
            [
                (
                    '<p class="matrix-page-prompt">运维中心 · ADMIN</p>',
                    '<p class="matrix-page-prompt">{{ currentMenu.code }} · {{ currentMenu.label }}</p>',
                ),
                (
                    "width: var(--sidebar-width, 256px);",
                    "width: var(--sidebar-width, 248px);",
                ),
            ],
        ),
        (
            "admin/PlatformDashboard.vue",
            [
                (
                    '<div class="bar" :style="{ height: (item.count * 20 + 40) + \'px\' }"></div>',
                    '<div class="bar" :style="{ height: Math.min(180, item.count * 20 + 40) + \'px\' }"></div>',
                ),
            ],
        ),
        (
            "Auth.vue",
            [
                (
                    '<n-button type="default" block strong @click="login" :loading="loading">\n'
                    "              确认进入系统\n"
                    "            </n-button>",
                    '<n-button type="primary" block strong @click="login" :loading="loading">\n'
                    "              确认进入系统\n"
                    "            </n-button>",
                ),
            ],
        ),
        (
            "Scoreboard.vue",
            [
                (
                    "<p class=\"matrix-page-prompt\">{{ loadError ? '排行榜加载失败' : '暂无排行数据' }}</p>",
                    "<p class=\"matrix-page-prompt\">{{ loadError ? '排行榜暂时不可用' : '暂无排行数据' }}</p>",
                ),
            ],
        ),
    ]

    for name, pairs in replacements:
        patch(ROOT / name, pairs, name)

    # adminMenu：去掉 shell cmd，改成游戏向副标（如被某处展示）
    menu = Path(__file__).resolve().parent / "src" / "config" / "adminMenu.js"
    mt = menu.read_text(encoding="utf-8")
    cmd_map = {
        "stats --overview": "overview",
        "users --list": "roster",
        "content --ls": "library",
        "bulletin --edit": "notices",
        "carousel --list": "banners",
        "games --admin": "arenas",
        "config --edit": "settings",
        "audit --tail": "audit",
    }
    for old, new in cmd_map.items():
        mt = mt.replace(f"cmd: '{old}'", f"cmd: '{new}'")
    menu.write_text(mt, encoding="utf-8", newline="\n")
    print("[ok] adminMenu.js cmds")


if __name__ == "__main__":
    main()
