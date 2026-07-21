# NEEPU CTF — 后端已测 API 与前端对接清单

> 供前端同学对照：页面/组件是否已对接、路径是否正确。  
> **图例：** ✅ 脚本 E2E 已测 · ⚠️ 仅探针/部分 · ❌ 未测  
> 测试脚本目录：`backend/scripts/`（`full_competition_e2e.py`、`traffic_capture_e2e.py`、`sqli_traffic_capture_e2e.py`、`container_lifecycle_e2e.py`、`admin_smoke_test.py` 等）

---

## 认证

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `POST /api/auth/login` | 登录页 | ✅ |
| `GET /api/auth/me` | `services/auth.js`、各页鉴权 | ✅ |
| `POST /api/auth/logout` | 登出 | ✅ |

---

## 赛事 / 报名

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/competitions/?exclude_training=true` | `Home.vue`、`GamesHub.vue`、`PlatformLanding.vue` | ✅ |
| `GET /api/competitions/{gid}` | `GameDetail.vue`、`CTFCompetitions.vue`、`Scoreboard.vue`、`TitleBar.vue` | ✅ |
| `GET /api/competitions/{gid}/joined` | `GameDetail.vue`、`CTFCompetitions.vue` | ✅ |
| `POST /api/competitions/{gid}/join` | `GameDetail.vue`、`CTFCompetitions.vue`、`GameTeams.vue` | ✅ |
| `POST /api/competitions/admin/create` | `Training.vue`、`CtfManagement.vue` | ✅ |
| `PUT /api/competitions/admin/{gid}/update` | `GameAdmin.vue`、`GameDetail.vue`、`CtfManagement.vue` | ⚠️ |
| `DELETE /api/competitions/admin/{gid}/delete` | `GameAdmin.vue` | ❌ |

---

## 题目列表 / 详情 / 提交

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/challenges/games/{gid}/challenges` | `ChallengeWorkspace.vue`、`Scoreboard.vue`、`GameAdmin.vue` | ✅ |
| `GET /api/challenges/{cid}` | `ChallengeWorkspace.vue`、`ChallengeDetailPage.vue` | ✅ |
| `GET /api/challenges/{cid}/stats` | `ChallengeWorkspace.vue`、`ChallengeDetailPage.vue` | ✅ |
| `GET /api/challenges/{cid}/hints` | `ChallengeWorkspace.vue` | ⚠️ GET only |
| `POST /api/challenges/{cid}/access-hint` | `ChallengeWorkspace.vue` | ✅ |
| `POST /api/challenges/{cid}/submit` | `ChallengeWorkspace.vue`、`ChallengeDetailPage.vue` | ✅ |
| `GET /api/challenges/{cid}/submissions` | `Submissions.vue` | ❌ |
| `GET /api/challenges/games/{gid}/first-solves` | `ChallengeWorkspace.vue`、`Scoreboard.vue` | ✅ |

**提交 body：** 后端接受 `answer` 或 `flag` 字段（Workspace 两种都传）。

---

## 附件 / 资源

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/resources/{id}/content` | `ChallengeDetailPage.vue`、`CtfManagement.vue`、`<a href>` 直链 | ✅ |
| `POST /api/admin/challenges/games/{gid}/challenges/{cid}/attachments` | `CtfManagement.vue` 上传 | ✅ |

---

## 容器（选手侧）

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/challenges/{cid}/container-status` | `ChallengeWorkspace.vue`、`ChallengeDetailPage.vue` | ✅ |
| `POST /api/challenges/{cid}/start-container` | `ChallengeWorkspace.vue`、`ChallengeDetailPage.vue`（优先） | ✅ |
| `POST /api/container/start/{cid}` | `ChallengeWorkspace.vue`（fallback） | ✅ |
| `POST /api/challenges/instances/{iid}/stop` | `InstanceBox.vue`、`ChallengeDetailPage.vue` | ✅ |
| `POST /api/challenges/instances/{iid}/extend` | `InstanceBox.vue` 延期按钮 | ✅ |
| `GET /api/platform/instances` | `InstanceBox.vue` 实例列表 | ✅ |
| `GET /api/container/status/{cid}` | 若有 fallback 路径 | ❌ |
| `POST /api/container/stop/{iid}` | 旧路径 | ❌ |
| `POST /api/container/extend/{iid}` | 旧路径 | ❌ |

### 拨号地址（非 API）

- 开容器后展示 **`connection_url`**（如 `http://公网IP:10009`），选手必须访问此地址。
- 开启流量捕获时，`connection_url` 指向**代理端口**；直连内网 port 不会进 PCAP。
- 公网主机由后端 `CONTAINER_PUBLIC_HOST` 配置。

### 容器生命周期（已测行为）

| 行为 | 说明 | 状态 |
|------|------|------|
| 默认 TTL | `container/start` 路径：**1 小时** | ✅ |
| 手动销毁 | `stop` → Docker stop + remove | ✅ |
| 延时 | `extend` → `expires_at` +1 小时 | ✅ |
| 到期销毁 | Scheduler 每 30s 清理 + status 懒清理 | ✅ |

---

## 积分榜 / 公告 / 血榜

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/ctf/games/{gid}/scoreboard` | `Scoreboard.vue`、`GameAdmin.vue` | ✅ |
| `GET /api/ctf/games/{gid}/scoreboard/timeline` | `GameAdmin.vue` | ✅ |
| `GET /api/ctf/games/{gid}/notices` | `CTFCompetitions.vue` | ✅ |
| `GET /api/challenges/{cid}/hammer` | `HammerPanel.vue`、`ChallengeWorkspace.vue` | ✅ |
| `POST /api/challenges/{cid}/hammer` | `HammerPanel.vue` | ✅ |

---

## 队伍

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/teams/me?game_id=` | `GameDetail.vue`、`CTFCompetitions.vue`、`GameTeams.vue` | ✅ |
| `GET /api/teams/?game_id=` | `GameTeams.vue` | ✅ |
| `POST /api/teams/` | `GameTeams.vue`、`Teams.vue` | ✅ |
| `POST /api/teams/join` | `GameTeams.vue`、`Teams.vue` | ✅ |
| `PATCH /api/teams/{id}` | `GameTeams.vue` | ✅ |
| `POST /api/teams/{id}/leave` | `GameTeams.vue` | ✅ |
| `GET /api/teams/{id}/solves` | `GameAdmin.vue`、`GameTeams.vue` | ✅ |

---

## 管理端（`services/admin/ctf.js` / `CtfManagement.vue`）

| API | 用途 | 状态 |
|-----|------|------|
| `POST /api/admin/challenges/games/{gid}/challenges` | 创建题目 | ✅ |
| `GET /api/admin/challenges/games/{gid}/challenges-list` | 管理端题目列表 | ❌ |
| `PUT /api/admin/challenges/games/{gid}/challenges/{cid}` | 编辑题目 | ❌ |
| `DELETE /api/admin/challenges/games/{gid}/challenges/{cid}` | 删除题目 | ❌ |
| `GET /api/competitions/admin/{gid}/traffic-captures?sync=1` | 流量包列表 | ✅ |
| `GET /api/competitions/admin/traffic-captures/{id}/download` | 下载 PCAP | ✅ |
| `DELETE /api/competitions/admin/traffic-captures/{id}` | 删除 PCAP | ✅ |
| `/api/competitions/admin/{gid}/divisions/*` | 分组 CRUD | ❌ |
| `/api/competitions/admin/{gid}/archive` | 归档 | ❌ |

创建赛事时可传 `enable_traffic_capture: true` 开启动态容器流量捕获。

---

## 平台管理后台（GET 冒烟）

| API | 状态 |
|-----|------|
| `GET /api/admin/platform/dashboard` 等 12 个 | ✅ |
| `GET /api/admin/cheat-detection` | ✅ |
| `GET /api/admin/first-solves` | ✅ |
| `GET /api/admin/games`（遗留，建议改用 `competitions/admin`） | ✅ 兼容 |
| `GET /api/ctf/games?per_page=10` | ✅ |
| `GET /api/teams/admin` | ✅ |

---

## 其他

| API | 前端可能位置 | 状态 |
|-----|-------------|------|
| `GET /api/captcha/` | `Captcha.vue` | ❌（默认关闭 `NEPU_CAPTCHA_REQUIRED`） |
| `GET /api/health/` | 健康检查 | ✅ |

---

## 前端重点自查（5 条）

1. **开容器流程**：先 `GET .../container-status`，再 `POST .../start-container`，失败再 fallback `POST /api/container/start/{cid}`。
2. **拨号地址**：展示并复制 `connection_url`，不要只展示 port 或 localhost。
3. **销毁 / 延期**：统一走 `/api/challenges/instances/{id}/stop` 与 `/extend`（`InstanceBox` 已按此对接）。
4. **提交 Flag**：body 带 `answer` 或 `flag` 均可。
5. **未测页面优先联调**：`InstanceBox` 列表、`Submissions`、Hammer POST、队伍全流程、PCAP 下载。

---

## 测试脚本索引

| 脚本 | 覆盖 |
|------|------|
| `backend/scripts/full_competition_e2e.py` | 建赛、5 类题、附件、容器、动态 flag、一二三血、积分榜 |
| `backend/scripts/traffic_capture_e2e.py` | 流量捕获 + HTTP GET + PCAP |
| `backend/scripts/sqli_traffic_capture_e2e.py` | SQL 注入 POST/GET + PCAP |
| `backend/scripts/container_lifecycle_e2e.py` | 销毁、延时、到期清理 |
| `backend/scripts/admin_smoke_test.py` | 管理端 GET 冒烟 |
| `backend/scripts/game_api_probe.py` | 赛事/题目/队伍 API 探针 |

本地复测示例：

```bash
cd backend
python scripts/full_competition_e2e.py
python scripts/container_lifecycle_e2e.py
```
