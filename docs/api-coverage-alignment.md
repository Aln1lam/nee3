# NEEPU CTF · 前后端覆盖度对齐（4.1 / 4.2）

> 对照用户清单逐项核实后的结论与已做对齐。  
> 日期：2026-07-21

---

## 4.1 前端调用了，后端未见 / 路径错误

| 前端原调用 | 核实 | 对齐结果 |
|------------|------|----------|
| `GET /api/challenges/games/:id/scoreboard/user` | ❌ 仅有 `/api/ctf/games/:id/scoreboard/user` | ✅ 已改 `CTFCompetitions.vue` → `/api/ctf/...`；排行榜列表一并改到 ctf 主路径 |
| `POST /api/admin/platform/distribute-todos` | ❌ 后端无此接口；`TodoDistribution` 未挂入 `AdminContent` | ✅ 停止错误请求，提示「尚未开放」 |
| `GET /api/admin/submissions` | ❌ 无此接口；`Admin.vue` 未挂路由 | ✅ 改为 `/api/admin/first-solves`；赛事列表改 `/api/ctf/games`；文件头标明 LEGACY |
| `/api/dynamic/cheat-detection/:id/details` | ❌ 应为 `/api/admin/cheat-detection` | ✅ `CheatDetectionDetail.vue` 已改；审核改 `/api/admin/cheat-records/:id/{review\|confirm\|dismiss}` |
| `/api/dynamic/challenges/:id/upload-package` | ❌ 应为 `/api/admin/dynamic-packages/.../upload` | ✅ 同上模板组件已改 |
| `GET /api/media?hash=` | ❌ 后端无 `/api/media` | ✅ `UiPicture.vue`：仅用 `url`；裸 `hash` 显示占位，不再打不存在的 API |

**说明：** `CTFCompetitions` / `Admin` / `CheatDetectionDetail` / `TodoDistribution` 多数**未进现网 router**，但错误路径会在复用时复发，故仍对齐到主路径。

---

## 4.2 后端存在、前端主路径几乎未暴露

| API | 核实 | 对齐策略 |
|-----|------|----------|
| `/api/container/debug/<instance_id>` | ✅ 脚本/E2E 用 | **故意不进选手 UI**；运维用脚本。保持现状 |
| `/api/container/test-flag-generation` | ✅ 运维测 Flag | **故意不进 UI**；`scripts/test_dynamic_flag.py` |
| `/api/container/proxy/<instance_id>` | ✅ 流量捕获代理 | **选手无感**：`connection_url` 已指向代理端口，前端只展示/复制 URL 即可 |
| `/api/competitions/debug/game/<id>` | ✅ 调试 | **故意不进 UI** |
| `/api/ctf/cleanup/containers` | ✅ Admin 清容器 | 现由 Scheduler + 管理端实例操作覆盖；可不单独做页。若要做可挂靶场管理「运维」按钮（未做） |
| `/api/tokens/*` | ✅ 有 CRUD | **产品暂缓**：无管理 UI（见 frontend-gaps N16）。脚本可直接调 |
| `/api/games/*` | ✅ 曾与 competitions/ctf 重叠 | **已 410 Gone**（整前缀下线） |
| `/api/admin/games*` | ✅ 曾与 competitions 重叠 | **已 410 Gone**（含 stats/export；继任 `/api/competitions/admin/`） |
| `/api/ctf` 非榜类 | ✅ 与 competitions/challenges 重叠 | **已 410**；仅保留 scoreboard*/notices/health/cleanup |

---

## Canonical 主路径（联调约定）

| 能力 | 应用 |
|------|------|
| 赛事读写 | `/api/competitions`、`/api/competitions/admin/*`（含 stats/export-scoreboard） |
| 做题/提交/容器 | `/api/challenges/*`（启容器可 fallback `/api/container/start`） |
| 积分榜/个人榜/时间线 | `/api/ctf/games/:id/scoreboard*` |
| 作弊/首解/Hammer 管理 | `/api/admin/cheat-*`、`/api/admin/first-solves`、`/api/admin/hammer-messages` |
| 动态附件包 | `/api/admin/dynamic-packages/challenges/:id/upload` |
| 附件下载 | `/api/resources/:id/content` 或 `/api/uploads/serve/...`（**不要** `/api/media`） |

**禁止新代码使用：** `/api/games/*`、`/api/admin/games*`、`/api/ctf`（除 scoreboard*/notices/health/cleanup）、`/api/dynamic/*`、`/api/media`、`/api/admin/submissions`。

---

## 修改文件

- `frontend/src/components/CTFCompetitions.vue`
- `frontend/src/components/ui/UiPicture.vue`
- `frontend/src/components/templates/CheatDetectionDetail.vue`
- `frontend/src/components/admin/TodoDistribution.vue`
- `frontend/src/components/Admin.vue`
- `backend/route/ctf_admin.py`（`/api/games` Deprecation 头）
- 本文档
