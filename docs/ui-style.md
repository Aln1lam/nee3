# NEEPU CTF · UI 风格规范（ui-style）

> **全站唯一视觉基准**：已敲定的 `Home.vue`  
> （黄金比例双栏 + 248px 通底侧栏 + 去搜索框纯净 Hero Banner）  
> 工程验收见 [`frontend-ui-harness.md`](frontend-ui-harness.md)。  
> 本文即权威规范；`ui-style-guide.md` 与本文内容同步。

---

## 1. 设计定位

| 维度 | 约定 |
|------|------|
| 产品 | 高校 CTF 竞赛 · 训练 · 知识库 · 运维后台 |
| 气质 | **深色极客 HUD**（对齐 HTB / NSSCTF 信息密度）+ Token 化薄荷绿 / 樱花粉签名 |
| 视觉基准页 | **`/home` → `Home.vue`**（其他路由必须与之对齐，禁止另起一套皮肤） |
| 布局哲学 | **黄金分割 φ ≈ 1.618** + Fibonacci 间距；双栏常用 **1.3fr : 1fr** |
| 侧栏哲学 | **248px 可折叠 rail**，高度通底，版权固定收在侧栏底部 |

### 禁用清单

- 全局假搜索 / Hero 放大镜 / `搜索题目 · 公告 · Wiki…` 弹层（搜索仅允许 `/training` 题过滤、`/wiki` 文档检索）
- 假大空卡片：`0 score` 属性格、无数据的「热门战队」等占位模块
- Inter / IBM Plex 作为 UI 字体
- 硬编码 Hex 铺满业务样式（Docker 激活蓝除外）
- 文字 `text-shadow`、父容器对正文 `filter: blur(...)`、2px 硬直角卡片
- Vue scoped 里写页面级 `padding` / `grid-template-columns`（与 `golden-ratio.css` 冲突）
- 对含中文的 `.vue` 直接用 Cursor Write/StrReplace（易乱码 → **Python UTF-8 脚本**）

---

## 2. 色彩与 Token

主题文件：`frontend/public/themes/light.css`、`dark.css`。  
运行时：`html[data-theme="light|dark"]` + `#theme-css` 切换。**禁止破坏双主题架构。**

| 角色 | Token | 浅色 | 深色 | 用途 |
|------|-------|------|------|------|
| Primary | `var(--primary)` | `#2DB58A` | `#5ED9A8` | 主按钮、链接、选中、侧栏强调 |
| Accent / Chip | `var(--primary)` / 薄荷绿 | `#2DB58A` | `#5ED9A8` | **Chip 强制薄荷绿，禁止粉/紫** |
| Docker 激活 | `#2496ED`（特例） | 同左 | 同左 | **仅**容器运行指示灯蓝光呼吸 |
| Surface | `var(--card-bg)` | `#FFFFFF` | `#232838` / `#131722` | 卡片、面板 |
| Canvas | `var(--page-bg)` | `#EEF2F5` | `#0B0E14` / `#1A1D2E` | 页面底 |
| Muted | `var(--muted)` | `#64748B` | `#9CA8C4` | 说明、占位 |

速查：`var(--text)` `var(--border)` `var(--hover)` `var(--code-bg)` `var(--primary-rgb)`  
`var(--card-radius)`（**10px**）`var(--nav-height)`（**72px**）`var(--gradient-card-shadow)` `var(--glass-sidebar-bg)`

---

## 3. 字体与去糊

| 角色 | Token | 栈 | 场景 |
|------|-------|-----|------|
| UI | `--font-ui` | `M PLUS Rounded 1c`, `Noto Sans SC`, `PingFang SC` | 导航、标题、按钮、侧栏 |
| Mono | `--font-mono` | `JetBrains Mono`, `Fira Code` | Flag、分数、代码、终端 |

硬性要求：

- 全站 `-webkit-font-smoothing: antialiased`
- 禁止文字 `text-shadow`；禁止对正文父级 `filter: blur`
- Naive `themeOverrides.fontFamily` 必须用 UI 栈，**禁止 Inter**
- 圆角：卡片 `var(--card-radius)`（10px）；Chip `var(--radius-pill)`；**严禁 2px 硬角**

---

## 4. 布局：248px 侧栏 + φ + 100vh

### 4.1 标准侧栏壳

```html
<div class="{page}-layout layout-with-sidebar lab-deck" style="--sidebar-width: 248px">
  <aside class="sidebar-rail">…导航…</aside>
  <button class="sidebar-collapse-trigger">‹</button>
  <main class="sidebar-main">…</main>
</div>
```

```js
import { useCollapsibleSidebar } from '@/composables/useCollapsibleSidebar'
const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_{page}_sidebar_collapsed')
```

- 侧栏高度贯穿 `calc(100vh - 72px)`，主区 `overflow: hidden`（禁止整页纵向乱跑）
- 底部版权统一：`© 2022-2026 东北电力大学`（链到 neepu.edu.cn），收在 **Sidebar 最下方**（`margin-top: auto`）

### 4.2 黄金双栏

定义只写 `frontend/src/assets/golden-ratio.css`：

| 场景 | 比例 |
|------|------|
| Home / 通用双栏 | **`1.3fr : 1fr`**（`.golden-dual-column`） |
| 严格 φ | **`1.618fr : 1fr`**（`.golden-dual-column.golden-dual-phi`） |
| 卡片网格 | `minmax(324px, 1fr)`，gap `21px` / `34px` |
| 公告 / Feed | **单列纵向**，禁止横向拉爆的扁长卡片 |

### 4.3 Hero Banner（对齐 Home）

- 纯净暗色微渐变 + 薄荷绿描边；左侧极弱薄荷绿光晕
- **禁止**密集斜纹、`repeating-linear-gradient`、紫/粉大发光、右下角模糊 LIVE 水印
- **禁止** Banner 内放大镜 / 全局搜索入口

---

## 5. 路由对齐任务（必须以 Home 为基准）

| 路由 | 要求 |
|------|------|
| `/home` | 视觉基准：φ 双栏、248px 通底侧栏、纯净 Banner、BUL 单列、SYS 终端 |
| `/training` | 248px 侧栏 + 题目卡 min 324px + Drawer/做题台 |
| `/games` | Hero/封面主舞台 + 248px 列表轨 + 版权通底 |
| `/wiki` `/bulletin` | 248px 侧栏 + **单列 Feed**；Wiki 保留页内搜索 |
| `/admin` | metrics 卡 + 100vh 高密度 HUD + 侧栏版权 |

---

## 6. 组件速记

- **Chip**：`link-code` / `item-code`，2–3 字母（`TRN` `BUL` `DOC`）
- **Docker 图标**：内联线稿 SVG（`DockerWhaleIcon`）；空闲哑光灰，运行中 `#2496ED` + 呼吸
- **主题切换**：`UiThemeBox` + `stores/theme.js`；`light.css` / `dark.css` 真双主题
- **空状态**：真人话引导，禁止长 shell / SIGTRAP 口吻

---

## 7. CSS 加载顺序（勿乱）

```
global.css → typography → layout-proportions → components
→ neepu-matrix → linux-ui → admin-matrix → gradient-system
→ collapsible-sidebar → fullwidth-layout → golden-ratio  ← 最后
```

布局只改 `golden-ratio.css`；颜色 / hover 可写 Vue scoped 或主题 CSS。

---

## 8. Agent Prompt（可直接粘贴）

```
按 docs/ui-style.md（与 ui-style-guide.md 同步）改 NEEPU CTF 前端：

基准：Home.vue（248px 通底侧栏 + 1.3fr/1fr 双栏 + 纯净 Banner）。
禁止：全局假搜索、假大空卡片、Inter、硬编码色、scoped 布局、中文 Vue 直写。
Token：--primary / --accent / --card-bg / --page-bg；Docker 激活仅用 #2496ED。
双主题：light.css + dark.css + data-theme，勿锁死。

任务：[具体页面]
步骤：布局进 golden-ratio.css → Python UTF-8 改中文 .vue → npm run build → MCP 验收。
```

---

## 9. 验收清单

- [ ] 气质对齐 Home HUD，无全局假搜索
- [ ] 字体为 M PLUS / Noto，无 Inter
- [ ] 侧栏 248px + 底栏版权，无主舞台底断层
- [ ] 双栏 1.3:1 或 φ；公告单列
- [ ] 圆角 10px；无文字阴影 / 正文 blur
- [ ] 深浅主题均可读
- [ ] `npm run build` 通过

---

## 10. 相关文档

| 文档 | 用途 |
|------|------|
| [`ui-style-guide.md`](ui-style-guide.md) | 与本文同步的别名副本 |
| [`frontend-ui-harness.md`](frontend-ui-harness.md) | 脚本 / MCP / 构建 |
| `Home.vue` | **全站唯一视觉与结构锚点** |
