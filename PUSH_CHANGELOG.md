# 推送变更记录

本文件记录每次推送到 GitHub 仓库的改动摘要（不含密钥、隐私信息）。  
**约定：** 每次 push 前在顶部新增一节；改接口/页面时同步更新 `docs/功能说明书.md`。

---

## 2026-09-21 — 题型 4（附件+动态容器）、移除动态附件包、题目交付校验

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`、`origin`  
**分支：** `main`

### 变更摘要

- **管理端题型：** 新增 `challenge_type=4`「附件 + 动态容器（PWN）」；静态附件与容器互斥校验（纯附件题不带 Docker；容器题可挂附件）。
- **下线动态附件：** 拒绝 `type=2`；删除 `DynamicPackageManager` 与 dynamic-packages 前端 API。
- **后端：** `challenge_admin` 创建/更新/上传附件校验；容器链路识别 type 4。
- **脚本：** `backend/scripts/test_challenge_type4.py` 冒烟（登录、type4 CRUD、附件、列表、启容器等）。

### 验证

- `python backend/scripts/test_challenge_type4.py`（需本地 Flask + MySQL；启容器项需 Docker 可用）

---

## 2026-09-21 — 赛内通知、校徽、按赛队伍、首页推荐赛

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`、`origin`  
**分支：** `main`

### 变更摘要

- **#12 赛内通知：** 题目页右侧 `GameNoticesRail`，`GET /api/competitions/{id}/notices`。
- **#20 校徽：** 全局 `HiddenSchoolEmblem`（`/assets/neepu-emblem.jpg`）。
- **#18 按赛事队伍：** `Team.game_id` + `team_service` 按赛隔离；创建/加入/报名带 `game_id`。
- **#14 首页推荐赛：** `SystemConfig.home_featured_game_id`，管理端系统设置可选；Home Hero 优先展示。
- 内测文档 `NEEPU-SEC 内测系统.md` 已写全量问题答复（本地，不推送）。

### 验证

- `python -m pytest backend/tests/test_fixes.py -v`
- `cd frontend && npm run build`

---

## 2026-09-21 — NEEPU-SEC 内测问题修复（Wiki / 资料 / 内容管理 / 赛事日历等）

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`、`origin`  
**分支：** `main`

### 变更摘要

- **Wiki**：内链改为 `/wiki/{slug}`；启动时 `repair_wiki_internal_links()`；`ArticleView` 支持 slug 与统一响应解包。
- **个人资料**：`ProfileEdit` 提交用户名；维护模式放行 `/api/auth/profile`、`/me`；`MyProfile` 拉取 `/api/auth/users/:id` 展示参赛/队伍。
- **内容管理**：管理端列表支持 `search`；分页切换触发加载；`ArticleEdit` 使用 `content`；发布页 Cookie 会话；发布/编辑后失效文章缓存。
- **赛事与首页**：近期赛事来自 API；国内/国际日历与 agenda 区域一致；外链 agenda 跳转 `/events`；未报名进题目页重定向队伍页；`/competition/:id` 先进概览。
- **访问**：`/home` 与训练场浏览对未登录用户开放（做题/提交仍须登录）。
- **容器**：默认存活 1h（`NEEPU_CONTAINER_EXPIRE_HOURS`，上限 4）。
- **登录**：`allow_registration=false` 时隐藏注册 Tab（管理员在系统设置关闭）。

### 未在本轮实现（需产品确认）

- 比赛页右侧通知栏、全局旋转校徽、跨赛事独立队伍（当前模型为单用户全局 `team_id`）。
- 系统重置/备份：见 `docs/deploy-single-server.md` 运维章节。
- 工作台终端：演示用白名单命令，非真实 shell。

### 涉及文件（主要）

- 后端：`platform_admin.py`、`platform_seed.py`、`maintenance_service.py`、`auth.py`、`container_expire.py`、`container_service.py`、`container_start_queue.py`、`challenges.py`、`ctf_api.py`
- 前端：`ArticleView.vue`、`ArticleEdit.vue`、`ArticleUpload.vue`、`ContentManagement.vue`、`ProfileEdit.vue`、`MyProfile.vue`、`Home.vue`、`Events.vue`、`GameChallenges.vue`、`Auth.vue`、`App.vue`、`router/index.js`、`SystemSettings.vue`

### 验证

- `python -m pytest backend/tests/test_fixes.py -v`（8 passed）
- `cd frontend && npm run build`

---

## 2026-09-17 — 项目约定改为本地文档

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`、`origin`  
**分支：** `main`

### 变更摘要

- **`项目约定.md`** 从仓库移除，加入 `.gitignore`，仅保留在本地供 Cursor / 维护者使用。
- **`README.md`** 去掉对项目约定的公开链接。

### 涉及文件

- `.gitignore`
- `README.md`
- `PUSH_CHANGELOG.md`（本条目）
- `项目约定.md`（自 Git 跟踪中移除，本地文件保留）

---

## 2026-09-17 — 功能说明书与项目约定

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`  
**分支：** `main`

### 变更摘要

- 新增 **`docs/功能说明书.md`**：全项目功能域说明，细化到「文件 → 函数」，含统计汇总与使用说明。
- 新增 **`项目约定.md`**：规定「先读文档再开发」、文档与代码同步、推送流程与安全清单。
- 更新 **`AGENT.md`**：前置必读增加 `项目约定.md`、`功能说明书.md`、`PUSH_CHANGELOG.md`；完成后须同步文档。

### 涉及文件

- `docs/功能说明书.md`（新增）
- `项目约定.md`（新增）
- `AGENT.md`（更新前置工作流）
- `PUSH_CHANGELOG.md`（本条目）

### 验证提示

- 文档只读，无需重启服务。
- 后续任何功能改动请按 `项目约定.md` § 四 同步更新功能说明书与本文件。

---

## 2026-09-17 — 修复 Flag 提交 / 动态 Flag / 容器地址 / 注册

**推送目标仓库：** `https://github.com/Aln1lam/nee3.git`  
**分支：** `main`

### 问题与修复

| 问题 | 原因 | 修改 |
|------|------|------|
| Flag 提交提示比赛未开始 | 开始时间 UTC 被二次减 8 小时；`status` 长期停在 `not_started` | 新增 `backend/server/time_utils.py`；提交时与定时任务自动 `not_started` → `ongoing` |
| 动态 Flag 固定为 `734M_HaSH` | 模板 `{{{team_hash}}}` 未识别，被 Leet 转换 | `flag_generator.py` 增加 `normalize_flag_template()` |
| 多题容器地址相同 | 流量捕获代理端口存在 `tcpdump_pid`，归一化却用 `instance.port` | `container_access.py` 优先使用代理端口 |
| 注册失效 | 维护模式拦截 `/api/auth/register`；注册路由未切 Tab | 维护白名单补充注册相关 API；`Auth.vue` 支持 `?mode=register` |

### 涉及文件

**后端**

- `backend/server/time_utils.py`（新增）
- `backend/server/container_access.py`
- `backend/route/challenges.py`
- `backend/route/competitions.py`
- `backend/route/container_challenges.py`
- `backend/services/flag_generator.py`
- `backend/services/scoring_service.py`
- `backend/services/scheduler.py`
- `backend/services/container_service.py`
- `backend/services/maintenance_service.py`
- `backend/tests/test_fixes.py`（新增）

**前端**

- `frontend/src/components/Auth.vue`

**仓库**

- `.gitignore` — 排除本地 zip、临时脚本等
- `PUSH_CHANGELOG.md` — 本文件

### 部署提示

- 重启后端使 scheduler 生效。
- 若数据库中比赛开始时间为旧版本地 naive 时间，可在环境变量设置 `NEPU_START_TIME_LEGACY_LOCAL=1`。
- 已开容器若地址异常，销毁后重新启动。

### 未纳入本次推送（刻意排除）

- `.env` 及一切含密钥/口令的文件
- `neepu.zip`、本地临时脚本 `scripts/_*.py`
- 重复目录 `neepu/`（与根目录代码重复，仅本地备份）
