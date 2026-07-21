# Task 01：工程初始化 + 路由骨架

> **前置依赖**：`00-common-context.md`
> **后续任务**：02-global-layout
> **技术栈**：沿用 `frontend/` 现有 Vue 3 + Vite + Naive UI + Axios 工程

---

## 本任务目标

在现有 `frontend/` 工程上补齐路由骨架与基础设施，确保全部目标路由可访问（未实现页面用占位组件），统一主题与平台配置 store。

## 具体要求

### 1. 工程基础（已存在，本任务查漏补缺）

- Vite + Vue 3 项目：`frontend/`
- 路径别名 `@/` → `src/`（`vite.config.js` 已配置）
- 主题 CSS：`public/themes/light.css`、`dark.css`
- 开发代理：`/api` → Flask 后端

### 2. 目录结构

```
frontend/src/
├── components/     # 页面与 UI 组件
├── composables/    # useTheme、usePlatform、toast 等
├── stores/         # theme.js、platform.js（响应式全局状态）
├── services/       # platform.js、API 封装
├── assets/         # global.css、components.css
└── router/index.js # 路由定义
```

### 3. 路由骨架（全部注册）

| 路由前缀 | 说明 | 状态 |
|---------|------|------|
| `/` | 首页 | 已有 PlatformLanding |
| `/account/*` | 账号 | 已有 |
| `/games` | 赛事列表 | 已有 |
| `/games/:id` | 比赛详情 | 已有 |
| `/games/:id/challenges` | 做题 | 已有 |
| `/games/:id/scoreboard` | 积分板 | 已有 |
| `/games/:id/teams/*` | 队伍 | 已有 |
| `/games/:id/admin/*` | 比赛管理 | 占位 RoutePlaceholder |
| `/training` | 训练场列表 | 已有 |
| `/training/:game` | 训练场做题 | 已有 |
| `/wiki` | 知识库 | 已有 |
| `/wiki/:article` | 知识库文章 | 已有 |
| `/bulletin` | 公告 | 已有 |
| `/bulletin/:article` | 公告详情 | 已有 |
| `/users` | 用户列表 | 已有 |
| `/users/:id` | 用户主页 | 已有 |
| `/magic/about` | 关于页 | 已有 |
| `/magic/sakana` | 彩蛋 | 已有 |
| `/admin/*` | 平台管理子路由 | AdminPanel + section 映射 |
| `/sigtrap/*` | 错误页 | 已有 |

### 4. 基础设施

- **Axios**：baseURL、401/502/503 拦截（`main.js` 已有）
- **主题 store**：`stores/theme.js` + `composables/useTheme.js`
- **平台配置 store**：`stores/platform.js`，从 `GET /api/platform/info` 加载，西电 fallback
- **路由过渡**：`App.vue` fade 过渡（已有）
- **占位页**：`RoutePlaceholder.vue` 供未实现路由使用

### 5. 主题 CSS 变量

`public/themes/*.css` 中定义：
- 主色 `#0078D6`、强调色 `#f83030`
- 语义色 success / warning / error / info
- `bg-layer` 半透明层

## 验收标准

- [ ] `npm run dev` 可启动，无编译错误
- [ ] 访问任意已注册路由可看到页面或占位页
- [ ] 深色/浅色主题切换生效
- [ ] `fetchPlatformInfo` fallback 返回西电配置
- [ ] 路由懒加载生效（Network 面板可见 chunk 分割）

## 输出说明

完成后列出：新建/修改文件、路由表、mock/fallback 数据位置。
