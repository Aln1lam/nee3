# Task 09：做题页（核心）`/games/:id/challenges`

> **前置依赖**：Task 04（Terminal、Article、Hammer、SidebarLayout）、Task 03（Splitter、Tabs）
> **复杂度**：最高，建议单独一次完整执行

---

## 本任务目标

实现 CTF 平台核心做题体验，含题目列表、题面、终端、多 Tab 面板。

## 布局：SidebarLayout

### 左侧 ChallengeList

- 搜索框：「搜索名称或者标签」
- 分类 Tab：安全杂项 | 从此开始 | 二进制漏洞审计 | 密码学 | 逆向工程 | Web安全与渗透测试
- 题目卡片：分数、解出状态、一血标记
- URL `?challenge=` 同步选中

### 右侧 Splitter 上下分栏

**上半 — Intro 题面：**
- Article Markdown 渲染
- 标题 banner：名称 + solve 计数（如 "0 solve"）
- 附件区：「附件:」+ 下载按钮
- 标签 Tag

**下半 — BottomPanel Tab 栏：**

| Tab | 选手 | 管理员 | 训练场 |
|-----|------|--------|--------|
| 终端 | ✅ | ✅ | ✅ |
| 提示 | ✅ | ✅ | ✅（自动解锁）|
| 锤子 🔨 | ✅ | ✅ | ❌ disabled |
| 题解 | 归档后 | ✅ | ✅ |
| 统计 | ❌ | ✅ | ❌ |
| 附件管理 | ❌ | ✅ | ❌ |
| 实例管理 | ❌ | ✅ | ❌ |
| 判题脚本 | ❌ | ✅ | ❌ |
| 题目设置 | ❌ | ✅ | ❌ |

**终端 Tab：**
- xterm.js 全功能终端
- 底部 flag 提交（提示 ctrl+shift+V）
- 容器连接信息
- 文件名 +「启动」按钮（下载附件/启动在线环境）
- tcp 类标注 tcp，提示 netcat

### 顶部额外区域（比赛模式）

- Welcome（比赛欢迎/规则摘要 Tab）
- Team（当前队伍信息）
- Notifications（比赛公告推送）

## 交互逻辑

- 未登录 → `/account/login?redirect=...`
- 比赛未开始且非管理员 → Toast 警告并退回
- 已归档 → 自动跳转 `/training/:id`
- 未读 Hammer 消息 → Toast 提醒，点击跳转题目
- 管理员可一键上/下架题目（Popover 确认）
- URL `?tab=` 同步当前 Tab

## 验收标准

- [x] 题目列表搜索与分类过滤
- [x] 选中题目 URL 同步
- [x] 终端 WebSocket 连接 + flag 提交
- [x] Tab 权限按角色/模式显示
- [x] Hammer 消息 Toast
- [x] 管理员题目上下架
