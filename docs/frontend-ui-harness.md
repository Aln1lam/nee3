# NEEPU CTF 前端 UI Harness

> 下次做前端美化、布局调整、全站风格统一时，按本文档执行。  
> 配套 API 联调清单见 [`api-frontend-checklist.md`](api-frontend-checklist.md)。

---

## 1. 目标与约束

| 项 | 约定 |
|----|------|
| 布局节奏 | 黄金分割 φ ≈ 1.618，间距用 Fibonacci：8 → 13 → 21 → 34 → 55 → 89 → 144 → 233 |
| 主/侧分栏 | 约 **61.8% : 38.2%**（文案区、日历区、详情主栏等） |
| 卡片网格 | 最小列宽 **324px**（≈ 200×φ），间距 **21px / 34px** |
| 卡片比例 | 横向卡片 `aspect-ratio: φ`（宽:高 ≈ 1.618:1） |
| 全屏 | 顶栏以下铺满视口，窄栏居中已被 `fullwidth-layout.css` 取消 |
| 顶栏高度 | `--nav-height: 72px`（`public/themes/light.css`、`dark.css`） |
| 中文 Vue 文件 | **禁止** Cursor `Write` / `StrReplace` 直接改含中文的 `.vue` → 用 Python UTF-8 脚本 |

---

## 2. 关键文件地图

```
frontend/src/
├── main.js                          # CSS 引入顺序（golden-ratio 必须最后）
├── assets/
│   ├── golden-ratio.css             # ★ 全局 φ 布局（优先改这里）
│   ├── layout-proportions.css       # 侧栏 256px、工作区高度、page-gutter
│   ├── fullwidth-layout.css         # 取消 max-width 窄栏
│   ├── typography.css               # 西电风格字号 token
│   ├── gradient-system.css          # 渐变 / 网格底纹
│   └── neepu-matrix.css             # Matrix 侧栏壳
├── components/
│   ├── PlatformLanding.vue          # 平台首页 /
│   ├── Home.vue                     # 个人工作台 /home（class: home-page）
│   ├── TitleBar.vue                 # 顶栏
│   ├── Training.vue                 # 训练 /training
│   ├── KnowledgeList.vue            # Wiki /wiki
│   ├── AdminPanel.vue               # 运维壳 /admin/*
│   └── GameDetail.vue               # 赛事详情 /games/:id
└── App.vue                          # full-height-mode / immersive-mode

frontend/                            # 维护脚本（UTF-8 安全）
├── rewrite_damaged.py               # 整文件重写损坏组件
├── patch_golden_overrides.py        # 去掉 scoped 与 golden-ratio 冲突
├── patch_golden_global.py           # 全局 golden 批量清理
├── rewrite_theme_pages.py           # 离题页面 Matrix/auth 重写
├── patch_theme_scoped.py            # 批量去掉 scoped 布局冲突
├── rewrite_golden_landing.py        # 首页 scoped 精简
├── fix_gamedetail_utf8.py           # GameDetail 中文恢复模板
├── fix_gamedetail_labels.py
└── scan_corruption.py               # 扫描 ?? 乱码
```

---

## 3. CSS 加载顺序（勿改乱）

`main.js` 中 **`golden-ratio.css` 必须在 `fullwidth-layout.css` 之后**，作为全局布局最后一层：

```js
import './assets/layout-proportions.css'
// … components / matrix / gradient …
import './assets/fullwidth-layout.css'
import './assets/golden-ratio.css'   // ← 最后
```

新增页面级布局规则：**只写进 `golden-ratio.css`**，不要在各 Vue 的 scoped 里重复 padding / grid-template-columns。

---

## 4. 标准工作流

### 4.1 启动环境

```powershell
cd E:\neepu\frontend
npm run dev
# 默认 http://localhost:5173/（若占用则 5174、5175…看终端输出）
```

可选本地账号（联调 /home、/admin）：

- 邮箱：`admin@neepu.edu.cn`
- 密码：`NeepuAdmin2025!`

### 4.2 改布局（推荐顺序）

1. **读页面结构**：确认根 class（如 `home-page`、`landing-page`、`matrix-layout`）。
2. **改 `golden-ratio.css`**：加/改 token 与选择器，优先用已有 `--fib-*`、`--space-gutter*`。
3. **删 scoped 冲突**：若 Vue 内仍有 `padding: 20px`、`grid-template-columns: …`，用 Python 脚本去掉（见 §5）。
4. **构建验证**：`npm run build`（必须 0 error；乱码正则会导致构建失败）。
5. **MCP 浏览器验收**：截图 + CDP 量尺寸（见 §6）。

### 4.3 新增页面接入 golden-ratio

**模板：**

```css
/* golden-ratio.css */

/* 页面壳 */
.your-page-wrap {
  padding: var(--space-gutter-lg);
  box-sizing: border-box;
}

@media (min-width: 1200px) {
  .your-page-wrap {
    padding: var(--space-section) clamp(var(--fib-34), 4vw, var(--fib-55));
  }
}

/* 卡片网格 */
.your-page-wrap .card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--card-grid-min-golden), 1fr));
  gap: var(--space-gutter-lg);
}

.your-page-wrap .card-item {
  aspect-ratio: var(--phi);
  min-height: var(--card-min-height-golden);
  padding: var(--card-padding-y-golden) var(--card-padding-x-golden);
}
```

**Vue 侧：**

- 根节点加语义 class（如 `home-page`）。
- scoped 只保留颜色、边框、hover、动画；**不写** padding / gap / grid 列宽。

---

## 5. 中文文件安全编辑

### 5.1 禁止

- 对含中文的 `.vue` 使用 Cursor **Write / StrReplace**（易变成 `??`，破坏模板与正则）。

### 5.2 正确做法

```powershell
# 扫描乱码
python E:\neepu\frontend\scan_corruption.py

# 批量去掉 scoped 布局冲突（可按需复制改 patches 列表）
python E:\neepu\frontend\patch_golden_global.py

# 整文件重写（TitleBar / PlatformLanding 等）
python E:\neepu\frontend\rewrite_damaged.py
```

**新脚本模板：**

```python
# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'Your.vue'
text = p.read_text(encoding='utf-8')
old = """...原样复制，含中文..."""
new = """...替换内容..."""
if old not in text:
    raise SystemExit('block not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
print('ok')
```

### 5.3 乱码症状

| 症状 | 处理 |
|------|------|
| 页面上 `??` 文案 | Python 按上下文恢复字符串 |
| 构建报 `Invalid regular expression: /??\|ban/i` | `GameDetail.vue` 等 script 内中文正则损坏 → `fix_gamedetail_utf8.py` 类脚本 |
| `grep '\?\?' frontend/src/components/Foo.vue` 有命中 | 优先修该文件 |

---

## 6. MCP 浏览器验收清单

使用 Cursor **browser MCP**（非必须登录的页先测）：

| 路由 | 检查点 |
|------|--------|
| `/` | Hero 三栏 φ；快速开始面板中间偏右；底部 **4 列** feature 卡；无 LIVE「容器生命周期」条 |
| `/home` | 侧栏 ≈38.2%；轮播高度；日历:公告 ≈ 1.618:1（需登录） |
| `/training` | Matrix 侧栏；quick-card 网格与间距 |
| `/wiki` | 侧栏 + 列表；主区内边距 fib 节奏 |
| `/admin/dashboard` | metrics-grid 卡片比例 |
| `/games/:id` | detail-layout 主栏:侧栏 ≈ 1.618:1 |

**CDP 量比例示例**（在浏览器 MCP 里执行）：

```javascript
(() => {
  const c = document.querySelector('.feature-card');
  const grid = document.querySelector('.feature-grid');
  return {
    cardRatio: c ? (c.offsetWidth / c.offsetHeight).toFixed(3) : null,
    cols: grid ? getComputedStyle(grid).gridTemplateColumns : null,
    gap: grid ? getComputedStyle(grid).gap : null,
  };
})()
```

期望参考：

- 卡片宽高比 ≈ **1.55–1.65**
- 桌面 feature 网格 **4 列**，gap **34px**

---

## 7. 构建与回归

```powershell
cd E:\neepu\frontend
npm run build
```

通过标准：

- 无 `Invalid regular expression` / 语法错误
- 仅有 chunk size 警告可忽略

**勿提交**（除非刻意保留工具链）：`frontend/tmp-*.py`、`tmp-*.vue` 临时文件。

---

## 8. 已有 golden-ratio 选择器速查

| 选择器 | 用途 |
|--------|------|
| `.landing-page .landing-hero` | 平台首页 Hero φ 三栏 |
| `.landing-page .feature-grid` | 首页 2→4 列卡片 |
| `.home-page.home-wrap` | 个人工作台整体 |
| `.home-page .home-bottom-grid` | 日历 + 公告 |
| `.training-main .game-quick-list .quick-card` | 训练卡片 φ |
| `.detail-layout` | 赛事详情主:侧 |
| `.stat-grid` / `.metrics-grid` | 管理/赛事统计卡 |
| `.charts-section` / `.charts-row` | 图表双栏 |
| `.profile-content-grid` | 个人资料双栏 |
| `.page-wrap` 等 | 通用页面 padding |

---

## 9. 与 API 清单并行时

UI harness **不负责** API 对接；联调时打开 [`api-frontend-checklist.md`](api-frontend-checklist.md)，按页面查：

- `InstanceBox`、Submissions、Hammer POST 等是否已接
- 后端脚本在 `backend/scripts/`（E2E 已测 API 以清单为准）

建议顺序：**先 harness 布局统一 → 再按 checklist 补 API**。

---

## 10. 给 Agent 的一次性 Prompt（复制即用）

```
按 docs/frontend-ui-harness.md 执行：

1. 只改 golden-ratio.css + 必要时 Python UTF-8 脚本清理 scoped 冲突
2. 禁止 Write/StrReplace 写中文 Vue
3. golden-ratio.css 保持在 fullwidth-layout.css 之后
4. npm run build 必须通过
5. MCP 浏览器验收：/ 、/home 、/training 、/wiki 、/admin/dashboard
6. 卡片分布与大小符合 φ（324px 网格、34px 间距、aspect-ratio: var(--phi)）
7. API 对接对照 docs/api-frontend-checklist.md，本次若只做 UI 则说明未动 API 项
```

---

## 11. 常见问题

**Q：改了 golden-ratio 但页面没变化？**  
A：Vue scoped 覆盖了全局。检查组件内是否还有 `padding` / `grid-template-columns`，用 Python 删掉或降低 scoped 优先级。

**Q：首页卡片变 2 列？**  
A：`.landing-page .feature-grid` 在 768px 以下 2 列、以上 4 列；scoped 里不要写死 `repeat(2, 1fr)`。

**Q：训练页卡片还是 260px 网格？**  
A：跑 `patch_golden_overrides.py` 或检查 `Training.vue` scoped 是否残留 `minmax(260px)`。

**Q：运维页又变成旧全屏 fixed？**  
A：应使用 `AdminPanel.vue` matrix 侧栏 + `router-view`，勿改回 fixed 全屏盖顶栏。

---

## 12. 全站主题审计（2026-07-20）

### 已重写为 Matrix / auth-aux 的页面

| 页面 | 路由 |
|------|------|
| `Scoreboard.vue` | `/games/:id/scoreboard` |
| `ForgotPassword.vue` | `/forgot-password` |
| `ResetPassword.vue` | `/reset-password` |
| `VerifyEmail.vue` | `/verify-email` |
| `Archive.vue` | `/archive` |
| `Submissions.vue` | `/submissions` |
| `Teams.vue` | `/teams` |
| `AdminSetup.vue` | `/admin/setup`（matrix-panel 壳） |

### 已 patch scoped + golden-ratio 的页面

Bulletin · GameTeams · GamesHub · Training · ChallengeDetailPage · ArticleView · ArticleUpload · ArticleEdit · Events · ProfileEdit · Account* · DevComponents · Games.vue（孤儿 legacy 标记）

### 仍偏 legacy、下次优先

- **`CTFCompetitions.vue`** — 赛事做题主路径，白底卡片多；已加 `.competitions-container` golden 网格，待迁 MatrixShell
- **`ArticleView.vue`** — PDF 区仍有 `#fff` fallback，正文已接 `--prose-max-golden`
- **`Admin.vue` / `Games.vue`** — 无路由孤儿组件，勿再引用

### 批量命令

```powershell
python E:\neepu\frontend\rewrite_theme_pages.py
python E:\neepu\frontend\patch_theme_scoped.py
cd E:\neepu\frontend; npm run build
```

---

*最后更新：2026-07-20 — ChallengeWorkspace MatrixShell + MCP 全站验收*

---

## 13. ChallengeWorkspace MatrixShell（2026-07-20）

### 结构

`ChallengeWorkspace.vue` 根节点改为 `MatrixShell`：

- **#sidebar**：`LinuxPrompt` + 题目树（`.tree-panel--matrix`）
- **#sidebar-footer**：返回练习场 / 赛事 / 排行榜链接
- **主区**：`workspace-dock` + 终端 / Tab 工作区
- **embedded 模式**：嵌入 `Training.vue` 时隐藏 Matrix 页头，避免与欢迎条重复

脚本：

```powershell
python E:\neepu\frontend\patch_challenge_matrix.py
python E:\neepu\frontend\patch_workspace_embedded.py
```

CSS：`golden-ratio.css` → `.challenge-workspace-matrix` 全高、零 padding 主区。

---

## 14. MCP 截图验收清单（2026-07-20）

截图保存在 Cursor 临时目录：`audit-01-*.png` … `audit-13-*.png`。

| # | 路由 | 截图 | 检查点 | 结果 |
|---|------|------|--------|------|
| 01 | `/` | audit-01-landing | Hero φ 三栏；feature 4 列 gap 34px；卡片比 ≈1.615 | ✅ |
| 02 | `/training` | audit-02-training-list | Matrix 侧栏 + quick-card 网格 | ✅ |
| 03 | `/training/69` | audit-03/04 | **MatrixShell 做题台**：LinuxPrompt、题目树、终端 Tab | ✅ |
| 05 | `/home` | audit-05-home | 个人工作台侧栏 + 日历/公告 φ 分栏 | ✅ |
| 06 | `/wiki` | audit-06-wiki | Wiki 侧栏 + matrix-page-head | ✅ |
| 07 | `/admin/dashboard` | audit-07-admin-dashboard | 运维侧栏 + metrics-grid | ✅ |
| 08 | `/bulletin` | audit-08-bulletin | Bulletin Matrix 双栏 | ✅ |
| 09 | `/forgot-password` | audit-09-forgot-password | auth-aux + LinuxPrompt | ✅ |
| 10 | `/archive` | audit-10-archive | MatrixShell 归档列表 | ✅ |
| 11 | `/games` | audit-11-games | GamesHub 侧栏 + 海报区 | ✅ |
| 12 | `/events` | audit-12-events | 日历 + 赛程双栏 | ✅ |
| 13 | `/teams` | audit-13-teams | MatrixShell 战队页 | ✅ |

### CDP 量化（首页 `/`）

- 卡片宽高比：**1.615**（目标 1.55–1.65）
- feature-grid gap：**34px**
- Hero 列：`1462px : 278px` ≈ **5.26:1**（三栏含中间 quick 面板）

### CDP 量化（做题台 `/training/69`）

- `.challenge-workspace-matrix` 存在：**true**
- LinuxPrompt：**true**
- Matrix 页头（embedded 前）：**true**；embedded 后由 Training 欢迎条承担标题

### 待补截图（可选）

- `/games/:id/challenges`（CTFCompetitions legacy 容器）
- `/games/:id/scoreboard`、`/games/:id/teams`
- `/submissions`、`/verify-email`、`/reset-password`

