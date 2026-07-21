# NEEPU CTF · 前后端功能缺口（全局重扫）

> 2026-07-21 按代码重新对照：后端蓝图 / 前端路由 / 主路径组件。  
> **不要沿用「P0/P1 已全绿」的旧结论**——公开赛主路径大体可用，但下列缺口仍在。  
> 每条：**问题 → 改法 → 原因 → 收益**。

---

## 总览

| 结论 | 说明 |
|------|------|
| 公开赛办赛主路径 | 大体可用（列表→详情→组队→做题→交 Flag→容器→积分榜→管理端） |
| 文档旧状态 | `G01–G26` 多已落地，但**漏记**登录合同、私有赛邀请码、误报名等 P0 |
| 私有赛 / 鉴权合同 | **未闭环**，会直接踩坑 |
| BE 有、FE 无 | 退赛、归档真数据、文件台、Token、赛季、赛事 notices |
| FE 有、BE stub | ~~动态附件包~~ → 已 ready |
| 刻意不做 | Task19 全套子页、完整 OAuth 回调、换栈、真 WebSocket 终端 |

---

## A · P0 现网会直接坏 / 误操作

### N01 · 登录成功仍卡在已废弃的 `access_token`

- **问题**：后端登录只写 Cookie，响应 `{ user }`，**无** `access_token`。`Auth.vue` 成功分支包在 `if (data?.access_token)` 内 → 无提示、不跳转、不 `emit('logged')`。Cookie 可能已写入，UI 却像失败。
- **改法**：以 HTTP 200 + `data.user`（或随后 `fetchSession({ force: true })`）为成功；去掉对 localStorage Bearer 的硬依赖。
- **原因**：JWT 已迁 `cookies`，前端合同未跟。
- **收益**：登录主路径可用。
- **证据**：`backend/route/auth.py`（`set_access_cookies` + `jsonify({"user"})`）；`frontend/src/components/Auth.vue` ~140。

### N02 · 私有赛邀请码：后端强制，现网主路径不传

- **问题**：`is_public=false` 时后端要求 `invite_code`。现网 `GameDetail` / `GameTeams.joinCompetition` 都是 `POST .../join` + `{}`。带邀请码的逻辑只在未挂路由的旧 `Games.vue`。
- **改法**：详情页、战队报名页增加邀请码输入并传入 join；按 `is_public` 分支提示。
- **原因**：主路径迁到 GamesHub + GameDetail 后，旧报名 UI 未迁入。
- **收益**：私有赛 / 多赛道可报名。
- **证据**：`backend/route/competitions.py` ~266–273；`GameDetail.vue` ~366–378；`GameTeams.vue` join 空 body。

### N03 · 详情页 `checkBanned` 用 join 探测 → 公开赛误报名

- **问题**：详情加载时对已登录用户 `POST /api/competitions/{gid}/join`。公开赛会真正报名；后端无赛事 ban，探测无效。
- **改法**：删除 `checkBanned`；报名状态只用 `GET .../joined`；403 仅在用户主动报名时处理。
- **原因**：用写接口做旁路探测。
- **收益**：避免「看一眼就报名」。
- **证据**：`GameDetail.vue` ~280、~299–308。

### N04 · 建队成功、报名失败 →「有队无参赛」

- **问题**：`GameTeams` 先建队/入队，再 `joinCompetition()`。私有赛缺邀请码时后者失败，队伍已存在，错误易被当成建队失败。
- **改法**：两步错误拆开提示；报名失败引导填邀请码。可选：后端同事务支持 `game_id` + `invite_code`。
- **原因**：队伍与参赛非原子。
- **收益**：少脏数据、少清队工单。
- **证据**：`GameTeams.vue` create/join 后再调 `joinCompetition`。

---

## B · P1 功能半边（一侧有、一侧缺或不接）

### N10 · `/archive` 是假数据

- **问题**：页面写死两条静态条目；后端已有赛事归档 / `game_type=archived` / 训练场侧栏。
- **改法**：拉已归档 competitions（或训练侧栏 archived），链到训练/详情。
- **原因**：占位页未接 API。
- **收益**：归档库有真实内容。
- **证据**：`Archive.vue` 硬编码 `archives`；后端 `competitions` archive / training sidebar。

### N11 · 退赛：后端有，前端无

- **问题**：`POST /api/competitions/<id>/leave` 存在；前端只有退队（`/api/teams/.../leave`），无退赛。
- **改法**：详情或战队页加「退出本赛」，调 competitions leave。
- **原因**：只实现了报名半边。
- **收益**：误报名（含 N03）可自助退出。
- **证据**：`competitions.py` leave；前端无 competitions leave 调用。

### N12 · 赛事 notices：后端有，做题台未展示

- **问题**：`GET /api/ctf/games/<id>/notices` 存在；`polling.js` 有 notices 间隔，做题台未拉公告/血讯列表展示。
- **改法**：Workspace / 详情展示 notices，或确认血讯已由其他通道覆盖后删死配置。
- **原因**：接口与轮询配置悬空。
- **收益**：赛时公告可达选手。

### N13 · 动态附件包 ✅

- **状态**：BE CRUD + `meta.status=ready`；FE `DynamicPackageManager` 已接真上传/删除。

### N14 · 启容器排队 ✅

- **状态**：`async=1` → 202 + `job_id`；`GET /container-jobs/<id>`；Workspace 展示排队位次并轮询。

### N15 · 文件管理：后端有，管理菜单无

- **问题**：`/api/admin/platform/files*` 意图存在；`adminMenu` 无「文件」页。且蓝图自带前缀 + `register(..., url_prefix=/api/admin/platform)` 可能双重前缀，需先实测真实 URL。
- **改法**：核对真实路径 → 加管理页，或下线未用 API。
- **原因**：孤儿文件靠脚本，运营不可见。
- **收益**：可自助清存储。

### N16 · API Token：后端有，前端无

- **问题**：`/api/tokens` CRUD 存在；无管理 UI。
- **改法**：简单创建/列表/吊销页，或文档说明仅脚本发钥。
- **原因**：自动化集成需要可审计发钥。
- **收益**：少改库发 Token。

### N17 · 赛季 Season ✅

- **状态**：`/api/admin/seasons` CRUD + 管理端「seasons」页（`SeasonManager`）。

### N18 · OAuth：列表壳 ✅ / 完整授权仍半成品

- **状态**：`GET /api/auth/oauth/providers` + 启动跳转；无完整 callback/绑定。配置 `oauth_providers`+`auth_url` 后可跳转。
---

## C · P1/P2 合同与技术债

### N20 · 鉴权双轨残留（Cookie vs Bearer）

- **问题**：主路径应 Cookie + `withCredentials`；多处管理页仍读 `localStorage.neepu_token` 拼 Bearer（`CtfManagement` 队伍相关 raw fetch、`UserManagement`、`SystemSettings`、`LogAudit` 等）。N01 修复后 token 常为空，同域 Cookie 可能仍能过，但契约脆弱。
- **改法**：管理请求统一走 `authFetch` / axios（只 Cookie）；删除 Bearer 拼装。
- **原因**：双轨在跨域、过期、清存储时会偶发 401。
- **收益**：会话行为可预期。

### N21 · 三套 API 面并存

- **问题**：选手主路径 `/api/competitions` + `/api/challenges`；榜/部分只读 `/api/ctf`；兼容 `/api/container`、遗留 `/api/games`、`/api/admin/games*`。前端主路径已避开 `/api/games`，后端仍注册全套。
- **改法**：文档标 canonical；legacy 只读/限流；禁止新功能扩旧前缀。
- **原因**：选错路径会导致计分/权限不一致（如旧 `submit-flag` 不走完整计分）。
- **收益**：联调与废弃可控。

### N22 · 未挂路由死代码含「正确旧逻辑 / 错误合同」

- **问题**：`Games.vue`、`CTFCompetitions.vue`、`ChallengeCard`、`ContainerChallenge`、`Admin.vue`、`TerminalView` 等未进现网 router，却含邀请码 join、旧 `submit-flag`、Bearer 等。后人复用易引入错误或「好逻辑没迁到主路径」。
- **改法**：移入 `_legacy/` 或删除；需要的逻辑（如邀请码）迁到 `GameDetail`/`GameTeams`（见 N02）。
- **原因**：死代码是复发源。
- **收益**：主路径唯一真相。

### N23 · 容器 TTL / 延期合同不一致

- **问题**：主路径启容器与兼容 `/api/container` 默认 TTL 可能不同；`extend` 固定 +1h 且可忽略 body。
- **改法**：统一默认值；前端只展示后端返回的 `expires_at`。
- **原因**：用户看到的「还能用多久」与真实过期不一致。
- **收益**：倒计时可信。

### N24 · 账号注销 ✅

- **状态**：`POST /api/auth/delete-account`（密码 + confirm）+ `AccountDelete.vue` 真流程。

---

## D · 已对齐（勿重复开工）

| 模块 | 状态 |
|------|------|
| 注册 / 邮箱验证 / 找回改密 / profile / logout / `/me` | OK（登录成功 UX 除外，见 N01） |
| Captcha 组件 + 配置开关（Auth 已接组件） | OK（仍受 N01 成功分支影响） |
| 落地 / Home / 轮播 / 公告 / Wiki / 外赛 / 维护遮罩 | OK |
| 公开赛列表→详情→组队→做题台→提交/提示/Hammer/附件 | OK |
| 容器启停延期 + `connection_url`（Workspace） | OK |
| 积分榜 + 时间线曲线；管理端导出 CSV | OK |
| 管理 CTF：赛事 CRUD/归档/赛道/题目/PCAP/作弊/首解/统计/Hammer | OK（部分仍有 Bearer 散落，见 N20） |
| 管理平台：仪表盘/用户/内容/公告/轮播/配置/日志 | OK |
| 前端主路径已无 `/api/games` | OK |

---

## E · 暂缓 / 不做

| ID | 项 | 说明 |
|----|-----|------|
| G42* | WebSocket / 真交互终端 | 未做；已提供实例日志 MVP |
| X01 | Task19 全套管理子页 1:1 | 统一 `/admin/ctf` |
| X02 | 完整 OAuth 授权回调 | 仅 providers 列表 + auth_url 跳转 |
| X03 | 换前端栈 | 成本过高 |

---

## 建议修改顺序

1. **N01** 登录成功判定（立刻）  
2. **N03** 去掉误报名 `checkBanned`  
3. **N02 + N04** 私有赛邀请码 + 半完成态提示  
4. **N11** 退赛按钮（配合 N03）  
5. **N20** 清管理端 Bearer  
6. **N10 / N12** 归档真数据、notices  
7. **N22** 隔离死代码（并把邀请码逻辑迁走）  
8. **N15 / N16** 文件台、API Token（N13/N14/N17/N18/N24 已收）  

---

## 与旧 `G*` 清单关系

| 旧结论 | 本次结论 |
|--------|----------|
| G01–G26「办赛/管理体验已收口」 | **公开赛侧大体成立**；但 **N01–N04 未进旧清单，必须重开为 P0** |
| G18 验证码已完成 | Captcha UI 已接；仍受 N01 登录分支拖累 |
| G21 维护模式已完成 | 成立（`App.vue` overlay） |
| G40–G43 暂缓 | **已推翻**：G40/G41/G43 已落地；G42 仅日志 MVP |
| G27–G35 文件/Token/赛季/OAuth | 赛季/注销已收；文件台/Token/完整 OAuth 仍开 |

---

## 完成记录

| 日期 | 备注 |
|------|------|
| 2026-07-21 | 全局重扫；纠正「P0/P1 全绿」；以 N01–N24 为现行缺口清单 |
| 2026-07-21 | 直接改 BE+FE：G40 动态包、G41 排队、G42 日志 MVP、G43 协管、赛季/注销/OAuth 列表 |
