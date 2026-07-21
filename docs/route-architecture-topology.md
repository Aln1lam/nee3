# NEEPU CTF 平台 · 路由与架构拓扑

> 审计基线文档（2026-07-21）。前端：Vue 3 + Vue Router；后端：Flask Blueprint（约 243 个 endpoint，含部分重复注册）。

---

## 1. 技术架构概览

```
┌─────────────────┐     /api/*      ┌──────────────────────────────┐
│  frontend/      │ ──────────────► │  backend/app.py              │
│  Vue Router     │                 │  Blueprint 注册              │
│  services/*.js  │                 │  route/*.py                  │
└─────────────────┘                 └──────────────────────────────┘
```

**双轨注意（清理进度 2026-07-21）**：

| 前缀 | 状态 |
|------|------|
| `/api/competitions` | **赛事主路径**（列表/join/CRUD/分组/stats/export/流量） |
| `/api/challenges` | **做题主路径**（submit/hints/容器） |
| `/api/ctf` | **仅排行榜** scoreboard/timeline/user（+ notices/health/cleanup）；其余 **410** |
| `/api/container` | 兼容回退，Deprecation |
| `/api/games` | **已下线 410** |
| `/api/admin/games` | **已下线 410**（含 stats/export） |

---

## 2. 前端页面路由

来源：`frontend/src/router/index.js` + `frontend/src/config/adminMenu.js`

### 2.1 落地 / 公共

| 路径 | 名称 | 组件 | 鉴权 |
|------|------|------|------|
| `/` | Landing | PlatformLanding | 公开 |
| `/home` | PlatformHome | Home | 登录 |
| `/archive` | Archive | Archive | 公开 |
| `/events` | Events | Events | 公开 |
| `/magic/sakana` | MagicSakana | MagicSakana | 公开 |
| `/dev/components` | DevComponents | DevComponents | 登录 + 仅 DEV |
| `/sigtrap/:code` | Sigtrap | ErrorPage | 公开 |
| `/*` | — | → `/sigtrap/404` | — |

### 2.2 账号 / 认证

| 路径 | 说明 |
|------|------|
| `/auth` | 登录/注册合一页 |
| `/verify-email` `/forgot-password` `/reset-password` | 邮箱验证 / 找回 / 重置 |
| `/account/login` `/account/register` 等 | 别名 → `/auth` 等 |
| `/account/settings` → `info` / `password` / `oauth` / `mov-esp-ebp-pop-ebp` | 资料 / 改密 / OAuth / 注销（需登录） |
| `/myprofile` | 个人主页（需登录） |
| `/profile` | → settings/info |

### 2.3 公告 / Wiki / 用户

| 路径 | 说明 |
|------|------|
| `/bulletin` `/bulletin/:id` | 公告列表/详情 |
| `/bulletin/create` | 发公告（Admin） |
| `/wiki` `/wiki/:id` | 知识库列表/文章 |
| `/knowledge/new` `/knowledge/:id/edit` | 新建/编辑文章 |
| `/users` `/users/:id` | 用户列表/公开资料 |

### 2.4 训练 / 赛事 / 做题

| 路径 | 说明 |
|------|------|
| `/training` `/training/:gameId` | 训练场 |
| `/games` | 赛事中心（`/ctf` 重定向至此） |
| `/games/:id` | 赛事详情 |
| `/games/:id/challenges` | 做题工作台 ChallengeWorkspace（需登录） |
| `/games/:id/scoreboard` | 排行榜 |
| `/games/:id/teams` (+ choose/create/join/:teamId) | 组队流（需登录） |
| `/games/:id/admin/*` | 全部重定向 → `/admin/ctf?game_id=...` |
| `/challenge/:id` | 单题详情页（需登录） |
| `/teams` `/submissions` | 队伍 / 提交记录（需登录） |
| `/competition/:id` `/scoreboard/:gameId` | 旧路径别名 |

### 2.5 管理后台 `/admin/*`（需 Admin）

| 子路径 | 模块 |
|--------|------|
| `/admin/dashboard` | 仪表盘 |
| `/admin/users` | 用户管理 |
| `/admin/content` | 内容管理 |
| `/admin/announcement` | 公告管理 |
| `/admin/carousel` | 轮播图 |
| `/admin/ctf` | 靶场/赛事管理 |
| `/admin/settings` | 系统设置 |
| `/admin/logs` | 日志审计 |
| `/admin/setup` | 首次引导（仅需登录） |
| 旧路径 `statistics/media/lifecycle/...` | 重定向到上表 |

---

## 3. 后端 API（按 Blueprint）

注册入口：`backend/app.py`（约 L412–447）

### 3.1 Auth — `/api/auth`

| 方法 | 路径 |
|------|------|
| POST | `register` `verify-email` `resend-verification` `forgot-password` `reset-password` `login` `logout` `change-password` `delete-account` |
| GET | `me` `users` `users/<id>` `oauth/providers` `oauth/<provider>` |
| PUT | `profile` |

### 3.2 Captcha / Health / Platform

| 前缀 | 接口 |
|------|------|
| `/api/captcha` | `GET /` · `POST /verify` |
| `/api/health` | `/` · `/live` · `/ready` |
| `/api/platform` | `info` · `version` · `bulletins` · `bulletins/<id>` · `training/sidebar` · `instances` |
| `/api/external/events` | 挂在 `app.py` 的代理 |

### 3.3 队伍 — `/api/teams`

`POST /` · `POST /join` · `GET /me|/|/<id>` · `PATCH /<id>` · `POST /<id>/leave`  
`GET /<id>/solves|/score-timeline` · Admin：`GET /admin` · `DELETE /admin|/<id>`

### 3.4 赛事双轨

| 模块 | 前缀 | 职责 |
|------|------|------|
| competitions | `/api/competitions` | **主路径**：列表/详情/join/leave/training-join/divisions；admin CRUD、stats、export-scoreboard、流量捕获 |
| ctf_api | `/api/ctf` | **仅保留** scoreboard(+timeline/user)、notices、health、cleanup；其余重叠路径 **410** |
| games | `/api/games` | **410 Gone**（整前缀下线） |

管理端重叠（已收敛）：

- `admin.py` 与 `ctf_admin.py` 曾同挂 `/api/admin` 且重复注册 `/games`、`/users`；现 `/api/admin/games`（含 stats/export）统一 410，`GET /users` 合并为单一分页+过滤实现。
- 赛事写操作 / 统计 / 导出唯一入口：`/api/competitions/admin/*`（前端 `services/admin/ctf.js`）。

### 3.5 题目 / 容器

| 模块 | 前缀 | 关键动作 |
|------|------|----------|
| challenges | `/api/challenges` | **主路径**：列表、详情、submit、hints、hammer、stats、container-status/start、instances stop/extend/logs |
| container | `/api/container` | **兼容别名（弃用中）**：start/stop/status/instance/extend/submit-flag；另含 debug、test-flag-generation；proxy 已 410 |
| resources | `/api/resources` | `<id>` · `<id>/content` |

#### 容器 API 弃用策略

- **选手前端**统一经 `frontend/src/services/container.js`：优先 `/api/challenges/*`，失败时回退 `/api/container/*`。
- `/api/container/*` 响应带 `Deprecation` / `Warning` 头；新功能只加在 `/api/challenges`。
- `test-flag-generation` 仅 DEBUG+admin，且**不回传明文 Flag**（只返回长度与占位符诊断）。
- 生产环境：`REDIS_ENABLED` 且连不上时默认 **拒绝启动**（`NEPU_REQUIRE_REDIS=0` 可覆盖，不推荐）。

### 3.6 内容 / 上传

| 前缀 | 接口 |
|------|------|
| `/api/articles` | wiki-nav、carousel、announcements、CRUD、`wiki/<slug>` |
| `/api/uploads` | `POST /` · `POST /upload-image/` · `GET /serve/<path>` |
| `/api/attachments` | article/carousel 附件 CRUD |
| `/api/tokens` | token CRUD |

### 3.7 管理端

| 前缀 | 覆盖面 |
|------|--------|
| `/api/admin`（admin.py + ctf_admin.py） | 用户/赛事、cheat、first-solves、hammer、seasons、export、moderator（存在路由重叠） |
| `/api/admin/challenges` | 分类与题目 CRUD、附件 |
| `/api/admin/platform` | dashboard、users、env、config、articles、logs、announcements、carousel、stats |
| `/api/admin/platform/files` | 文件列表/统计/清理 |
| `/api/admin/dynamic-packages` | 动态附件包 CRUD/下载 |

## 4. 相关源文件

| 角色 | 路径 |
|------|------|
| 前端路由 | `frontend/src/router/index.js` |
| Admin 菜单 | `frontend/src/config/adminMenu.js` |
| Blueprint 注册 | `backend/app.py` |
| 路由模块 | `backend/route/*.py` |
| 前端 API 封装 | `frontend/src/services/`（容器：`container.js`） |
