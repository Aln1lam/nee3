# NEEPU CTF · AGENT.md

> 本文件约束所有 AI Agent（Cursor / Claude / 其他）在本仓库中的开发、重构、Code Review 与 Bug 排查行为。  
> **规则优先于通用最佳实践**：与本文冲突时，以本文与 `docs/` 下专项文档为准。

---

## 0. Agent 强制前置读物

动手改代码前，按任务类型至少阅读对应文档：

| 任务类型 | 必读 |
|----------|------|
| 任意改动 | 本文 `AGENT.md` |
| 路由 / API / 页面映射 | `docs/route-architecture-topology.md` |
| 前端 UI / 视觉 | `docs/ui-style.md` + `.cursor/skills/neepu-anime-ui/SKILL.md` |
| 前端工程验收 | `docs/frontend-ui-harness.md` |
| API↔前端对接 | `docs/api-frontend-checklist.md` |
| 生产部署相关 | `docs/deploy-single-server.md` |

**UI 规范优先级**：改前端视觉时只认 `docs/ui-style.md` + `Home.vue` 锚点；**禁止**引用已废弃的 `neepu-anime-ui`。

---

## 1. 项目概要与技术栈映射

### 1.1 产品定位

高校 CTF 竞赛 / 训练 / 知识库 / 运维后台平台（东北电力大学 NEEPU）。  
核心能力：题目与比赛、动态 Flag、Docker 容器题调度、JWT Cookie 鉴权、Redis 限流与提交锁、排行榜与作弊检测。

### 1.2 技术栈（以仓库文件为准）

| 层 | 技术 | 版本 / 来源 |
|----|------|-------------|
| 后端 | Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-JWT-Extended + Flask-CORS | `requirements.txt`（Flask ≥3.0） |
| ORM / DB | SQLAlchemy ≥2.0、PyMySQL ≥1.1（默认 MySQL；可用 `NEPU_DATABASE_URL` 切 SQLite） | `backend/server/config.py` |
| 缓存 / 限流 | redis ≥5.0；Compose 镜像 `redis:7-alpine` | `requirements.txt`、`docker-compose.yml` |
| 容器 | docker SDK ≥7.0；APScheduler ≥3.10 | `backend/services/container_service.py`、`scheduler.py` |
| 生产 WSGI | gunicorn ≥22.0 | `deploy/gunicorn.conf.py` |
| 前端 | Vue ^3.3.4、Vue Router ^4.6.3、Vite ^5.2.0、axios ^1.13.2、naive-ui ^2.43.2 | `frontend/package.json` |
| Markdown / XSS | marked ^17、DOMPurify ^3.4、vditor、highlight.js | `frontend/src/utils/markdown.js` |
| E2E | Playwright ^1.61.1 | `e2e/package.json` |
| 单测 | pytest | `tests/` |

> `docker-compose.yml` **仅启动 Redis**（绑定 `127.0.0.1:6379`）。MySQL / API / 前端不在 compose 内。

### 1.3 核心目录（真实路径）

```
neepu/
├── backend/
│   ├── app.py                      # create_app() 入口、CORS、JWT Cookie、中间件、Blueprint 注册
│   ├── route/                      # HTTP 路由（Controller 层）
│   ├── services/                   # 业务服务（Flag / Docker / Redis / 计分 / 锁）
│   ├── server/                     # config、extensions、db_models、安全辅助
│   ├── middleware_refactored/      # 限流、缓存、安全头、压缩、日志
│   └── scripts/                    # 冒烟 / 生命周期 e2e 脚本
├── frontend/
│   ├── src/router/index.js         # 前端路由（requiresAuth / requiresAdmin）
│   ├── src/services/               # API 客户端层（禁止页面内散落 axios）
│   ├── src/utils/http.js           # authFetch / parseJsonResponse / isApiSuccess
│   ├── src/utils/markdown.js       # marked + DOMPurify
│   ├── src/stores/                 # 轻量模块 store（非 Pinia）
│   └── public/themes/              # light.css / dark.css
├── tests/                          # pytest
├── e2e/                            # Playwright
├── docker_templates/               # 容器题镜像模板
├── deploy/                         # Nginx / systemd / Gunicorn 模板
├── scripts/                        # 运维脚本
├── docs/                           # 架构与 UI 文档
├── captures/、instance/            # 运行时数据（不入库）
├── .env                            # 密钥（禁止提交、禁止写入回复）
└── docker-compose.yml
```

### 1.4 后端 Blueprint 前缀

| 前缀 | 文件 |
|------|------|
| `/api/auth` | `backend/route/auth.py` |
| `/api/challenges` | `backend/route/challenges.py` |
| `/api/ctf` | `backend/route/ctf_api.py` |
| `/api/container` | `backend/route/container_challenges.py` |
| `/api/competitions` | `backend/route/competitions.py` |
| `/api/teams` | `backend/route/teams.py` |
| `/api/games` | `backend/route/games.py` |
| `/api/admin` | `backend/route/admin.py` |
| `/api/admin/platform` | `backend/route/platform_admin.py`、`file_management.py` |
| `/api/admin/challenges` | `backend/route/challenge_admin.py` |
| `/api/admin/dynamic-packages` | `backend/route/dynamic_packages.py` |
| `/api/uploads` | `backend/route/uploads.py` |
| `/api/articles` | `backend/route/articles.py` |
| `/api/platform` | `backend/route/platform.py` |
| `/api/captcha` | `backend/route/captcha.py` |
| `/api/health` | `backend/route/health.py` |

**双轨 API 警告**：`/api/challenges`、`/api/ctf`、`/api/container` 行为不完全一致。新增或修改接口前必须对照 `docs/route-architecture-topology.md`，禁止 silently 只改一条轨导致前后端分裂。

---

## 2. 代码风格与命名规范

### 2.1 后端（Python）

- 包路径：`backend.route.*`、`backend.services.*`、`backend.server.*`、`backend.middleware_refactored.*`
- Blueprint：`bp = Blueprint("name", __name__)`，在 `backend/app.py` 的 `create_app()` 中统一 `register_blueprint`
- 模型：集中在 `backend/server/db_models.py`；表名 snake_case（如 `ctf_challenge`）；CTF 业务模型用 `Ctf*` 前缀
- 服务类：`XxxService`（例：`FlagValidationService`、`ContainerService`）
- 环境变量：`NEPU_*`、`REDIS_*`、`MAIL_*`、`CONTAINER_*`、`PCAP_*`
- JWT Cookie 名：`neepu_token`（勿改名，除非同步改前后端与文档）
- Redis key 约定：`ratelimit:*`、`neepu:submit:lock:*` 等现有前缀；禁止随意发明无前缀 key
- API JSON 习惯：`{"code": 200|0|4xx|5xx, "msg": "...", "data": ...}`；前端用 `isApiSuccess` 兼容 `code === 200 || code === 0`
- Schema 演进：仓库内**无**完整 `migrations/` 目录；列变更需同步考虑 `backend/app.py` 中 `_ensure_columns()` 的 `ALTER TABLE` 逻辑，并注明风险
- 禁止在 route 文件顶部做重量级副作用（启动 Docker 客户端、连 Redis 写全局）；复用 `extensions` / `services` 懒加载模式

### 2.2 前端（Vue / JS）

- 页面组件：`PascalCase.vue`，放在 `frontend/src/components/`（含 `admin/`、`shared/`、`ui/`）
- API 调用：只通过 `frontend/src/services/*.js` 与 `frontend/src/services/admin/*.js`
- HTTP 工具：Cookie 会话用 `frontend/src/utils/http.js` 的 `authFetch`（`credentials: 'include'`）；axios 实例须 `withCredentials: true`
- 状态：使用现有 `frontend/src/stores/` 与 `services/auth.js` 模块缓存；**不要引入 Pinia/Vuex**，除非任务明确要求并更新文档
- 路由守卫：鉴权页设 `meta.requiresAuth`；管理页设 `meta.requiresAdmin`（见 `frontend/src/router/index.js`、`frontend/src/config/adminMenu.js`）
- 主题：改颜色写 CSS 变量到 `frontend/public/themes/light.css` / `dark.css`，经 `html[data-theme]` 切换
- **含中文的 `.vue` 文件**：禁止直接用 Cursor Write/StrReplace（易乱码）；按 `docs/ui-style.md` 用 **UTF-8 Python 脚本**改写
- Vue scoped 样式：避免在 scoped 里硬写会破坏黄金分割布局的 `padding` / `grid-template-columns`（见 UI 指南禁用清单）

### 2.3 通用

- 注释：解释非显而易见的业务/安全约束，不写废话注释
- 密钥与 Flag：日志、异常信息、API 响应、测试输出中必须脱敏（见 `backend/services/flag_redact.py`）
- 不提交：`.env`、`*.db`、`captures/`、`instance/`、`uploads/`、密钥文件（见 `.gitignore`）

---

## 3. 架构与设计原则

### 3.1 分层（强制）

```
route（Controller） → services（业务） → server/db_models + Redis/Docker
```

| 允许 | 禁止 |
|------|------|
| `backend/route/*.py` 做参数校验、鉴权装饰器、调用 service、组装 JSON | route 内直接 `docker.from_env()`、实现 Flag 比对算法、复制一份限流逻辑 |
| `backend/services/*.py` 承载 Flag 校验、计分、容器编排、锁、配额 | 在 service 里返回未脱敏的完整 Flag 给非管理端 |
| `frontend/src/services/*.js` 封装 `/api/*` | 页面组件内直接 `axios.get('/api/...')` 散落调用 |
| 题目描述 / 公告 / 文章经 `utils/markdown.js` 渲染 | `v-html` 喂原始 Markdown / 用户 HTML |

### 3.2 Flag 校验（唯一权威路径）

- **核心**：`backend/services/scoring_service.py` → `FlagValidationService.validate_flag`
- **动态 Flag**：`backend/services/flag_generator.py`（`DynamicFlagGenerator`、`ContainerFlagService`、`resolve_challenge_expected_flag`）
- **提交入口**（改逻辑必须三处对齐或明确废弃其一）：
  - `POST /api/challenges/<id>/submit` → `backend/route/challenges.py`（`@jwt_required` + `@submission_rate_limit`）
  - `backend/route/ctf_api.py` → `submit_flag`
  - `backend/route/container_challenges.py` → `/submit-flag`
- **并发**：`backend/services/submit_lock.py`（DB `FOR UPDATE` + Redis `neepu:submit:lock:*`）
- **作弊**：`backend/services/cheat_detection_service.py`（由 Flag 校验链路调用）
- 动态占位符：`[GUID]`、`[TEAM_HASH]`、`[LEET]`、`[CLEET]`；实例字段 `CtfGameInstance.dynamic_flag`
- **禁止**：在 route 内 `if flag == challenge.flag` 硬编码比对；禁止跳过 `submit_lock`；禁止把静态 Flag 明文返回给普通用户

### 3.3 Docker 容器调度

| 职责 | 路径 |
|------|------|
| 编排 | `backend/services/container_service.py` |
| 端口 | `backend/server/container_ports.py` |
| 访问 URL | `backend/server/container_access.py` |
| 配额 | `backend/services/instance_quota.py` |
| 启停队列 | `backend/services/container_start_queue.py` |
| 定时清理 | `backend/services/scheduler.py` |
| 流量捕获 | `backend/services/container_traffic.py`、`backend/server/traffic_capture.py` |
| 题模板 | `docker_templates/signup/`、`docker_templates/sqli-simple/` |

规则：

- 启容器 API 必须保留限流（例：`ctf_api.start_container_instance` 上 `@rate_limit(..., max_requests=8, window_seconds=60)`）
- 注入环境变量 `FLAG=` 等敏感信息时，不得写入可被普通用户拉取的日志 / 管理列表非必要字段
- 资源限制（CPU/内存/网络）在 `container_service` 统一配置，禁止 route 随意 `docker run` 无限制容器
- 过期清理依赖 scheduler；修改实例生命周期必须同步考虑清理任务

### 3.4 鉴权与权限

- JWT：**仅 Cookie**（`JWT_TOKEN_LOCATION=['cookies']`，Cookie `neepu_token`），见 `backend/app.py`
- 登录/注册：`backend/route/auth.py`，须保留 `@login_rate_limit` / `@rate_limit` + 验证码链路（`backend/route/captcha.py`、`captcha_store.py`、`security_helpers.py`）
- 管理接口：`@jwt_required()` 后检查 `user.is_admin`（部分允许 `is_moderator`）；参考 `challenge_admin.py`、`ctf_admin.py`、`dynamic_packages.py`
- 比赛内权限：`GamePermission`（`scoring_service` / `permission_service.py`）
- 前端：`credentials: 'include'`；生产 `JWT_COOKIE_SECURE` / SameSite 行为勿在 DEBUG 假设下硬编码破坏
- 生产：`NEPU_JWT_SECRET` ≥ 32 字符；禁止提交弱密钥或把 secret 写进前端

### 3.5 限流与 Redis

- 装饰器：`backend/middleware_refactored/rate_limiting/decorators.py`（`rate_limit`、`submission_rate_limit`、`login_rate_limit`）
- Redis 实现：`redis_rate_limiter.py`（前缀 `ratelimit:`）
- 封装：`backend/services/redis_service.py`；中间件初始化在 `backend/app.py`（`configure_redis_backend`）
- **高频接口必须挂限流**：Flag 提交、登录/注册、启容器、验证码获取、批量导出类管理接口
- 无 Redis 时回退内存限流仅适开发；生产默认依赖 Redis（`NEPU_REQUIRE_REDIS`）；多 worker 下禁止依赖纯内存限流

### 3.6 上传与文件

- 路由：`backend/route/uploads.py`、`attachments.py`、`dynamic_packages.py`、管理端上传入口
- Zip 防护：`backend/services/zip_safety.py`（必须保留解压大小/层数限制）
- 存储：`backend/services/storage.py`（local / S3）
- `app.py` 中 `block_public_uploads`：禁止 `/static/uploads/` 未授权直链；新增静态目录时同步考虑封锁策略
- 敏感词：`backend/services/sensitive_words.py`、`backend/config/sensitive_word_list.txt`

---

## 4. 安全与 CTF 业务底线

### 4.1 绝对禁止

1. 在响应、日志、前端 store、E2E 报告中泄露 **静态 Flag / 动态 Flag / JWT secret / Redis 密码 / 邮箱密码**
2. 绕过 `@jwt_required`、admin 检查、`GamePermission` 暴露题目 Flag、附件或管理 API
3. 移除或架空 `@submission_rate_limit` / 启容器 `@rate_limit` / 登录限流「仅为了方便调试」且不恢复
4. 前端 `v-html` 渲染未经过 `frontend/src/utils/markdown.js`（DOMPurify）的用户/运营内容
5. 将 `.env`、真实 `captures/*.pcap`、生产库 dump 提交进 Git
6. 编写或提供针对**本平台生产环境**的利用 PoC 并建议对外攻击；安全修复可保留防御性测试，但不得附带可复用的 exploit payload
7. 在容器题模板中默认 `privileged: true` 或挂载 Docker socket，除非有书面安全评审

### 4.2 敏感路径清单（改动需额外 Review）

| 模块 | 路径 |
|------|------|
| Flag 校验 / 计分 | `backend/services/scoring_service.py`、`flag_generator.py`、`flag_redact.py` |
| 提交锁 / 血榜竞态 | `backend/services/submit_lock.py`、`tests/test_p0_race_blood.py` |
| 容器编排 | `backend/services/container_service.py`、`instance_quota.py`、`container_start_queue.py` |
| 鉴权 | `backend/route/auth.py`、`backend/app.py`（JWT 段）、`permission_service.py` |
| 限流 | `backend/middleware_refactored/rate_limiting/` |
| 管理 API | `backend/route/admin.py`、`ctf_admin.py`、`challenge_admin.py`、`platform_admin.py` |
| XSS / Markdown | `frontend/src/utils/markdown.js` |
| 上传 / Zip | `backend/route/uploads.py`、`zip_safety.py` |
| 审计 | `backend/server/audit_log.py`、`submit_audit.py` |

### 4.3 安全头与 CORS

- 安全头：`backend/middleware_refactored/security/headers.py`
- CORS：仅允许 `config.settings.FRONTEND_URL` 配置的来源，且 `supports_credentials=True`；禁止改为 `*` 且带 Cookie

### 4.4 数据模型注意点

关键模型在 `backend/server/db_models.py`：`User`、`Team`、`CtfGame`、`CtfSeason`、`CtfChallenge`、`CtfChallengeSubmission`、`CtfGameInstance`、`CtfSolves`、`CtfScoreboard`、`CtfCheatInfo`、`PcapCapture`、`CtfDynamicPackage` 等。  
修改 `CtfChallenge.flag` / `flag_template` / `docker_*` / `challenge_type` 或 `CtfGameInstance.dynamic_flag` 属于 P0 变更。

---

## 5. 测试与验收

| 类型 | 位置 / 命令 |
|------|-------------|
| API / 竞态 / Redis / Zip | `tests/` — `pytest tests/ -q` |
| P0 血榜竞态 | `tests/test_p0_race_blood.py` |
| Playwright 拓扑扫描 | `e2e/` — 见 `e2e/README.md` |
| 后端脚本冒烟 | `backend/scripts/*_smoke.py`、`*_e2e.py` |
| 动态 Flag 脚本 | `scripts/test_dynamic_flag.py` |

规则：

- 修改 Flag 提交、血榜、限流、容器启停后：**至少**跑相关 pytest；有条件跑 e2e 拓扑扫描
- 新增限流/锁逻辑时补充或更新测试，禁止只改生产代码
- 前端 UI 改动按 `docs/frontend-ui-harness.md` 做 MCP / 视觉验收（若环境可用）

---

## 6. UI / 前端专项约束（摘要）

完整规范见 `docs/ui-style.md`。Agent 必须遵守：

- 气质：**二次元 / 轻游戏 UI**；禁用 Matrix 绿雨、终端主导导航、Inter/IBM Plex 作为主 UI 字体
- 布局：黄金分割 φ；侧栏 **248px** 可折叠 rail（对齐 `/training`）
- 签名元素：圆角卡片 + 分类色标 chip；不要做成通用 SaaS 仪表盘堆砌
- 主题 Token 走 `frontend/public/themes/*.css`
- 中文 Vue 文件用 UTF-8 Python 脚本编辑

---

## 7. 自动化排查与 Code Review 指令

用户或 Agent 可通过下列指令触发对应检查清单（执行时对照真实路径勾选）。

### `@Agent Review` — 通用 Diff Review

1. 分层是否被破坏（route 直连 Docker/DB 业务逻辑）？
2. 新 `/api/*` 是否在 `app.py` 注册、是否写入 `docs/route-architecture-topology.md` / checklist？
3. 是否触及第 4.2 节敏感路径？若是，是否保留鉴权 + 限流 + 脱敏？
4. 前端是否只经 `src/services/` 调 API？Cookie 是否 `include`？
5. Markdown / `v-html` 是否经 DOMPurify？
6. 是否误改 `.env` 示例外的密钥或把 Flag 写入测试断言明文？
7. 双轨 API（challenges / ctf / container）是否只改一边？

### `@Agent Review Security` — 安全专项

检查清单：

- [ ] Flag 提交仍走 `FlagValidationService` + `submit_lock` + `@submission_rate_limit`
- [ ] 管理接口 `jwt_required` + `is_admin`（或文档允许的 moderator）
- [ ] 启容器仍有 rate limit + 配额（`instance_quota`）
- [ ] 上传 / Zip 仍受 `zip_safety` 约束
- [ ] 无 CORS `*` + credentials；无公开 static uploads 直链回退
- [ ] 日志与异常无 Flag / token 泄漏（`flag_redact`）
- [ ] Redis 限流 key 与锁 key 未冲突、未取消生产 Redis 要求

### `@Agent Review Flag` — Flag / 计分专项

重点文件：`scoring_service.py`、`flag_generator.py`、`submit_lock.py`、`challenges.py`、`ctf_api.py`、`container_challenges.py`、`cheat_detection_service.py`、`tests/test_p0_race_blood.py`。

验证：静态 Flag、动态模板、容器实例 Flag、一血竞态、重复提交、跨队作弊路径。

### `@Agent Review Container` — 容器调度专项

重点文件：`container_service.py`、`container_ports.py`、`container_access.py`、`instance_quota.py`、`container_start_queue.py`、`scheduler.py`、`container_challenges.py`、`docker_templates/**`。

验证：端口泄漏、僵尸容器、FLAG 环境变量暴露面、无限制资源、清理任务是否仍注册。

### `@Agent Debug Submit` — 提交失败排查顺序

1. 鉴权 Cookie `neepu_token` 是否送达（前端 `authFetch` / axios `withCredentials`）
2. 限流是否触发（Redis `ratelimit:*` / 装饰器）
3. `submit_lock` 是否超时或死锁
4. `resolve_challenge_expected_flag` 对应该题 `flag_template` / 实例 `dynamic_flag`
5. 比赛权限 `GamePermission`、训练赛 vs 正式赛分支（`_is_training_game`）
6. 对比 `/api/challenges/.../submit` 与 `/api/ctf/...` 是否打到同一套校验

### `@Agent Debug Container` — 容器启停排查顺序

1. Docker daemon 可达性（`docker.from_env()`）
2. 用户/队伍配额 `instance_quota`
3. 启容器限流与 `container_start_queue`
4. 端口分配 `container_ports` 与访问 URL `container_access`
5. scheduler 清理是否误杀
6. 题目 `docker_*` 字段与 `docker_templates/` 镜像是否匹配

### 建议本地命令（Agent 可执行）

```bash
# 后端单测
pytest tests/ -q

# 聚焦 P0 竞态
pytest tests/test_p0_race_blood.py -q

# Redis / 中间件
pytest tests/test_redis_middleware.py -q

# Zip 安全
pytest tests/test_zip_safety.py -q

# 前端构建
cd frontend && npm run build

# E2E（需服务已启动，见 e2e/README.md）
cd e2e && npx playwright test
```

---

## 8. 变更工作流（Agent 必须遵守）

1. **先读后改**：敏感模块先读现有实现再补丁，禁止平行实现第二套 Flag/限流
2. **最小 diff**：不重构无关文件；不顺手「清理」大段无关注释或重排 import（除非阻碍变更）
3. **文档同步**：新增/废弃 API 或路由时更新 `docs/route-architecture-topology.md` 与必要时 `api-frontend-checklist.md`
4. **密钥**：不把真实 `.env` 内容粘贴进对话；示例用占位符
5. **Git**：仅在用户明确要求时 commit / push；遵守仓库既有提交信息风格
6. **回复语言**：与用户沟通使用简体中文（除非用户要求其他语言）

---

## 9. 快速决策表

| 场景 | 正确做法 |
|------|----------|
| 页面要调新接口 | 加 `frontend/src/services/xxx.js`，组件只调 service |
| 新管理 API | `jwt_required` + admin 检查 + 写审计（如适用）+ 限流 |
| 改 Flag 逻辑 | 只改 `scoring_service` / `flag_generator`，入口 route 只做编排 |
| 渲染题面 Markdown | `utils/markdown.js` |
| 改主题色 | `frontend/public/themes/*.css` |
| 改含中文 Vue | UTF-8 Python 脚本 |
| 加容器题模板 | `docker_templates/<name>/` + 文档；走 `container_service` |
| 临时关掉限流调试 | 仅本地 DEBUG，合并前必须恢复，并在 PR/说明中明示 |

---

## 10. 文档索引

- `docs/README.md` — 文档总目录
- `docs/route-architecture-topology.md` — 路由拓扑与双轨 API
- `docs/deploy-single-server.md` — 单机生产部署
- `docs/ui-style.md` — UI 规范
- `docs/frontend-ui-harness.md` — UI 验收
- `docs/api-frontend-checklist.md` — 对接清单
- `docs/ui-style.md` — 本项目 UI 规范（唯一）

---

*最后根据仓库实扫生成。若代码结构重大变更，请同步更新本文敏感路径与 Blueprint 表。*
