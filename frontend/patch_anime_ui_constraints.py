# -*- coding: utf-8 -*-
"""按 docs/ui-style-guide.md §6 二次元约束做一轮集中修补。

- 主题 Token → 薄荷绿 / 樱花粉 / 天蓝
- UI 字体 → M PLUS Rounded + Noto Sans SC（非 Reverier/Inter 主导）
- 去掉终端主导 prompt（neepu@ctf / curl …）
- Home/MyProfile 用 Cookie 会话而非仅 localStorage
- 仪表盘图表溢出、Auth 按钮对比度、GamesHub 侧栏铺满
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[ok] write {path.relative_to(ROOT)}")


def patch_replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new in text or new[:40] in text:
            print(f"[skip] {label} already applied")
            return
        raise SystemExit(f"[fail] {label}: old snippet not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"[ok] {label}")


LIGHT_CSS = r""":root {
  /* NEEPU 二次元 / 轻游戏 · light — docs/ui-style-guide.md */
  --color-primary: #2DB58A;
  --color-accent: #EC4899;
  --color-depth: #60A5FA;
  --color-neon: #5ED9A8;
  --accent-red: #EC4899;
  --primary: var(--color-primary);
  --muted: #64748B;
  --success: #16A34A;
  --warning: #D97706;
  --error: #E11D48;
  --info: var(--color-depth);
  --glow: none;
  --circuit-color: rgba(45, 181, 138, 0.08);
  --circuit-opacity: 0.08;
  --grid-line-color: rgba(45, 181, 138, 0.06);
  --grid-opacity: 0.35;
  --bg-layer: rgba(240, 251, 246, 0.92);
  --code-bg: rgba(45, 181, 138, 0.08);
  --term-bg: #1A1D2E;
  --term-fg: var(--color-primary);
  --card-radius: 12px;
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 14px;
  --radius-pill: 10px;

  --avatar-dark: rgba(45, 181, 138, 0.14);
  --avatar-light: rgba(255, 255, 255, 0.95);

  --light-page-bg: #F0FBF6;
  --light-nav-bg: rgba(240, 251, 246, 0.78);
  --nav-height: 72px;
  --light-card-bg: #FFFFFF;
  --light-text: #0F172A;
  --light-border: rgba(15, 23, 42, 0.08);

  --landing-panel-bg: rgba(255, 255, 255, 0.86);
  --landing-splash-bg: #F0FBF6;
  --on-primary-text: #FFFFFF;
  --content-max-width: none;
  --shadow-lg: 0 10px 30px rgba(45, 181, 138, 0.12);
  --landing-mask: none;
  --carousel-caption-gradient: linear-gradient(
    to top,
    rgba(15, 23, 42, 0.45) 0%,
    rgba(15, 23, 42, 0.16) 38%,
    transparent 100%
  );

  --gradient-page-base: #F0FBF6;
  --gradient-page-glow: radial-gradient(ellipse at 20% 0%, rgba(45, 181, 138, 0.16), transparent 55%),
    radial-gradient(ellipse at 90% 10%, rgba(236, 72, 153, 0.1), transparent 45%);
  --noise-opacity: 0;

  --main-surface-bg: #EEF2F5;
  --main-surface-grid: rgba(45, 181, 138, 0.05);
  --sidebar-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);

  --gradient-card-bg: #FFFFFF;
  --gradient-card-border: rgba(15, 23, 42, 0.06);
  --gradient-card-border-hover: rgba(45, 181, 138, 0.35);
  --gradient-card-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  --gradient-card-shadow-hover: 0 12px 28px rgba(45, 181, 138, 0.14);
  --gradient-card-header: rgba(45, 181, 138, 0.06);
  --gradient-card-header-text: #0F172A;

  --gradient-btn-fill: #2DB58A;
  --gradient-btn-fill-hover: #249E76;
  --gradient-btn-glow: none;
  --gradient-btn-glow-soft: none;

  --gradient-border: rgba(45, 181, 138, 0.35);
  --gradient-tag-fill: rgba(236, 72, 153, 0.12);
  --gradient-tag-text: #DB2777;
  --gradient-tag-border: rgba(236, 72, 153, 0.24);

  --gradient-nav-bg: rgba(240, 251, 246, 0.78);
  --gradient-nav-active: rgba(45, 181, 138, 0.14);
  --gradient-nav-hover: rgba(45, 181, 138, 0.08);

  --page-bg: var(--light-page-bg);
  --nav-bg: var(--gradient-nav-bg);
  --card-bg: var(--gradient-card-bg);
  --sidebar-bg: transparent;
  --glass-sidebar-bg: rgba(255, 255, 255, 0.72);
  --glass-sidebar-border: rgba(15, 23, 42, 0.08);
  --surface-shine: rgba(255, 255, 255, 0.7);
  --surface-edge: rgba(15, 23, 42, 0.06);
  --text: var(--light-text);
  --border: var(--light-border);
  --primary-rgb: 45, 181, 138;
  --primary-hover: #249E76;
  --hover: rgba(45, 181, 138, 0.1);
  --overlay: rgba(15, 23, 42, 0.22);
  --landing-page-bg: transparent;

  --card-accent: var(--color-primary);
  --card-accent-foreground: var(--on-primary-text);
}

html,
body,
#app {
  transition: background-color 250ms ease, color 250ms ease;
}
"""

DARK_CSS = r""":root {
  /* NEEPU 二次元 / 轻游戏 · dark — docs/ui-style-guide.md */
  --color-primary: #5ED9A8;
  --color-accent: #F472B6;
  --color-depth: #7EB8FF;
  --color-neon: #5ED9A8;
  --accent-red: #F472B6;
  --primary: var(--color-primary);
  --muted: #9CA8C4;
  --success: #4ADE80;
  --warning: #FBBF24;
  --error: #FB7185;
  --info: var(--color-depth);
  --glow: none;
  --circuit-color: rgba(94, 217, 168, 0.12);
  --circuit-opacity: 0.1;
  --hex-grid-color: rgba(255, 255, 255, 0.03);
  --grid-line-color: rgba(94, 217, 168, 0.08);
  --grid-opacity: 0.35;
  --bg-layer: rgba(26, 29, 46, 0.92);
  --code-bg: #232838;
  --term-bg: #12141D;
  --term-fg: var(--color-primary);
  --card-radius: 12px;
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 14px;
  --radius-pill: 10px;

  --light-page-bg: #1A1D2E;
  --light-nav-bg: rgba(26, 29, 46, 0.78);
  --light-card-bg: #232838;
  --light-text: #E2E8F0;
  --light-border: rgba(255, 255, 255, 0.1);

  --nav-height: 72px;
  --content-max-width: none;
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.35);
  --hover: rgba(94, 217, 168, 0.12);

  --landing-page-bg: transparent;
  --landing-panel-bg: rgba(35, 40, 56, 0.86);
  --landing-splash-bg: #1A1D2E;
  --on-primary-text: #0F172A;
  --landing-mask: none;
  --carousel-caption-gradient: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.55) 0%,
    rgba(0, 0, 0, 0.2) 40%,
    transparent 100%
  );

  --gradient-page-base: #1A1D2E;
  --gradient-page-glow: radial-gradient(ellipse at 15% 0%, rgba(94, 217, 168, 0.18), transparent 50%),
    radial-gradient(ellipse at 90% 8%, rgba(244, 114, 182, 0.12), transparent 45%);
  --noise-opacity: 0;
  --main-surface-bg: #1A1D2E;
  --main-surface-grid: rgba(94, 217, 168, 0.06);
  --sidebar-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);

  --gradient-card-bg: #232838;
  --gradient-card-border: rgba(255, 255, 255, 0.08);
  --gradient-card-border-hover: rgba(94, 217, 168, 0.4);
  --gradient-card-shadow: 0 10px 28px rgba(0, 0, 0, 0.28);
  --gradient-card-shadow-hover: 0 14px 32px rgba(94, 217, 168, 0.12);
  --gradient-card-header: rgba(94, 217, 168, 0.08);
  --gradient-card-header-text: #E2E8F0;

  --gradient-btn-fill: #5ED9A8;
  --gradient-btn-fill-hover: #7EE8C0;
  --gradient-btn-glow: none;
  --gradient-btn-glow-soft: none;
  --gradient-border: rgba(94, 217, 168, 0.35);
  --gradient-tag-fill: rgba(244, 114, 182, 0.16);
  --gradient-tag-text: #F9A8D4;
  --gradient-tag-border: rgba(244, 114, 182, 0.28);

  --gradient-nav-bg: rgba(26, 29, 46, 0.78);
  --gradient-nav-active: rgba(94, 217, 168, 0.16);
  --gradient-nav-hover: rgba(94, 217, 168, 0.1);

  --page-bg: var(--light-page-bg);
  --nav-bg: var(--gradient-nav-bg);
  --card-bg: var(--gradient-card-bg);
  --sidebar-bg: transparent;
  --glass-sidebar-bg: rgba(35, 40, 56, 0.78);
  --glass-sidebar-border: rgba(255, 255, 255, 0.08);
  --surface-shine: rgba(255, 255, 255, 0.04);
  --surface-edge: rgba(255, 255, 255, 0.06);
  --text: var(--light-text);
  --border: var(--light-border);
  --primary-rgb: 94, 217, 168;
  --primary-hover: #7EE8C0;
  --overlay: rgba(0, 0, 0, 0.45);

  --card-accent: var(--color-primary);
  --card-accent-foreground: var(--on-primary-text);
}

html,
body,
#app {
  transition: background-color 250ms ease, color 250ms ease;
}
"""


def patch_themes() -> None:
    write(ROOT / "public" / "themes" / "light.css", LIGHT_CSS)
    write(ROOT / "public" / "themes" / "dark.css", DARK_CSS)


def patch_fonts() -> None:
    global_css = ROOT / "src" / "assets" / "global.css"
    text = global_css.read_text(encoding="utf-8")
    text2 = text.replace(
        "  /* 西电同款混排：Reverier Mono + 系统中文 */\n"
        "  --font-ui: 'Reverier Mono', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;\n"
        "  --font-mono: 'Reverier Mono', Menlo, Consolas, monospace;\n"
        "  --font-display: var(--font-ui);\n"
        "  --font-hacker: var(--font-ui);",
        "  /* 二次元 UI：圆润正文字体；mono 仅 Flag/代码 */\n"
        "  --font-ui: 'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif;\n"
        "  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;\n"
        "  --font-display: var(--font-ui);\n"
        "  --font-hacker: var(--font-mono);",
    )
    if text2 == text:
        # try looser
        if "M PLUS Rounded 1c" in text:
            print("[skip] global.css fonts already anime")
        else:
            raise SystemExit("[fail] global.css font block not found")
    else:
        global_css.write_text(text2, encoding="utf-8", newline="\n")
        print("[ok] global.css fonts")

    index = ROOT / "index.html"
    idx = index.read_text(encoding="utf-8")
    old_link = """    <link rel="stylesheet" href="/fonts/reverier-mono.css" />
    <!-- 西电同款：Reverier Mono（本地）+ 系统中文；勿 CDN 拉 Noto 切片 -->"""
    new_link = """    <link rel="stylesheet" href="https://fonts.bunny.net/css?family=m-plus-rounded-1c:400,500,700|noto-sans-sc:400,500,700|jetbrains-mono:400,500&display=swap" />
    <link rel="stylesheet" href="/fonts/reverier-mono.css" />
    <!-- UI: M PLUS Rounded + Noto Sans SC；mono: JetBrains；Reverier 仅作兼容 -->"""
    if old_link in idx:
        index.write_text(idx.replace(old_link, new_link, 1), encoding="utf-8", newline="\n")
        print("[ok] index.html font CDN")
    elif "m-plus-rounded-1c" in idx:
        print("[skip] index.html fonts already anime")
    else:
        raise SystemExit("[fail] index.html font block not found")


def patch_app_theme() -> None:
    path = ROOT / "src" / "App.vue"
    text = path.read_text(encoding="utf-8")
    start = text.find("    const themeOverrides = computed(() => {")
    end = text.find("    return {\n      user, themeOverrides,", start)
    if start < 0 or end < 0:
        raise SystemExit("[fail] App.vue themeOverrides block not found")

    ui = "'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif"
    mono = "'JetBrains Mono', 'Fira Code', Consolas, monospace"
    block = f"""    const themeOverrides = computed(() => {{
      if (isDark.value) {{
        return {{
          common: {{
            primaryColor: '#5ED9A8',
            primaryColorHover: '#7EE8C0',
            bodyColor: 'transparent',
            textColor1: '#E2E8F0',
            textColor2: '#9CA8C4',
            textColor3: '#9CA8C4',
            cardColor: '#232838',
            modalColor: '#232838',
            popoverColor: '#232838',
            inputColor: '#232838',
            tableColor: '#232838',
            borderColor: 'rgba(94, 217, 168, 0.22)',
            borderRadius: '12px',
            fontSize: '16px',
            fontSizeMini: '12px',
            fontSizeTiny: '12px',
            fontSizeSmall: '14px',
            fontSizeMedium: '16px',
            fontSizeLarge: '18px',
            fontSizeHuge: '20px',
            fontFamily: "{ui}",
            fontFamilyMono: "{mono}",
          }},
          Button: {{
            textColorPrimary: '#0F172A',
            textColorHover: '#FFFFFF',
            textColorPressed: '#FFFFFF',
            textColorFocus: '#FFFFFF',
            border: '1px solid rgba(94, 217, 168, 0.28)',
            borderHover: '1px solid rgba(94, 217, 168, 0.55)',
            color: 'rgba(94, 217, 168, 0.12)',
            colorHover: 'rgba(94, 217, 168, 0.22)',
            colorPressed: 'rgba(94, 217, 168, 0.28)',
          }},
          Input: {{
            color: '#232838',
            colorFocus: '#2A3144',
            textColor: '#E2E8F0',
            placeholderColor: 'rgba(156, 168, 196, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderHover: '1px solid rgba(94, 217, 168, 0.45)',
            borderFocus: '1px solid rgba(94, 217, 168, 0.7)',
            caretColor: '#5ED9A8',
          }},
          Card: {{
            color: '#232838',
            textColor: '#E2E8F0',
            borderColor: 'rgba(255, 255, 255, 0.08)',
          }},
        }}
      }}
      return {{
        common: {{
          primaryColor: '#2DB58A',
          primaryColorHover: '#249E76',
          bodyColor: 'transparent',
          textColor1: '#0F172A',
          textColor2: '#64748B',
          textColor3: '#64748B',
          cardColor: '#FFFFFF',
          borderColor: 'rgba(45, 181, 138, 0.18)',
          borderRadius: '12px',
          fontSize: '16px',
          fontSizeMini: '12px',
          fontSizeTiny: '12px',
          fontSizeSmall: '14px',
          fontSizeMedium: '16px',
          fontSizeLarge: '18px',
          fontSizeHuge: '20px',
          fontFamily: "{ui}",
          fontFamilyMono: "{mono}",
        }},
      }}
    }})

"""
    path.write_text(text[:start] + block + text[end:], encoding="utf-8", newline="\n")
    print("[ok] App.vue themeOverrides")


def patch_home_session() -> None:
    path = ROOT / "src" / "components" / "Home.vue"
    text = path.read_text(encoding="utf-8")

    # soften eyebrow
    text = text.replace(
        '<p class="matrix-page-prompt">cd ~/home</p>',
        '<p class="matrix-page-prompt">个人工作台</p>',
    )

    if "from '@/services/auth'" not in text and "from '../services/auth'" not in text:
        # find script import area
        needle = "import { ref,"
        # looser: after first import block
        if "import { fetchSession, getUser }" not in text:
            # insert after vue imports
            import_anchor = None
            for cand in (
                "import { useRouter } from 'vue-router'\n",
                "import { useMessage } from 'naive-ui'\n",
            ):
                if cand in text:
                    import_anchor = cand
                    break
            if not import_anchor:
                # try any import line near script setup
                idx = text.find("<script")
                idx2 = text.find("\n", text.find("import", idx))
                import_anchor = text[idx2 + 1 : text.find("\n", idx2 + 1) + 1]
            text = text.replace(
                import_anchor,
                import_anchor + "import { fetchSession, getUser } from '@/services/auth'\n",
                1,
            )

    old_refresh = """    function refreshUserData() {
      const s = localStorage.getItem('neepu_user')
      if (s) {
        try {
          user.value = JSON.parse(s)
          console.log('User data refreshed:', user.value)
        } catch (e) {
          console.warn('Failed to parse user data:', e)
        }
      }
    }

    const user = ref(null)
    try {
      const s = localStorage.getItem('neepu_user')
      if (s) user.value = JSON.parse(s)
    } catch (e) { user.value = null }"""

    new_refresh = """    async function refreshUserData() {
      try {
        const u = await fetchSession({ force: true })
        user.value = u || getUser()
      } catch (e) {
        user.value = getUser()
      }
    }

    const user = ref(getUser())
    refreshUserData()"""

    if old_refresh in text:
        text = text.replace(old_refresh, new_refresh, 1)
    elif "fetchSession({ force: true })" in text:
        print("[skip] Home session already patched")
    else:
        raise SystemExit("[fail] Home.vue refreshUserData block not found")

    path.write_text(text, encoding="utf-8", newline="\n")
    print("[ok] Home.vue session + prompt")


def patch_myprofile_session() -> None:
    path = ROOT / "src" / "components" / "MyProfile.vue"
    text = path.read_text(encoding="utf-8")
    if "fetchSession" not in text:
        text = text.replace(
            "import { ref, onMounted, onUnmounted, inject } from 'vue'\n",
            "import { ref, onMounted, onUnmounted, inject } from 'vue'\n"
            "import { fetchSession, getUser } from '@/services/auth'\n",
            1,
        )
    old = """      try {
        const s = localStorage.getItem('neepu_user')
        if (s) user.value = JSON.parse(s)
      } catch (e) {
        user.value = null
      }"""
    # may vary whitespace
    import re
    text2, n = re.subn(
        r"try:\s*\n\s*const s = localStorage\.getItem\('neepu_user'\)\s*\n\s*if \(s\) user\.value = JSON\.parse\(s\)\s*\n\s*\} catch \(e\) \{\s*\n\s*user\.value = null\s*\n\s*\}",
        "try {\n"
        "        user.value = (await fetchSession({ force: true })) || getUser()\n"
        "      } catch (e) {\n"
        "        user.value = getUser()\n"
        "      }",
        text,
        count=1,
    )
    if n == 0:
        # simpler replace attempt
        if "await fetchSession" in text:
            print("[skip] MyProfile session already patched")
            return
        # find loadUserData function
        marker = "async function loadUserData"
        if "function loadUserData" in text or "async function loadUserData" in text:
            # replace localStorage block only
            if "localStorage.getItem('neepu_user')" in text:
                text = text.replace(
                    "const s = localStorage.getItem('neepu_user')\n"
                    "        if (s) user.value = JSON.parse(s)",
                    "user.value = (await fetchSession({ force: true })) || getUser()",
                    1,
                )
                # ensure loadUserData is async
                text = text.replace("function loadUserData()", "async function loadUserData()", 1)
                text = text.replace("function loadUserData ()", "async function loadUserData()", 1)
                path.write_text(text, encoding="utf-8", newline="\n")
                print("[ok] MyProfile.vue session")
                return
        raise SystemExit("[fail] MyProfile.vue user load block not found")
    # make loadUserData async if needed
    text2 = text2.replace("function loadUserData()", "async function loadUserData()", 1)
    path.write_text(text2, encoding="utf-8", newline="\n")
    print("[ok] MyProfile.vue session")


def patch_prompts() -> None:
    reps = [
        (
            ROOT / "src" / "components" / "Scoreboard.vue",
            [
                ('prompt="neepu@ctf:~$"', 'prompt=""'),
                (
                    ':page-prompt="`curl /games/${gameId}/scoreboard`"',
                    'page-prompt="积分排行"',
                ),
                (
                    "{{ loadError ? 'scoreboard --error' : 'scoreboard --empty' }}",
                    "{{ loadError ? '排行榜加载失败' : '暂无排行数据' }}",
                ),
            ],
        ),
        (
            ROOT / "src" / "components" / "Archive.vue",
            [('prompt="neepu@ctf:~$"', 'prompt=""')],
        ),
        (
            ROOT / "src" / "components" / "Teams.vue",
            [
                ('prompt="neepu@ctf:~$"', 'prompt=""'),
                ("team status ?empty", "暂无战队，创建或加入一支队伍开始"),
            ],
        ),
        (
            ROOT / "src" / "components" / "Submissions.vue",
            [('prompt="neepu@ctf:~$"', 'prompt=""')],
        ),
        (
            ROOT / "src" / "components" / "BulletinDetail.vue",
            [("cat /bulletin — not found", "公告不存在或已下线")],
        ),
        (
            ROOT / "src" / "components" / "UserList.vue",
            [("ls /users ?empty", "暂无用户")],
        ),
        (
            ROOT / "src" / "components" / "UserPublicProfile.vue",
            [("<p class=\"sidebar-prompt\">neepu@ctf:~$</p>", "<p class=\"sidebar-prompt\">选手主页</p>")],
        ),
        (
            ROOT / "src" / "components" / "AccountPassword.vue",
            [("<p class=\"matrix-page-prompt\">config / password</p>", "<p class=\"matrix-page-prompt\">安全设置</p>")],
        ),
        (
            ROOT / "src" / "components" / "AccountOAuth.vue",
            [("<p class=\"matrix-page-prompt\">config / oauth</p>", "<p class=\"matrix-page-prompt\">第三方账号</p>")],
        ),
        (
            ROOT / "src" / "components" / "AccountDelete.vue",
            [("<p class=\"matrix-page-prompt\">config / delete</p>", "<p class=\"matrix-page-prompt\">账号注销</p>")],
        ),
    ]
    for path, pairs in reps:
        if not path.exists():
            print(f"[skip] missing {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        changed = False
        for old, new in pairs:
            if old in text:
                text = text.replace(old, new)
                changed = True
        if changed:
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"[ok] prompts {path.name}")
        else:
            print(f"[skip] prompts {path.name}")

    # ChallengeWorkspace page prompt
    cw = ROOT / "src" / "components" / "ChallengeWorkspace.vue"
    t = cw.read_text(encoding="utf-8")
    old = ": `curl /games/${props.gameId}/challenges`"
    new = ": '选择题目开始挑战'"
    if old in t:
        cw.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
        print("[ok] ChallengeWorkspace prompt")
    else:
        print("[skip] ChallengeWorkspace prompt")

    # KnowledgeList / Bulletin LinuxPrompt — soften via string replace on cmd props
    for path, old, new in [
        (
            ROOT / "src" / "components" / "KnowledgeList.vue",
            '<LinuxPrompt path="~/wiki" cmd="ls articles/" extra-class="matrix-page-prompt" />',
            '<p class="matrix-page-prompt">知识库 · WIKI</p>',
        ),
        (
            ROOT / "src" / "components" / "Bulletin.vue",
            '<LinuxPrompt path="~/bulletin" cmd="less index.md" extra-class="matrix-page-prompt" />',
            '<p class="matrix-page-prompt">公告栏 · BULLETIN</p>',
        ),
    ]:
        if not path.exists():
            continue
        t = path.read_text(encoding="utf-8")
        if old in t:
            path.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
            print(f"[ok] soften {path.name}")
        else:
            print(f"[skip] soften {path.name}")


def patch_dashboard_css() -> None:
    path = ROOT / "src" / "assets" / "admin-matrix.css"
    text = path.read_text(encoding="utf-8")
    marker = "/* anime-ui: dashboard chart clamp */"
    if marker in text:
        print("[skip] admin dashboard clamp")
        return
    addon = f"""

{marker}
.admin-panel .chart,
.dashboard .chart {{
  overflow: hidden;
  max-height: 280px;
}}
.admin-panel .bar-chart,
.dashboard .bar-chart {{
  display: flex;
  align-items: flex-end;
  gap: var(--fib-8, 8px);
  height: 220px;
  max-height: 220px;
  overflow: hidden;
}}
.admin-panel .bar-chart .bar,
.dashboard .bar-chart .bar {{
  max-height: 180px !important;
}}
.admin-panel .todo-stats .progress-bar,
.dashboard .todo-stats .progress-bar {{
  height: 12px;
  border-radius: var(--radius-pill, 10px);
  overflow: hidden;
  background: rgba(var(--primary-rgb), 0.12);
}}
.admin-panel .todo-stats .progress-fill,
.dashboard .todo-stats .progress-fill {{
  height: 100%;
  border-radius: inherit;
  background: var(--primary);
}}
"""
    path.write_text(text + addon, encoding="utf-8", newline="\n")
    print("[ok] admin-matrix dashboard clamp")


def patch_gameshub_fill() -> None:
    path = ROOT / "src" / "assets" / "golden-ratio.css"
    text = path.read_text(encoding="utf-8")
    marker = "/* anime-ui: games hub fill */"
    if marker in text:
        print("[skip] games hub fill")
        return
    addon = f"""

{marker}
.games-hub.r2s-games,
.r2s-games {{
  min-height: calc(100vh - var(--nav-height, 72px) - 48px);
}}
.r2s-games__stage {{
  display: grid;
  grid-template-columns: minmax(248px, 0.382fr) minmax(0, 1.618fr);
  gap: var(--fib-21, 21px);
  align-items: stretch;
  min-height: 61.8vh;
}}
.r2s-games__list-pane {{
  min-height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: var(--card-radius);
  background: var(--glass-sidebar-bg, var(--card-bg));
  box-shadow: var(--sidebar-shadow, var(--gradient-card-shadow));
  padding: var(--fib-21, 21px) var(--fib-13, 13px);
}}
.r2s-games__list {{
  flex: 1;
}}
.r2s-games__cover-card {{
  border-radius: var(--card-radius);
  box-shadow: var(--gradient-card-shadow);
  overflow: hidden;
  min-height: 324px;
  aspect-ratio: var(--phi, 1.618);
  max-height: none;
}}
"""
    path.write_text(text + addon, encoding="utf-8", newline="\n")
    print("[ok] golden-ratio games hub fill")


def patch_auth_contrast() -> None:
    path = ROOT / "src" / "components" / "Auth.vue"
    text = path.read_text(encoding="utf-8")
    marker = "/* anime-ui: auth contrast */"
    if marker in text:
        print("[skip] auth contrast")
        return
    addon = f"""
{marker}
.n-card :deep(.n-button--default-type) {{
  background: var(--gradient-btn-fill, var(--primary)) !important;
  color: var(--on-primary-text, #fff) !important;
  border: none !important;
}}
.n-card :deep(.n-button--default-type:hover) {{
  background: var(--gradient-btn-fill-hover, var(--primary-hover)) !important;
}}
.n-card :deep(.n-input) {{
  --n-border: 1px solid var(--border) !important;
  --n-border-hover: 1px solid rgba(var(--primary-rgb), 0.45) !important;
  --n-border-focus: 1px solid rgba(var(--primary-rgb), 0.7) !important;
}}
"""
    # append before last style close or at end of style
    if "</style>" in text:
        text = text.replace("</style>", addon + "\n</style>", 1)
        path.write_text(text, encoding="utf-8", newline="\n")
        print("[ok] Auth.vue contrast")
    else:
        raise SystemExit("[fail] Auth.vue </style> not found")


def main() -> None:
    patch_themes()
    patch_fonts()
    patch_app_theme()
    patch_home_session()
    patch_myprofile_session()
    patch_prompts()
    patch_dashboard_css()
    patch_gameshub_fill()
    patch_auth_contrast()
    print("\nDone. Reload frontend and verify with MCP.")


if __name__ == "__main__":
    main()
