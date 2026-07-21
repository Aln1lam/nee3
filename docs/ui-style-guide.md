# NEEPU CTF · UI 风格指南

> 东北电力大学 NEEPU CTF 竞赛与训练平台的前端视觉与布局规范。  
> 给设计师、开发者、AI Agent 复用：**改 UI 前先读本文 + 对照参考页**。  
> 工程操作（脚本、MCP 验收、构建）见 [`frontend-ui-harness.md`](frontend-ui-harness.md)。

---

## 1. 设计定位

| 维度 | 约定 |
|------|------|
| 产品 | 高校 CTF 竞赛 · 训练 · 知识库 · 运维后台 |
| 气质 | **二次元 / 轻游戏 UI**（活动面板、赛事列表、公告栏） |
| 不是 | 黑客终端、工控后台、通用 SaaS 仪表盘、AI 默认「衬线+陶土色」模板 |
| 签名元素 | **圆角卡片 + 分类色标 chip**（2–3 字母缩写，如 `TRN` `BUL`）— 全站只突出这一处 |
| 布局哲学 | **黄金分割 φ ≈ 1.618** + Fibonacci 间距节奏 |
| 侧栏哲学 | **248px 可折叠 rail**，与 `/training` 对齐 |

### 禁用清单

- Matrix 绿雨、终端光标动画、等宽字体主导导航
- `neepu@ctf:~$`、`SIGTRAP at 0x…` 等 shell 口吻（保留极少量 `matrix-page-prompt` 作 eyebrow 即可）
- Inter / IBM Plex 作为 UI 字体
- 纯黑底 + 荧光绿
- `margin: 0 -20px`（会导致整页左移）
- Vue scoped 里写 `padding` / `grid-template-columns`（与全局 golden-ratio 冲突）
- 对含中文的 `.vue` 使用 Cursor Write/StrReplace（易乱码 → 用 Python UTF-8 脚本）

---

## 2. 配色 Token

主题文件：`frontend/public/themes/light.css`、`dark.css`。  
运行时通过 `html[data-theme="light|dark"]` 切换。

### 主色板（4–6 色）

| 角色 | 浅色 `--*` | 深色 `--*` | 用途 |
|------|------------|------------|------|
| Primary 薄荷绿 | `#2DB58A` | `#5ED9A8` | 主按钮、链接、选中态、侧栏标题 |
| Accent 樱花粉 | `#EC4899` | `#F472B6` | 分类 chip、徽章、标签 |
| Depth 天蓝 | `#60A5FA` | `#7EB8FF` | 渐变辅色、图表点缀 |
| Surface 卡片 | `#FFFFFF` | `#232838` | 卡片、面板底 |
| Canvas 页面 | `#EEF2F5` / `#F4F6F8` | `#1A1D2E` | 主区台面、页面底 |
| Muted 说明 | `#64748B` | `#9CA8C4` | 副标题、计数、占位 |

语义色：`--success` `--warning` `--error` `--info`（见主题文件）。

### CSS 变量速查

```css
/* 最常用 — 优先用 var()，不要硬编码 hex */
var(--primary)
var(--muted)
var(--text)
var(--border)
var(--card-bg)
var(--page-bg)
var(--hover)
var(--code-bg)
var(--primary-rgb)          /* rgba 半透明 hover 用 */
var(--card-radius)          /* 10px */
var(--nav-height)           /* 72px */
var(--gradient-card-shadow)
var(--glass-sidebar-bg)
```

### 渐变与背景

- 页面底：柔光渐变 + 极淡网格（`gradient-system.css`），**网格是氛围不是主角**
- 卡片：浅色微渐变 + 柔和多层阴影（`--gradient-card-shadow`），hover 略增强
- 侧栏：磨砂半透明 + 右侧圆角 + 轻阴影（`collapsible-sidebar.css`）
- 禁止：电路板/十六进制底纹占满屏、硬偏移黑影

---

## 3. 字体

| 角色 | Token / 字体栈 | 使用场景 |
|------|----------------|----------|
| UI 正文 | `--font-ui` → `M PLUS Rounded 1c`, `Noto Sans SC`, `PingFang SC` | 导航、标题、按钮、侧栏 |
| 等宽 | `--font-mono` → `JetBrains Mono`, `Fira Code` | Flag、分数、代码块、终端内容 |
| 字号 | `--text-xs` … `--text-3xl` | 见 `global.css` / `typography.css` |

Naive UI 覆盖（`App.vue` → `themeOverrides`）：

- `borderRadius: '10px'`（禁止 `2px`）
- `fontFamily` 用 UI 栈，**禁止 Inter**
- `bodyColor: 'transparent'`（背景由 gradient 层承担）

---

## 4. 圆角 · 间距 · 动效

### 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `--card-radius` | 10px | 卡片、输入框、按钮（全局上限概念 14px） |
| `--radius-pill` | 10px | chip、tag |
| 侧栏右缘 | `var(--radius-xl)` | sidebar-rail 右上/右下圆角 |

### 两套间距体系（并存，各有用途）

**Fibonacci（布局 / golden-ratio.css）**

```
8 → 13 → 21 → 34 → 55 → 89 → 144 → 233
--fib-8 … --fib-233
--space-gutter: 21px
--space-gutter-lg: 34px
--space-section: 55px
```

**8pt baseline（组件 / gradient-system.css）**

```
--space-1: 8px … --space-8: 64px
```

规则：**页面级布局用 Fibonacci**；组件内部 padding 可混用 `--fib-*` 或 `--space-*`。

### 动效

- 过渡：`200–300ms`，`cubic-bezier(0.4, 0, 0.2, 1)`
- Hover：卡片 `translateY(-2px)` + 边框 primary + 阴影增强
- 侧栏折叠：`0.32s` width 动画
- 尊重 `prefers-reduced-motion`

---

## 5. 黄金分割布局（φ）

定义见 `frontend/src/assets/golden-ratio.css`（**必须在 `fullwidth-layout.css` 之后加载**）。

### 核心 Token

```css
--phi: 1.618033988749895;
--phi-minor: 0.618;           /* 38.2% */
--card-grid-min-golden: 324px; /* ≈ 200 × φ */
--hero-panel-width: min(372px, 38.2vw);
--prose-max-golden: 61.8ch;
```

### 常用比例

| 场景 | 比例 / 规则 |
|------|-------------|
| 主栏 : 侧栏 | **61.8% : 38.2%** 或 `1.618fr : 1fr` |
| 卡片网格最小列宽 | **324px**，gap **21px / 34px** |
| 横向卡片 | `aspect-ratio: var(--phi)`（宽:高 ≈ 1.618:1） |
| 验收区间 | 卡片实测比 **1.55 – 1.65** 即合格 |

### 页面布局映射

| 页面 | 根 class | 关键 golden 选择器 |
|------|----------|-------------------|
| 平台首页 `/` | `landing-page` | `.landing-hero` 三栏 φ；`.feature-grid` 4 列 |
| 个人工作台 `/home` | `home-page home-wrap` | 侧栏 `min(372px, 38.2%)`；`.home-bottom-grid` 日历:公告 = 1.618:1 |
| 训练 `/training` | `training-layout` | `.quick-card` aspect-ratio φ |
| 赛事详情 | `detail-layout` | 主内容:侧栏 ≈ 1.618:1 |
| 管理仪表盘 | `.metrics-grid` | 统计卡片统一 min-height / padding |

**规则：布局只写 `golden-ratio.css`，Vue scoped 只保留颜色 / hover / 动画。**

---

## 6. 页面壳结构

### 6.1 顶栏以下标准侧栏页

```
┌──────────────────────────────────────────────────┐
│ TitleBar（72px） HOM DOC TRN CTF BUL ADM         │
├────────────┬─────────────────────────────────────┤
│ sidebar    │  sidebar-main                       │
│ 248px      │  matrix-page-head（可选）            │
│ sidebar-   │  ─────────────────                  │
│ rail       │  页面内容                            │
│ [‹ 折叠]   │                                     │
└────────────┴─────────────────────────────────────┘
```

**必备 class**

```html
<div class="{page}-layout layout-with-sidebar" style="--sidebar-width: 248px">
  <aside class="sidebar-rail">…</aside>
  <button class="sidebar-collapse-trigger">‹</button>
  <main class="sidebar-main">…</main>
</div>
```

**Script**

```js
import { useCollapsibleSidebar } from '@/composables/useCollapsibleSidebar'
const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_{page}_sidebar_collapsed')
```

主区内边距参考：`padding: 32px 40px 40px`（与 Wiki 一致）。

### 6.2 MatrixShell 封装页

复杂侧栏 / 做题台 / 归档等用 `MatrixShell.vue`：

- 根：`matrix-shell layout-with-sidebar lab-deck`
- 导航行：`sidebar-item` + `item-code` + `item-title` + `item-count`
- 页头：`matrix-page-head` → `matrix-page-prompt` / `matrix-page-title` / `matrix-page-desc`

已接入：Wiki、Bulletin、Training、GamesHub、ChallengeWorkspace、Archive、Teams 等。

### 6.3 无侧栏页

Auth、Landing、部分 Account 页：单栏 `matrix-page` 或 `auth-aux`，**不要**套 `layout-with-sidebar`。

---

## 7. 组件模式

### 7.1 分类 Chip（签名元素）

```html
<span class="link-code">TRN</span>
<span class="item-code">BUL</span>
```

- 2–3 字母大写缩写
- 字体：**UI 体**，非等宽黑客绿
- 样式：`neepu-matrix.css` → `.link-code`, `.item-code`（粉底 pill）

### 7.2 侧栏导航行

Grid 三列：`36px code | 1fr label | auto meta`

| 页面 | 行 class |
|------|----------|
| Wiki | `wiki-link` |
| Bulletin | `sidebar-row` |
| Training / MatrixShell | `sidebar-item` |
| Games | `game-list-item` |
| Home 快捷导航 | `sidebar-link` |

Active / Hover：`rgba(var(--primary-rgb), 0.12)` 底 + primary 边框。

### 7.3 卡片

```css
border-radius: var(--card-radius);
padding: var(--card-padding-y-golden) var(--card-padding-x-golden);
box-shadow: var(--gradient-card-shadow);
```

- 可选左侧/顶部 accent chip
- Hover：边框 `--gradient-card-border-hover`，轻微上浮

### 7.4 页头（matrix-page-head）

```html
<header class="matrix-page-head">
  <p class="matrix-page-prompt">cd ~/home</p>   <!-- 可选 eyebrow，简短 -->
  <h2 class="matrix-page-title">欢迎回来</h2>
  <p class="matrix-page-desc">轮播 · 赛事日历 · 平台公告</p>
</header>
```

Eyebrow 用 UI 小字 + primary 色，**不要**长 shell 命令。

### 7.5 空状态

| 避免 | 改用 |
|------|------|
| `cat /bulletin — not found` | 「暂无公告」+ 一句引导 |
| `SIGTRAP at 0x…` | 「页面走丢了」+ 返回按钮 |
| 道歉长文 | 说明原因 + 下一步操作 |

### 7.6 Naive UI

- 全局圆角 / 字体跟 `themeOverrides`
- 禁止组件内 `borderRadius: 2px` 或硬编码 Inter
- 卡片用 `NCard` + `:bordered="false"` + 外层 `matrix-panel` 类较常见

---

## 8. CSS 架构与加载顺序

`frontend/src/main.js` 引入顺序（**勿乱**）：

```
global.css → typography → layout-proportions → components
→ neepu-matrix → linux-ui → admin-matrix → gradient-system
→ collapsible-sidebar → fullwidth-layout → golden-ratio  ← 最后
```

| 文件 | 职责 |
|------|------|
| `public/themes/*.css` | 深浅色语义色、阴影、玻璃侧栏 |
| `global.css` | 字体 token、body 基线 |
| `gradient-system.css` | 渐变背景、主区台面、卡片阴影、8pt 间距 |
| `collapsible-sidebar.css` | 248px rail、折叠、sidebar-item 交互 |
| `layout-proportions.css` | 工作区高度、page-gutter |
| `fullwidth-layout.css` | 取消窄栏 max-width |
| `golden-ratio.css` | **全局 φ 布局（优先改这里）** |
| `neepu-matrix.css` | chip、matrix-panel、页头、Naive 圆角覆盖 |
| `admin-matrix.css` | 运维后台专用 |

---

## 9. 参考页面（复制骨架时优先打开）

| 路由 | 组件 | 学什么 |
|------|------|--------|
| `/wiki` | `KnowledgeList.vue` | 标准侧栏 + 列表 |
| `/training` | `Training.vue` | quick-card 网格 + Matrix 侧栏 |
| `/games` | `GamesHub.vue` | 赛事列表侧栏 + 海报主区 |
| `/bulletin` | `Bulletin.vue` | 公告双栏 |
| `/home` | `Home.vue` | 个人工作台（无代办）+ φ 底部网格 |
| `/` | `PlatformLanding.vue` | Hero 三栏 + feature 4 列 |
| `/admin/dashboard` | `PlatformDashboard.vue` | metrics 卡片 |
| `/training/:id` | `ChallengeWorkspace.vue` | MatrixShell 做题台 |

---

## 10. 改 UI 工作流（简版）

1. **读参考页** → 确认用侧栏页还是 MatrixShell
2. **Palette / Type / Layout** 三句话自检（见 §1 禁用清单）
3. **布局** → 只改 `golden-ratio.css`
4. **颜色 / hover** → Vue scoped 或主题 CSS
5. **中文 Vue** → Python UTF-8 脚本
6. **`npm run build`** 必须通过
7. **MCP 验收** → 侧栏 248px、无 todo/乱码、φ 比例（见 harness §6）

---

## 11. 给 Agent 的一次性 Prompt

```
按 docs/ui-style-guide.md + docs/frontend-ui-harness.md 改 NEEPU CTF 前端：

风格：二次元轻游戏 UI + 黄金分割布局，248px 可折叠侧栏，分类 chip 为签名元素。
禁止：黑客终端美学、Inter、scoped 布局、Write/StrReplace 改中文 Vue。

任务：[具体页面/需求]

步骤：
1. 布局只写 golden-ratio.css（保持在 fullwidth-layout 之后）
2. 侧栏对齐 layout-with-sidebar + sidebar-rail + 248px
3. 必要时 Python UTF-8 脚本改 .vue
4. npm run build
5. MCP 验收目标路由的尺寸与视觉
```

---

## 12. 验收清单（PR 前勾选）

- [ ] 气质像竞赛平台，不像黑客站 / 通用 SaaS
- [ ] 字体：圆润 UI + 有限 mono
- [ ] 圆角 ≤ 14px，卡片柔和阴影
- [ ] 侧栏宽 248px，左缘 `x === 0`（无 `-20px` margin）
- [ ] 卡片网格 min 324px，gap 21/34px，宽高比 ≈ 1.618
- [ ] 深浅主题均可读
- [ ] 无 `??` 乱码
- [ ] `npm run build` 通过

---

## 13. 相关文档

| 文档 | 用途 |
|------|------|
| [`frontend-ui-harness.md`](frontend-ui-harness.md) | 脚本、MCP、构建、golden 选择器速查 |
| [`.cursor/skills/neepu-anime-ui/SKILL.md`](../.cursor/skills/neepu-anime-ui/SKILL.md) | Cursor Agent Skill（与本指南同步） |
| [`.cursor/skills/neepu-anime-ui/LAYOUT.md`](../.cursor/skills/neepu-anime-ui/LAYOUT.md) | 侧栏 DOM 模板 |
| [`api-frontend-checklist.md`](api-frontend-checklist.md) | API 联调（与 UI 分开） |

---

*最后更新：2026-07-20 — 含 /home 去代办、MatrixShell 侧栏统一、φ 全站布局*
