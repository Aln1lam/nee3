# 推送变更记录

本文件记录每次推送到 GitHub 仓库的改动摘要（不含密钥、隐私信息）。  
**约定：** 每次 push 前在顶部新增一节；详见 [`项目约定.md`](项目约定.md)。

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
