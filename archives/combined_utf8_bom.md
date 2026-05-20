# Combined Documentation

Generated: 2026-05-20T16:35:19.3133512+08:00

## Source: docs\index.md

# neepu 项目知识库

欢迎使用本仓库生成的知识库。文档包括：项目概览、后端与前端结构、路由与服务详细说明、开发运行指南与常见问题。

快速开始：

- 在本地查看（推荐使用 MkDocs + Material 主题）：参见仓库根目录的 `mkdocs.yml`。
- 文档主页位于本目录下的各个 Markdown 文件，例如 `overview.md`、`backend.md`、`routes.md` 等。

若需在本地构建站点，请参见仓库根目录的 `build_docs.ps1`（或使用 `mkdocs` 命令）。

目录导航：参见站点侧边栏（已由 `mkdocs.yml` 配置）。


---

## Source: docs\overview.md

# 概览

项目根目录主要内容：

- `backend/`：后端服务与路由实现（Flask / FastAPI 风格结构）。
- `frontend/`：基于 Vite 的前端界面，包含 `src/`、`public/` 等。
- `captures/`：网络流量抓包（PCAP）示例数据，按挑战/团队组织。
- `GZCTF-develop/`：竞赛或平台相关资源与说明。
- `scripts/`：运维或查询脚本（如 `query_db.py`）。

快速阅读路径：

- 后端入口与配置：查看 `backend/app.py` 与 `backend/server/config.py`。
- 路由实现：查看 `backend/route/` 下的各模块（如 `challenges.py`、`auth.py`）。
- 服务层：`backend/server/services/` 下的多个服务（容器、评分、调度等）。


---

## Source: docs\backend.md

# 后端（模块概览）

主要目录与文件：

- `backend/app.py`：应用入口（启动配置与扩展初始化）。
- `backend/route/`：路由层，按功能划分（认证、挑战、队伍等）。
- `backend/server/`：平台级服务与配置（`config.py`、`db_models.py`、`extensions.py` 等）。
- `backend/services/`：业务服务实现（容器管理、评分、调度等）。

定位路由实现：

- 路由文件位于 [backend/route](backend/route)。常见模块：`challenges.py`、`auth.py`、`uploads.py`、`teams.py` 等。

日志与中间件：

- 中间件实现分为 `middleware/` 与 `middleware_refactored/`，用于缓存、压缩、限流与安全处理。

建议阅读顺序：

1. `backend/app.py`（启动流程）
2. `backend/server/extensions.py`（扩展注册）
3. `backend/route/*.py`（功能路由）
4. `backend/server/services/`（核心业务逻辑）


---

## Source: docs\frontend.md

# 前端（模块概览与运行）

项目前端位于 `frontend/`，基于 Vite：

- 入口：`frontend/index.html`。
- 源代码：`frontend/src/`（`App.vue`、路由、组件、服务等）。
- 依赖与脚本：`frontend/package.json`。

本地启动（常见）：

```bash
cd frontend
npm install
npm run dev
```

构建生产包：

```bash
npm run build
```


---

## Source: docs\development.md

# 开发环境与运行指南

建议的本地开发步骤（Python 后端）：

1. 创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖：如果仓库含 `requirements.txt` 或 `pyproject.toml`，请按文件安装；否则查看 `backend/` 下文档或源码声明的依赖。

3. 启动后端：查看 `backend/app.py` 以获取运行方式（WSGI/ASGI）。常见命令示例：

```powershell
python backend/app.py
# 或 使用 uvicorn/gunicorn 启动（如果为 ASGI）
```

4. 启动前端：参见 `docs/frontend.md`。

测试：

```bash
pip install pytest
pytest -q
```

注意：在执行数据库相关操作前，确认配置文件 `backend/server/config.py` 中的连接信息。


---

## Source: docs\routes.md

# 路由索引（概要）

路由实现集中在 `backend/route/`，文件按功能分组，下面列出仓库中常见的路由模块及职责：

- `admin.py`：平台管理相关接口。
- `articles.py`：文章/公告接口。
- `attachments.py`：附件管理。
- `auth.py`：认证、登录、会话。
- `challenges.py`：挑战列表、详情、提交逻辑（当前编辑文件）。
- `container_challenges.py`：基于容器的挑战接口。
- `ctf_api.py`、`ctf_admin.py`：赛事实时接口与管理。
- `teams.py`：队伍相关操作。
- `uploads.py`：上传处理。

查找某路由的实现细节：在对应文件中搜索路由装饰器（如 `@app.route`、`@bp.route` 或框架对应标记）。

## 路由文件清单（已扫描）

- [backend/route/challenges.py](backend/route/challenges.py): 题目相关路由；包含获取题目列表、题目详情、提交 Flag、排行榜、提示系统、作弊检测、容器实例管理（启动/停止/延时/状态）、题目统计等。关键端点示例：
	- `GET /games/<game_id>/challenges`：获取竞赛题目列表
	- `GET /<challenge_id>`：题目详情
	- `POST /<challenge_id>/submit`：提交 Flag（含动态分数、血液奖励、作弊检测）
	- `POST /<challenge_id>/start-container`：启动题目容器
	- `GET /games/<game_id>/scoreboard`：获取排行榜

- [backend/route/container_challenges.py](backend/route/container_challenges.py): 面向容器的题目特殊接口（与 `challenges.py` 互补）。
- [backend/route/auth.py](backend/route/auth.py): 认证、登录、JWT 相关接口。
- [backend/route/teams.py](backend/route/teams.py): 队伍创建/管理/成员邀请接口。
- [backend/route/uploads.py](backend/route/uploads.py): 文件上传与附件处理。
- [backend/route/ctf_api.py](backend/route/ctf_api.py): 比赛实时 API 接口（面向前端的汇总与实时数据）。
- [backend/route/ctf_admin.py](backend/route/ctf_admin.py): 比赛管理与管理员操作接口。
- [backend/route/admin.py](backend/route/admin.py): 平台级管理接口。
- [backend/route/articles.py](backend/route/articles.py): 公告与文章管理。
- [backend/route/attachments.py](backend/route/attachments.py): 附件存取接口。
- [backend/route/file_management.py](backend/route/file_management.py): 文件管理工具接口。
- [backend/route/games.py](backend/route/games.py): 与竞赛/赛季相关的接口。
- [backend/route/competitions.py](backend/route/competitions.py): 竞赛配置与列表。
- [backend/route/challenge_admin.py](backend/route/challenge_admin.py): 题目管理（创建/编辑/导入）。
- [backend/route/platform_admin.py](backend/route/platform_admin.py): 平台设置与管理员工具。
- [backend/route/resources.py](backend/route/resources.py): 静态资源或外部资源代理。
- [backend/route/tokens.py](backend/route/tokens.py): Token/凭证相关接口。
- [backend/route/todos.py](backend/route/todos.py): 待办/任务接口（内部使用）。

注：上面链接指向具体文件，后续可逐个提取每个路由函数的参数、权限要求与返回示例以补全文档。


---

## Source: docs\routes\admin.md

# 路由详解：`backend/route/admin.py`

功能：平台级管理接口，包含用户管理、审计日志、系统配置等。

关键端点（示例）：
- `GET /admin/users`：用户列表
- `POST /admin/config`：系统配置更新

注意：操作权限严格，仅管理员可执行。


---

## Source: docs\routes\articles.md

# 路由详解：`backend/route/articles.py`

功能：公告、文章与比赛通知的创建、编辑、发布与获取接口。

关键端点：
- `GET /articles`：文章列表
- `POST /articles`：管理员发布公告


---

## Source: docs\routes\attachments.md

# 路由详解：`backend/route/attachments.py`

功能：附件上传与管理，通常配合文章/题目附带文件的上传与访问控制。

关键点：附件可存储在 `static/uploads/`，应考虑权限与有效期清理。


---

## Source: docs\routes\auth.md

# 路由详解：`backend/route/auth.py`

功能：认证与会话管理，包含注册、登录、登出、JWT 刷新、密码重置等接口。

关键端点（示例）：
- `POST /auth/login`：用户登录，返回 JWT。
- `POST /auth/register`：用户注册。
- `POST /auth/refresh`：刷新访问令牌（需要 refresh token）。

鉴权要点：敏感操作返回和密码处理遵循安全最佳实践（哈希、速率限制、邮箱验证）。


---

## Source: docs\routes\challenge_admin.md

# 路由详解：`backend/route/challenge_admin.py`

功能：题目编写与管理接口，支持题目创建、编辑、导入导出与测试用例管理。

关键点：管理员接口，可能包含文件上传（附件/附件镜像）与题目验证流程。


---

## Source: docs\routes\challenges.md

# 路由详解：`backend/route/challenges.py`

概述：此模块实现与 CTF 题目相关的所有 API，包含题目列表/详情、提交 Flag、排行榜、提示系统、作弊检测、容器实例管理与题目统计等核心功能。

主要端点（摘要）：

- `GET /games/<game_id>/challenges`
  - 鉴权：公开
  - 描述：返回指定竞赛的题目列表（仅启用的题目）。
  - 返回：{ code, msg, data: [challenge] }

- `GET /<challenge_id>`
  - 鉴权：`@jwt_required()`
  - 描述：获取题目详情并附带当前用户的提交记录与是否已解。
  - 返回：{ code, msg, data: { challenge, submissions, submission_count, is_solved } }

- `POST /<challenge_id>/submit`
  - 鉴权：`@jwt_required()`
  - 描述：提交 Flag；实现包括答案校验、动态分数计算、血液奖励（首解/二解/三解）、作弊检测、排分更新、赛季统计触发与容器销毁（正确时）。
  - 请求体：{ answer: string }
  - 常见返回：正确时返回最终得分、血液等级、加成倍数；错误时返回相应错误码与消息。

- `GET /games/<game_id>/scoreboard`
  - 鉴权：公开
  - 描述：获取比赛实时排行榜（由 `ScoringService.calculate_rankings` 计算）。

- `GET /games/<game_id>/first-solves`
  - 鉴权：公开
  - 描述：获取首解/二解/三解记录。

- `GET /<challenge_id>/hints`
  - 鉴权：`@jwt_required()`
  - 描述：获取题目的提示列表，并标注当前用户已访问的提示。

- `POST /<hint_id>/access-hint`
  - 鉴权：`@jwt_required()`
  - 描述：记录用户查看提示的行为；如果提示配置了扣分，会更新排行榜分数。

- `GET /games/<game_id>/cheat-info`
  - 鉴权：`@jwt_required()`（需管理员权限）
  - 描述：管理员获取作弊检测信息（`CtfCheatInfo` 记录）。

- 容器/实例管理端点：
  - `GET /<challenge_id>/container-status`：查询用户该题目的容器状态（no_container/running/expired）。
  - `POST /<challenge_id>/start-container`：启动题目容器（集成 `container_service.create_container` 与流量捕获）。
  - `POST /<challenge_id>/start-instance`：为动态题目创建实例记录（1小时到期，支持流量捕获）。
  - `POST /instances/<instance_id>/stop`：用户手动停止/销毁容器实例（权限校验）。
  - `POST /instances/<instance_id>/extend`：延时容器过期时间（每次 +1 小时）。
  - `GET /instances/<instance_id>/status`：获取容器实例状态与剩余时间。

- `GET /<challenge_id>/stats`
  - 鉴权：公开
  - 描述：返回题目统计（唯一解题人数、总提交数、通过率、首解信息）。

实现要点与注意事项：

- 权限检查：大多数用户操作需要 `@jwt_required()`。管理员接口会进一步检查 `user.is_admin`。
- 提交限速与次数控制由题目属性（`submission_limit`）与 `CtfChallengeSubmission` 计数实现。
- 动态分数与血液奖励由 `ScoringService` 提供，具体算法见 `backend/services/scoring_service.py`。
- 作弊检测调用 `CheatDetectionService.detect_similar_flags`，如发现相似提交会写入 `CtfCheatInfo`。
- 容器操作依赖本地 Docker：`container_service` 在 `backend/services/container_service.py` 中提供创建/销毁/查询等接口；启动容器时会在后台启动流量捕获代理（若启用），并更新实例的 `connection_url`。
- 数据库模型（如 `CtfGameInstance`, `CtfChallengeSubmission` 等）定义在 `backend/server/db_models.py`，文档中引用了 `.to_dict()` 方法用于序列化响应。

建议：可将本文件中的每个端点复制到独立的 Markdown 条目中，补充示例请求/响应与错误码表，便于前端和测试人员使用。


---

## Source: docs\routes\competitions.md

# 路由详解：`backend/route/competitions.py`

功能：竞赛集合与分组管理，提供竞赛筛选、搜索与批量操作接口。


---

## Source: docs\routes\container_challenges.md

# 路由详解：`backend/route/container_challenges.py`

功能：容器化题目的专用接口，通常负责容器镜像、网络隔离、题目实例生命周期的高级操作。

关键端点（示例）：
- 启动/停止容器实例，查看容器日志/端口映射，管理网络策略。

实现要点：配合 `backend/services/container_service.py` 使用；注意 Docker 权限与主机资源限制。


---

## Source: docs\routes\ctf_admin.md

# 路由详解：`backend/route/ctf_admin.py`

功能：比赛管理接口（管理员权限），包含比赛创建、阶段控制、题目批量导入与赛程管理。

关键点：仅管理员可访问；操作会触发 `scheduler` 与 `season_stats_service` 的相应任务更新。


---

## Source: docs\routes\ctf_api.md

# 路由详解：`backend/route/ctf_api.py`

功能：面向前端的比赛实时数据接口，通常提供赛况、排行榜、题目汇总与活动通知。

关键端点：
- `GET /api/games/<id>/overview`：比赛概览数据
- `GET /api/games/<id>/live`：实时事件流


---

## Source: docs\routes\file_management.md

# 路由详解：`backend/route/file_management.py`

功能：文件与资源的管理工具接口，包含批量导入/导出、备份与清理任务。

关键点：通常仅管理员可访问；涉及磁盘操作请注意并发与权限。


---

## Source: docs\routes\games.md

# 路由详解：`backend/route/games.py`

功能：管理比赛/赛季的接口，包含比赛列表、详情及元数据。

示例端点：`GET /games`、`GET /games/<id>`、`POST /games`（管理员）。


---

## Source: docs\routes\platform_admin.md

# 路由详解：`backend/route/platform_admin.py`

功能：平台设置、系统监控、管理员工具集合（用户、队伍、系统参数）。

仅管理员可用。


---

## Source: docs\routes\resources.md

# 路由详解：`backend/route/resources.py`

功能：外部资源或静态资源代理接口，可能用于第三方服务代理、内嵌资源访问控制。


---

## Source: docs\routes\resources_overview.md

# 资源接口说明

更多细节请查看 `backend/route/resources.py`，包括外部 API 代理、安全限制与缓存策略。


---

## Source: docs\routes\teams.md

# 路由详解：`backend/route/teams.py`

功能：队伍创建、加入、邀请、成员管理与队伍配置接口。

关键端点（示例）：
- `POST /teams`：创建队伍
- `POST /teams/<id>/invite`：邀请成员
- `GET /teams/<id>`：获取队伍信息与成员列表

注意权限：加入/修改队伍通常需要验证用户身份与邀请码校验。


---

## Source: docs\routes\teams_overview.md

# 说明：团队接口快速参考

请参阅 `backend/route/teams.py` 获取完整实现。文档主要覆盖：队伍生命周期、邀请流程、权限边界与常见错误码。


---

## Source: docs\routes\todos.md

# 路由详解：`backend/route/todos.py`

功能：内部任务/待办项目接口，通常用于运维或后台任务控制面板。


---

## Source: docs\routes\tokens.md

# 路由详解：`backend/route/tokens.py`

功能：Token/凭证管理接口，包含生成/验证/吊销等操作（用于队伍邀请码、API 访问令牌等）。


---

## Source: docs\routes\uploads.md

# 路由详解：`backend/route/uploads.py`

功能：处理前端上传文件、附件存储、访问权限与文件清理。

关键端点（示例）：
- `POST /uploads`：上传文件（表单/多部分）
- `GET /uploads/<id>`：下载或预览文件

存储注意：文件保存路径为 `static/uploads/`，应限制上传大小和类型检查。


---

## Source: docs\services\cheat_detection_service.md

# 服务详解：`backend/services/cheat_detection_service.py`

职责：检测重复/相似提交、快速提交、IP 异常，生成作弊报告并写入 `CtfCheatInfo`。

主要方法：`calculate_similarity`, `detect_duplicate_submission`, `detect_similar_submission`, `detect_rapid_submission`, `detect_ip_pattern`, `create_cheat_record`, `get_cheat_report`。

提示：可根据比赛策略调整阈值（相似度、时间窗口等）。


---

## Source: docs\services\container_service.md

# 服务详解：`backend/services/container_service.py`

职责：与 Docker 交互，创建/销毁容器、查询状态、获取日志、清理过期实例、续期等。

主要方法：`create_container`, `destroy_container`, `get_container_status`, `cleanup_expired_containers`, `list_user_containers`, `renew_container_lease`, `get_container_logs`。

注意：生产环境需确保 Docker 权限、安全网络与资源配额；建议对 `create_container` 做限流与配额校验。


---

## Source: docs\services\flag_generator.md

# 服务详解：`backend/services/flag_generator.py`

职责：解析 Flag 模板并生成动态 Flag，支持 `[GUID]`, `[TEAM_HASH]`, `[LEET]`, `[CLEET]` 等占位符与 Leet 转换。

主要类：`DynamicFlagGenerator`, `ContainerFlagService`。

示例：使用 `ContainerFlagService.generate_dynamic_flag(template, challenge_id, user_id, game_id)`。


---

## Source: docs\services\invite_code_service.md

# 服务详解：`backend/services/invite_code_service.py`

职责：生成、分发与校验邀请码，用于控制比赛或队伍加入权限。

接口通常包括：`generate_code`, `validate_code`, `revoke_code`。


---

## Source: docs\services\permission_service.md

# 服务详解：`backend/services/permission_service.py`

职责：检查用户在比赛/题目/队伍上的权限，通常封装为 `check_game_permission`, `has_submission_permission`, `has_container_permission` 等。

注意：实际权限细节可能分散在多个文件（`scoring_service.py` 中也包含 `PermissionService`）。


---

## Source: docs\services\redis_service.md

# 服务详解：`backend/services/redis_service.py`

职责：Redis 连接管理、缓存 API（get/set/json）、排行榜与题目缓存、通知队列、缓存装饰器 `cache_result`。

主要类/函数：`RedisService`, `ScoreboardCache`, `ChallengeCache`, `UserSessionCache`, `NotificationQueue`, `initialize_redis`。

注意：需根据环境进行 `initialize_redis(host, port)`，并在应用启动时创建全局实例。


---

## Source: docs\services\scheduler.md

# 服务详解：`backend/services/scheduler.py`

职责：定时任务与比赛阶段调度，例如开始/结束比赛、清理过期容器、生成日常报表等。

通常与系统 cron 或 `APScheduler` 集成。


---

## Source: docs\services\scoring_service.md

# 服务详解：`backend/services/scoring_service.py`

主要类与职责：
- `ScoringService`：动态分数计算、血液奖励、记录首解、更新排行榜、计算排名。
  - 关键方法：`calculate_dynamic_score`, `calculate_blood_bonus`, `record_first_solve`, `update_scoreboard`, `calculate_rankings`。
- `CheatDetectionService`：辅助的作弊检测（字符串相似度、检测相似 Flags）。
- `FlagTemplateService`：根据模板生成动态 Flag。
- `PermissionService` / `FlagValidationService`：权限与 Flag 验证逻辑。

建议：接口已在 `backend/route/challenges.py` 被频繁使用；如需单元测试，可针对 `calculate_dynamic_score` 和 `detect_similar_flags` 编写测试用例。


---

## Source: docs\services\season_stats_service.md

# 服务详解：`backend/services/season_stats_service.py`

职责：赛季统计聚合与触发器（如题目解决触发统计更新）。

常见用途：在 `ScoringService` 成功记录解题后调用以更新赛季排名与汇总数据。


---

## Source: docs\faq.md

# 常见问题（快速回答）

Q: 我如何运行项目？

A: 启动前端：`cd frontend && npm install && npm run dev`。后端：参阅 `backend/app.py`，通常使用虚拟环境运行 Python 程序或通过 ASGI/WSGI 服务器运行。

Q: 我如何定位接口实现？

A: 在 `backend/route/` 下按模块查找。路由通常使用框架装饰器注册。

Q: 测试如何运行？

A: 运行 `pytest`（如仓库包含测试文件）。

Q: 捕获文件（PCAP）在哪？

A: 在 `captures/` 目录下，按挑战与队伍编号分类。

Q: 我想扩展服务或新增路由，在哪里注册？

A: 在 `backend/server/` 下查找扩展注册点（`extensions.py` 或 `app.py`）。


---

