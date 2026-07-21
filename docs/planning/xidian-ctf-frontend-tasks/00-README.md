# 西电 CTF 终端 — 前端复刻任务拆分

> 原文件：`xidian-ctf-frontend-prompt.md`（612 行，过大不便单次执行）
> **实际工程**：`frontend/`（Vue 3 + Naive UI + Axios），任务已按此技术栈适配
> 平台：https://ctf.xidian.edu.cn/ | 底层：Ret2Shell v3

## 使用方式

1. **先读** `00-common-context.md`（技术栈、设计系统、西电配置、API、交付要求）
2. **技术栈固定**：沿用 `frontend/` 现有 **Vue 3 + Vite + Naive UI + Axios**，不迁移 SolidJS
3. **按顺序**执行各任务文件，每个文件可单独交给 AI 一次运行
3. 每个任务文件顶部标注了**前置依赖**，未完成的依赖不要跳过
4. 已完成的部分在任务中标注「复用已有」，避免重复实现

## 推荐执行顺序

| 序号 | 文件 | 内容 | 预估复杂度 |
|------|------|------|-----------|
| 0 | `00-common-context.md` | 公共上下文（只读参考） | — |
| 1 | `01-project-scaffold.md` | 工程初始化 + 路由骨架 | ★★☆ ✅ 已完成 |
| 2 | `02-global-layout.md` | 全局 Layout / TitleBar / Background | ★★★ ✅ 已完成 |
| 3 | `03-ui-components.md` | 基础 UI 组件库 | ★★☆ ✅ 已完成 |
| 4 | `04-shared-feature-components.md` | 功能型共享组件（终端/Markdown 等） | ★★★★ ✅ 已完成 |
| 5 | `05-homepage.md` | 首页 `/` | ★☆☆ ✅ 已完成 |
| 6 | `06-account.md` | 账号模块 `/account/*` | ★★★ ✅ 已完成 |
| 7 | `07-games-list.md` | 赛事列表 `/games` | ★★☆ ✅ 已完成 |
| 8 | `08-game-detail.md` | 比赛详情 `/games/:id` | ★★☆ ✅ 已完成 |
| 9 | `09-challenges.md` | 做题页（核心）`/games/:id/challenges` | ★★★★★ ✅ 已完成 |
| 10 | `10-training.md` | 训练场 `/training` | ★★★ ✅ 已完成 |
| 11 | `11-scoreboard.md` | 积分板 `/games/:id/scoreboard` | ★★★ ✅ 已完成 |
| 12 | `12-teams.md` | 队伍模块 `/games/:id/teams/*` | ★★★ ✅ 已完成 |
| 13 | `13-wiki.md` | 知识库 `/wiki` | ★★☆ ✅ 已完成 |
| 14 | `14-bulletin.md` | 公告 `/bulletin` | ★☆☆ ✅ 已完成 |
| 15 | `15-users.md` | 用户主页 `/users` | ★★☆ ✅ 已完成 |
| 16 | `16-magic.md` | 彩蛋页 `/magic/*` | ★☆☆ ✅ 已完成 |
| 17 | `17-sigtrap.md` | 错误页 `/sigtrap/*` | ★☆☆ ✅ 已完成 |
| 18 | `18-platform-admin.md` | 平台管理 `/admin/*` | ★★★★ ✅ 已完成 |
| 19 | `19-game-admin.md` | 比赛管理 `/games/:id/admin/*` | ★★★★★ ✅ 已完成 |

## 依赖关系

```
00-common-context
       │
       ▼
01-project-scaffold
       │
       ▼
02-global-layout ──► 03-ui-components
       │                    │
       └────────┬───────────┘
                ▼
     04-shared-feature-components
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
 05-home    06-account   07-games-list
                │           │
                │           ▼
                │      08-game-detail
                │           │
                └─────┬─────┘
                      ▼
              09-challenges（核心，依赖最多）
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   10-training   11-scoreboard   12-teams
        │
        ▼
  13-wiki / 14-bulletin / 15-users / 16-magic / 17-sigtrap
        │
        ▼
  18-platform-admin / 19-game-admin
```

## 每个任务的标准输出

- 新增/修改的文件列表
- 路由注册变更
- 与后端 API 的对接点（mock 或真实）
- 自测检查项（该任务范围内的）

## 参考资源

- 开源代码：https://github.com/ret2shell/ret2shell （web/src 目录）
- 官方文档：https://docs.ret.sh.cn/
- 西电实例：https://ctf.xidian.edu.cn/
