# NEEPU 侧栏布局约定

与 `neepu-anime-ui` skill 配套。任何带侧栏的列表/工作台页面 **必须** 使用本结构。

## 标准 DOM 结构

```vue
<div
  class="{page}-layout layout-with-sidebar"
  :class="{ 'sidebar-collapsed': collapsed }"
  style="--sidebar-width: 248px"
>
  <aside class="{page}-sidebar sidebar-rail">
    <div class="sidebar-head sidebar-rail-head">
      <h2 class="sidebar-rail-title">中文标题</h2>
      <p class="sidebar-rail-sub">ENGLISH · TAG</p>
    </div>

    <nav class="sidebar-rail-nav">
      <!-- 导航行：wiki-link / sidebar-item / sidebar-row -->
    </nav>

    <div class="sidebar-rail-footer">
      <!-- 底部链接 -->
    </div>
  </aside>

  <button
    type="button"
    class="sidebar-collapse-trigger"
    :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
    @click="toggleSidebar"
  >
    <span class="chevron" :class="{ 'is-collapsed': collapsed }">‹</span>
  </button>

  <main class="{page}-main sidebar-main">
    <header class="matrix-page-head">
      <h2 class="matrix-page-title">主标题</h2>
      <p class="matrix-page-desc">副标题说明</p>
    </header>
    <!-- 页面内容 -->
  </main>
</div>
```

## Script 必备

```js
import { useCollapsibleSidebar } from '../composables/useCollapsibleSidebar'

const { collapsed, toggleSidebar } = useCollapsibleSidebar('neepu_{page}_sidebar_collapsed')
```

`storageKey` 每页独立，避免折叠状态串页。

## CSS 规则

### 必须

| 规则 | 原因 |
|------|------|
| 根节点含 `layout-with-sidebar` | 激活 `collapsible-sidebar.css` flex 布局 |
| 侧栏含 `sidebar-rail` | 统一宽度、圆角、背景 |
| 主区含 `sidebar-main` | 台面渐变 + 网格底纹（二次元风格下可改为柔光 blob） |
| `--sidebar-width: 248px` | 与 Wiki 对齐 |

### 禁止

| 反模式 | 后果 |
|--------|------|
| `margin: 0 -20px` | 整页左移 20px（Training/Bulletin 曾出现） |
| 侧栏单独 `width: 260px/280px` | 与 Wiki 不一致 |
| 省略 `sidebar-collapse-trigger` | 交互与 Wiki 不统一 |
| 省略 `layout-with-sidebar` 自写 flex | 重复造轮子、易歪 |

## 主区内边距

统一：`padding: 32px 40px 40px`（与 `KnowledgeList.vue` 一致）。

## 导航行类名对照

| 页面 | 导航元素 class | 全局 grid 选择器 |
|------|----------------|------------------|
| Wiki | `wiki-link` | `.layout-with-sidebar .wiki-link` |
| Bulletin | `sidebar-row` | `.bulletin-sidebar .sidebar-row` |
| Training | `sidebar-item` | `.training-sidebar .sidebar-item` |
| Games | `game-list-item` | `.layout-with-sidebar button.game-list-item` |
| SidebarLayout | `sidebar-layout__link` | `.layout-with-sidebar .sidebar-layout__link` |

新增页面：优先复用 `SidebarLayout.vue`；自定义导航行需加入 `collapsible-sidebar.css` 的 grid 选择器列表。

## 无侧栏页面

使用 `MatrixShell.vue` 或单栏 `matrix-page`，**不要** 套 `layout-with-sidebar`。

## MCP 验收命令

```js
// 布局左缘
document.querySelector('.layout-with-sidebar').getBoundingClientRect().x // 应为 0

// 侧栏宽度
getComputedStyle(document.querySelector('.sidebar-rail')).width // 应为 248px

// 字体
getComputedStyle(document.body).fontFamily // 应含 Noto Sans SC 或 M PLUS Rounded 1c
```

## 已接入页面

- `KnowledgeList.vue` — `/wiki`
- `Bulletin.vue` — `/bulletin`
- `Training.vue` — `/training`
- `GamesHub.vue` — `/games`

新增侧栏页：复制 Wiki 骨架，只替换导航 slot 与主区内容。
