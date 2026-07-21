# NEEPU CTF · Ret2Shell 对照优化清单

> 对照仓库：[ret2shell/ret2shell](https://github.com/ret2shell/ret2shell)（Rust + SolidJS）  
> 本仓库栈：Flask 单体 + Vue3 + Naive UI + MySQL/SQLite + Redis + Docker  
> **原则**：不搬栈、不重写；只采纳可落地子集。  
> **图例**：⬜ 未开始 · 🔄 进行中 · ✅ 已完成 · ⏸️ 暂缓 · ❌ 不做

最后更新：2026-07-21（**S2 全部完成**）

---

## 明确不做

| ID | 项 | 原因 | 状态 |
|----|----|------|------|
| X1 | 改写 Rust / SolidJS | 成本过高 | ❌ |
| X2 | K8s cluster + 内置 registry | 单机靶场过重 | ❌ |
| X3 | NATS 整套 queue | Redis + 定时任务够用 | ❌ |
| X4 | 完整 Rune 脚本引擎一次到位 | 可后期单独立项 | ❌ |

---

## S1 · P0（先补齐）

### 前端

| ID | 项 | 验收标准 | 状态 |
|----|----|----------|------|
| F01 | 做题台容器：开启 / 延时 / 销毁 / 倒计时 | Workspace 容器题可见完整操作；联调 API 成功 | ✅ |
| F02 | 附件题入口 | 无容器题突出下载；无附件有提示；有附件可下 | ✅ |
| F03 | 孤儿 DynamicPackage：下架或接 API | 管理端不再 404；有明确「未开放」或空列表 | ✅ |
| F04 | Terminal mock 标明 | UI 标明装饰终端；真连接引导看 `connection_url` | ✅ |
| F05 | 字体西电混排 | Reverier Mono + 系统中文；无 Noto CDN 切片 | ✅ |
| F06 | 前端 API 分层起步 | `services/container.js` 等收拢容器调用 | ✅ |

### 后端

| ID | 项 | 验收标准 | 状态 |
|----|----|----------|------|
| B01 | 容器 API 主路径文档化 | 主路径 `/api/challenges/...`；旧 `/api/container/*` 标兼容 | ✅ |
| B02 | 过期实例定时清理 + 幽灵对账 | Scheduler 清理过期；DB 运行中但 Docker 已无 → 标停止 | ✅ |
| B03 | 启容器 / 提交限流统一 | `start-container` + `submit` 已挂 rate limit | ✅ |
| B04 | 敏感词审核（队名） | 建队/改名拦截敏感词 | ✅ |
| B05 | 动态附件包 API | stub：列表空 + 写操作 501；前端不 404 | ✅ |
| B06 | Hint / Hammer / 队伍 / PCAP 缺口 | 对照 `api-frontend-checklist.md` 逐项接好 | ✅ |

---

## S2 · P1（体验 + 运维优化）

### 原计划

| ID | 项 | 验收标准 | 状态 |
|----|----|----------|------|
| F10 | 通知/血榜/锤子短轮询收敛或 SSE | `utils/polling.js` 统一间隔 + 可见性暂停；锤子/血榜/容器/管理端 chat | ✅ |
| F11 | 赛事管理占位入口隐藏或真做 | 未实现分区不进导航 | ✅ |
| F12 | Markdown 高亮/目录增强 | highlight.js + TOC；Wiki/题面/赛事说明走 `Article` | ✅ |
| F13 | InstanceBox 全局实例列表完善 | 顶栏实例列表接 `/platform/instances` + 延时/销毁 | ✅ |
| B10 | 启容器队列化（Redis） | `container_start_queue` 限并发；无 Redis 直通 | ✅ |
| B11 | 流量捕获配额与清理 | 日清 + 对账 + `PCAP_MAX_*` 配额回收 | ✅ |
| B12 | 上传存储抽象（bucket） | `storage.get_storage()` local 默认 / s3 可选 | ✅ |
| B13 | 提交审计字段（IP/队/耗时） | submission 记 `client_ip` / `team_id` / `duration_ms` | ✅ |

### 项目增量（联调中发现，已并入 P1）

| ID | 项 | 验收标准 | 状态 |
|----|----|----------|------|
| F14 | 管理端赛事列表过滤 E2E/探针 | `/api/ctf/games` 默认排除 ephemeral；`include_ephemeral=1` 可看全量 | ✅ |
| F15 | 管理端错误提示统一 | CtfManagement 用 `apiError` / naive toast，无 `alert` | ✅ |
| F16 | 管理端赛事筛选（正式/训练/探针） | UI 暴露 game_type / 探针开关；API `game_type=` | ✅ |
| B14 | PCAP 定时清理入 Scheduler | 每日清理 N 天前文件（默认 30 天） | ✅ |
| B15 | E2E 测试赛自动隐藏 | 定时将公开 ephemeral 赛 `is_public=False` | ✅ |
| B16 | Docker 反向幽灵巡检 | 清理 `ctf-{cid}-{uid}-*` 无 DB 记录的容器 | ✅ |
| B17 | PCAP 磁盘/DB 一致性清扫 | 缺文件删记录；可导入/可选删磁盘孤儿；日清对账 | ✅ |
| B18 | 训练场提交短路 | training 跳过血榜/公告/正式积分/赛季 | ✅ |
| B19 | 销毁幽灵 container 404 容忍 | Docker NotFound 视为成功并清库 | ✅ |

---

## S3 · P2（可选）

| ID | 项 | 状态 |
|----|----|------|
| P20 | 轻量 Checker（HTTP/表达式） | ⬜ |
| P21 | 真终端 / WSRX | ⬜ |
| P22 | Game lifecycle 预设 | ⬜ |
| P23 | OAuth / 增强邮件 | ⬜ |
| P24 | Compose 一键部署文档对齐 | ⬜ |

---

## 容器 API 约定（B01）

**主路径（前端优先）：**

| 操作 | Method | Path |
|------|--------|------|
| 状态 | GET | `/api/challenges/{cid}/container-status` |
| 启动 | POST | `/api/challenges/{cid}/start-container` |
| 停止 | POST | `/api/challenges/instances/{iid}/stop` |
| 延时 | POST | `/api/challenges/instances/{iid}/extend` |

**兼容别名（保留）：** `/api/container/start|stop|extend|status/...`

前端封装：`frontend/src/services/container.js`（Workspace 已改用）

---

## 前端页面 ↔ API 对照

| 能力 | 前端入口 | 服务层 | 后端 |
|------|----------|--------|------|
| 容器启停延时 | `ChallengeWorkspace` 在线环境面板 | `services/container.js` | `/api/challenges/...`（启容器可走 Redis 队列） |
| 全局实例 | 顶栏 `InstanceBox` | `services/instances.js` | `/api/platform/instances` |
| Hint 解锁 | Workspace「提示」Tab | `services/challenges.js` | `/hints` + `/access-hint` |
| Hammer | Workspace `HammerPanel` | `services/challenges.js` | `/hammer` GET/POST |
| 建队/改名/退队 | `GameTeams` | `services/teams.js` | `/api/teams/*` + 敏感词提示 |
| 动态附件包 | 管理端 CTF → **动态附件包** Tab | `services/admin/ctf.js` | stub 空列表 / 501 |
| 流量 PCAP | 管理端 CTF → **流量捕获** Tab | `TrafficCapturePanel` + `ctf.js` | list/download/delete |
| 限流/业务错误 | 上述页面统一 toast | `utils/apiError.js` | 429 / 400 msg |
| 赛事列表 | 管理端 / 流量 Tab | `ctf.js` listGames | `/api/ctf/games` 默认无 E2E |
| Markdown | Wiki / 题面 / writeup | `utils/markdown.js` + `Article` | — |
| 上传 | 编辑器 / 附件 | — | `storage.get_storage()` |

> `/games/:id/admin/*` 重定向到 `/admin/ctf`；PCAP 以管理端 Tab 为准。

---

## 关键环境变量（S2）

| 变量 | 默认 | 说明 |
|------|------|------|
| `PCAP_RETENTION_DAYS` | 30 | PCAP 保留天数 |
| `PCAP_MAX_TOTAL_BYTES` | 20GB | 总磁盘配额，0=不限 |
| `PCAP_MAX_BYTES_PER_GAME` | 2GB | 单赛配额，0=不限 |
| `PCAP_PRUNE_ORPHAN_FILES` | false | 对账时是否删无主文件 |
| `CONTAINER_START_MAX_CONCURRENT` | 2 | 启容器并发 |
| `CONTAINER_START_QUEUE_WAIT_SEC` | 90 | 排队等待超时 |
| `STORAGE_BACKEND` | local | `local` / `s3` |
| `STORAGE_LOCAL_ROOT` | `backend/static/uploads` | 本地根目录 |
| `STORAGE_S3_BUCKET` | — | S3/MinIO bucket |
| `REDIS_ENABLED` | true | 启容器队列依赖 Redis |

---

## 联调记录

| 日期 | 项 | 结果 | 备注 |
|------|----|------|------|
| 2026-07-21 | F01/F02 | ✅ | ChallengeWorkspace 容器/附件面板 |
| 2026-07-21 | F05 | ✅ | 去掉 Noto CDN；Reverier + 系统中文 |
| 2026-07-21 | B02 | ✅ | scheduler 清理 + 幽灵对账 |
| 2026-07-21 | B03 | ✅ | submit / start-container 限流 |
| 2026-07-21 | B04 | ✅ | 敏感词队名 |
| 2026-07-21 | F03/B05 | ✅ | 动态包 stub |
| 2026-07-21 | F04 | ✅ | Terminal 装饰标注 |
| 2026-07-21 | F06/B01 | ✅ | container.js |
| 2026-07-21 | B06 | ✅ | Hint/Hammer/Teams/PCAP 接线 |
| 2026-07-21 | 前端对照 + MCP | ✅ | 动态包/PCAP Tab、API 套件 |
| 2026-07-21 | B19 | ✅ | 销毁 404 容忍；`fe_be_smoke` 8/8 |
| 2026-07-21 | F14/B14/B15 | ✅ | list_games 默认滤 E2E；PCAP 日清；小时隐藏探针赛 |
| 2026-07-21 | B18 | ✅ | training 提交 `training_mode`；solves/notice/scoreboard 无增量 |
| 2026-07-21 | F15 | ✅ | CtfManagement `alert` → naive `message` + `apiErrorFromPayload` |
| 2026-07-21 | B16 | ✅ | `reconcile_orphan_docker_containers` 挂 30s 清理 |
| 2026-07-21 | B17 | ✅ | `TrafficCaptureService.reconcile_consistency` + 日清 03:45 |
| 2026-07-21 | F16 | ✅ | list_games `game_type`；CtfManagement 筛选条 + 类型列 |
| 2026-07-21 | F10 | ✅ | `polling.js`；Hammer/血榜/容器/GameAdmin chat 可见性轮询 |
| 2026-07-21 | B13 | ✅ | `client_ip`/`duration_ms`；提交带 `elapsed_ms` |
| 2026-07-21 | B11 | ✅ | 修 glob `*/*.pcap`；`enforce_disk_quota` + 日清 |
| 2026-07-21 | F12 | ✅ | highlight.js；Wiki/writeup/赛事说明 TOC |
| 2026-07-21 | B10 | ✅ | Redis 启容器队列；scheduler 2s 消费；无 Redis 直通 |
| 2026-07-21 | B12 | ✅ | `services/storage.py`；uploads 走抽象层 |

---

## 完成度汇总

| 阶段 | 完成 | 总计 | 进度 |
|------|------|------|------|
| 不做 X | 4 | 4 | — |
| S1 P0 | **12** | 12 | **100%** |
| S2 P1 | **17** | **17** | **100%** |
| S3 P2 | 0 | 5 | 0% |

> GPT 监督：以本文件状态列为准；每完成一项改 ⬜→✅，并在「联调记录」补一行。  
> **下一步（可选 S3）**：P20 Checker → P24 Compose 文档 → P21 真终端。
