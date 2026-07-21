---
name: neepu-anime-ui
description: >-
  NEEPU CTF 二次元 / 游戏 UI 设计规范：配色、字体、组件气质与 Anthropic 两阶段设计流程。
  改版 frontend 页面、主题、侧栏布局、Naive UI 覆盖、去黑客风/去 AI 模板味时使用。
  用户提到二次元、动漫风、游戏界面、UI 风格、主题、设计感时优先读取本 skill。
---

# NEEPU CTF · 二次元 UI Skill

## 设计定位（固定 brief）

| 维度 | 要求 |
|------|------|
| 产品 | 东北电力大学 NEEPU CTF — 竞赛与训练平台 |
| 受众 | 高校 CTF 选手、社团成员、赛事参与者 |
| 气质 | **二次元 / 轻游戏 UI**（活动面板、任务列表、公告栏），不是黑客终端、不是工控后台、不是通用 SaaS |
| 签名元素 | **圆角任务卡片 + 分类色标 chip**（全站只突出这一处；其余区域克制） |
| 禁用 | Matrix 绿雨、终端 prompt、`neepu@ctf:~$`、等宽主导 UI、Inter/IBM Plex、纯黑+荧光绿模板、`margin: 0 -20px` |

> 旧版 `matrix` / `neon` skill 仅作历史参考；**本 skill 优先级更高**。触达相关文件时顺势迁移，勿扩大终端美学。

---

## 风格 token（目标态）

写代码前先用命名 hex 定 palette，再落到 `frontend/public/themes/*.css` 与 `global.css`。

### 配色（4–6 色）

| 角色 | 深色 | 浅色 | 用途 |
|------|------|------|------|
| Primary | `#5ED9A8` 薄荷绿 | `#2DB58A` | 主按钮、链接、选中态 |
| Accent | `#F472B6` 樱花粉 | `#EC4899` | 分类 chip、徽章 |
| Depth | `#7EB8FF` | `#60A5FA` | 渐变辅色 |
| Surface | `#232838` | `#FFFFFF` | 卡片底 |
| Canvas | `#1A1D2E` | `#F0FBF6` | 页面底 |
| Muted | `#9CA8C4` | `#64748B` | 说明文字 |

渐变：大角度柔光（绿→粉→蓝，低饱和度），**禁止**电路网格 / 十六进制底纹作为主角。

### 字体（2+ 角色）

| 角色 | 字体 | 说明 |
|------|------|------|
| UI 正文 | `M PLUS Rounded 1c`, `Noto Sans SC`, `PingFang SC`, sans-serif | 圆润、偏二次元友好 |
| 标题/display | 同上加重 700，或 `ZCOOL QingKe HuangYou`（仅大标题，慎用） | 有性格但不抢正文 |
| 数据/Flag | `JetBrains Mono`, `Fira Code` | **仅**分数、Flag、代码块；不作为导航/标题字体 |

`index.html` 字体 CDN 示例：

```html
<link rel="stylesheet" href="https://fonts.bunny.net/css?family=m-plus-rounded-1c:400,500,700|noto-sans-sc:400,500,700&display=swap" />
```

### 圆角与间距

- 圆角上限 **14px**：`--card-radius: 12px`，`--radius-xl: 14px`
- 间距：8pt 网格 `--space-1: 8px` … `--space-4: 32px`（见 `gradient-system.css`）

### 质感

- 卡片：浅色微渐变 + 柔和外阴影（`--gradient-card-shadow`），**不要**硬偏移黑影
- 侧栏：磨砂半透明 + 轻阴影，与主区有层次
- 动效：200–300ms；hover 轻微上浮 2px；尊重 `prefers-reduced-motion`

---

## Anthropic 两阶段流程（写 UI 前必走）

### Pass 1 — 设计计划（内部完成，再写代码）

用一段话输出：

1. **Palette**：上表 4–6 个命名色
2. **Type**：UI / display / mono 分工
3. **Layout**：一句话 + 简 ASCII（见 [LAYOUT.md](LAYOUT.md)）
4. **Signature**：任务卡片 + 分类 chip 如何呈现

**自检（任一命中则改计划）：**

- [ ] 是否像「近黑 + 荧光绿黑客站」？
- [ ] 是否像「奶油底 + 衬线 + 陶土色」AI 默认？
- [ ] 是否像「无圆角报纸版」？
- [ ] 签名元素是否超过一处抢戏？
- [ ] 是否脱离 CTF/竞赛/训练语义？

### Pass 2 — 实现与验收

1. 只改与 brief 相关的文件，最小 diff
2. 布局必须遵循 [LAYOUT.md](LAYOUT.md)
3. `App.vue` `themeOverrides`：`fontFamily` 用 UI 字体，`borderRadius: '12px'`，**禁止** Inter / `2px`
4. 改完用 MCP 浏览器查：`body` 字体、`.sidebar-main` 左缘 `x===0`、卡片 `border-radius`
5. **Chanel 法则**：完成后再删一处多余装饰

---

## 布局约定（摘要）

完整规范见 [LAYOUT.md](LAYOUT.md)。

```text
┌─────────────────────────────────────────────┐
│ Nav (56px)                                  │
├──────────┬──────────────────────────────────┤
│ sidebar  │  main (sidebar-main)             │
│ 248px    │  matrix-page-head → 内容          │
│ sidebar- │                                  │
│ rail     │                                  │
│ [‹折叠]  │                                  │
└──────────┴──────────────────────────────────┘
```

- 根容器：`layout-with-sidebar` + `--sidebar-width: 248px`
- 侧栏：`sidebar-rail` + `sidebar-rail-head/nav/footer`
- 主区：`sidebar-main`；**禁止** `margin: 0 -20px`
- 折叠：`useCollapsibleSidebar` + `sidebar-collapse-trigger`
- 已对齐页面：Wiki、Bulletin、Training、GamesHub

### 文案语气（游戏 UI，非 shell）

| 避免 | 改用 |
|------|------|
| `neepu@ctf:~$` | 侧栏小标题 + 英文副标（如「知识库 · WIKI」） |
| `ls /wiki` | 「全部文章」或分区名 |
| `cat /bulletin — not found` | 「暂无公告」+ 一句引导 |
| `SIGTRAP at 0x…` | 「页面走丢了」+ 返回按钮 |

空状态与错误：**说明原因 + 下一步**，不道歉、不堆技术栈。

---

## 关键文件地图

| 用途 | 路径 |
|------|------|
| 主题 token | `frontend/public/themes/dark.css`, `light.css` |
| 全局字体/圆角 | `frontend/src/assets/global.css` |
| 侧栏布局 | `frontend/src/assets/collapsible-sidebar.css` |
| 台面/渐变 | `frontend/src/assets/gradient-system.css` |
| 旧 Matrix 类（迁移中） | `frontend/src/assets/neepu-matrix.css` |
| Naive 覆盖 | `frontend/src/App.vue` → `themeOverrides` |
| 侧栏组件 | `frontend/src/components/shared/SidebarLayout.vue` |
| 参考页 | `KnowledgeList.vue`, `Bulletin.vue`, `Training.vue` |

---

## 组件规则

### 卡片（签名元素）

- `border-radius: var(--card-radius)`
- 左侧或顶部 **分类 chip**（圆角 pill，accent 色）
- hover：边框 primary + 阴影略增强 + `translateY(-2px)`

### 侧栏导航行

- 网格：`36px code | 1fr label | auto meta`（`collapsible-sidebar.css` 已定义）
- code 用 **2–3 字母缩写**（`ALL` `TRN` `BUL`），字体 UI，**非**等宽黑客绿
- active：primary 浅色底 + 边框，非终端高亮

### Naive UI

- 与 `themeOverrides` 一致；禁止组件内硬编码 `borderRadius: 2px` / `Inter`

---

## 与旧 skill 的关系

| Skill | 状态 |
|-------|------|
| **neepu-anime-ui** | **本项目主 skill** |
| matrix / neon / futuristic | deprecated，勿用于新 UI |
| gradient | 可保留柔光渐变思路，去掉电路/网格主角 |
| awesome-design | 注册表入口，默认指向本 skill |

---

## QA 清单（PR / 改 UI 后）

- [ ] 无终端 prompt / 等宽主导导航
- [ ] 字体为圆润 UI 体 + 有限 mono
- [ ] 侧栏与 Wiki 左缘对齐（MCP `getBoundingClientRect().x === 0`）
- [ ] 圆角 ≤ 14px，卡片有柔和阴影
- [ ] 深浅色主题均可读（WCAG AA 对比）
- [ ] `npm run build` 通过
- [ ] 签名元素（任务卡片+chip）唯一突出
