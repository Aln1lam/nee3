# 西电 CTF 终端 — 前端整体复刻 Prompt

> ⚠️ **本文件已拆分为小任务**，建议改用 `xidian-ctf-frontend-tasks/` 目录下的任务文件逐条执行。
> 索引与执行顺序见 → [`xidian-ctf-frontend-tasks/00-README.md`](xidian-ctf-frontend-tasks/00-README.md)

> 平台：https://ctf.xidian.edu.cn/
> 底层：Ret2Shell v3（SolidJS + TailwindCSS + Fluent Icons）
> 用途：将此 Prompt 整体交给 AI，复刻西电 CTF 终端完整前端（**推荐拆分为小任务执行**）

---

## 你的任务

请完整实现「西电 CTF 终端」CTF 竞赛平台的前端。这是一个中文界面的夺旗赛（CTF）平台，风格为极客/终端美学，功能覆盖赛事、训练、做题、排行榜、队伍、知识库、公告、用户系统等全部模块。请严格遵循以下规格，一次性输出可运行的前端工程（或按模块逐步实现但保持风格统一）。

---

## 一、技术栈与工程约束

**框架与库：**
- SolidJS 1.9+、@solidjs/router（路由懒加载）
- TailwindCSS 4、@iconify-json/fluent 图标集
- TanStack Solid Query（API 数据缓存）
- luxon（时间处理）、clsx（样式组合）
- OverlayScrollbars（自定义滚动条）、solid-transition-group（页面过渡动画）
- ECharts（图表）、xterm.js + FitAddon/WebLinksAddon/CanvasAddon（终端）
- unified 流水线（remark-gfm + remark-math + rehype-katex + rehype-pretty-code/Shiki + rehype-sanitize）渲染 Markdown
- @modular-forms/solid（表单校验）、ky（HTTP 客户端）
- sakana-widget（/magic/sakana 彩蛋页）

**全局交互原则：**
- 路由懒加载，页面切换使用 fade/dive 过渡动画
- API 离线/502 跳转 /sigtrap 错误页；503 显示维护状态
- 前后端版本不匹配时 Toast 警告
- 未验证邮箱用户 Toast 引导至设置页
- 首次访问 Cookie 策略 Toast
- 响应式：lg 以下汉堡菜单 Popover，lg 以上水平导航

---

## 二、视觉设计系统

**美学定位：** 黑客终端 / 极客风格，半透明毛玻璃层，精致但不花哨。

**色彩：**
- 主色 #0078D6（蓝）
- 强调/错误色 #f83030（红）
- 语义色：success / warning / error / info
- 深色/浅色双主题，支持「跟随系统」

**背景：**
- 固定全屏 SVG 电路走线动画（draw-line 描边，opacity 10%）
- 半透明遮罩 bg-layer/90

**顶栏 TitleBar（sticky，高 64px）：**
- bg-layer/60 + backdrop-blur-sm
- 左侧：LogoAnimate 动画 Logo（24×24），进入比赛页切换为比赛 logo；平台名/比赛名打字机宽度动画
- 中间：导航链接（见第三节）
- 右侧：比赛倒计时 + TimeProgress | WebSocket Reflector X | 提示消息 | 主题 | 语言 | 用户 Avatar
- 可选高亮横幅 highlight_banner（警告色，可关闭）
- 打印模式：顶栏显示平台名 + 当前时间

**组件库（统一封装）：**
Button、Card、Link、Input、Popover、Divider、Avatar、Tag、Chart、Splitter、Timer、TimeProgress、LoadingTips、Article、Captcha、Select、Picture、Tabs

**动画：**
- 首页首次加载全屏打字机遮罩：[ 平台名 ]_ 光标闪烁
- LogoAnimate 品牌动画
- 排行榜进入时 Cover 动画：「{用户名} 登场！」

---

## 三、西电平台定制配置

```yaml
平台名: 西电 CTF 终端
导航文案:
  - 知识    → /wiki
  - 训练    → /training
  - 赛事    → /games
  - 公告    → /bulletin
首页副标题: 为世界上所有美好而战 → /magic/sakana
Footer:
  - 链接: 西安电子科技大学 网络安全与密码学部 → https://ce.xidian.edu.cn/
  - ICP: 陕ICP备05016463号 → https://beian.miit.gov.cn/
比赛内导航: 题目 | 积分板 | 队伍管理 | 返回
特有组件: WebSocket Reflector X（wsrx 题目环境连接器，顶栏工具栏）
西电特色:
  - 连接题目在线环境需「使用连接器」（Wiki 有教程）
  - tcp 类题目需 netcat 访问（Wiki 有教程）
  - 维护横幅示例: 「西电 CTF 终端预计将于 XX:XX ~ XX:XX（CST）期间进行升级维护...」
```

---

## 四、路由与页面规格（全部实现）

### 4.1 全局 Layout `/`

**壳层结构：**
```
<Background />          // SVG 电路背景
<TitleBar />            // 顶栏（含横幅）
{children}              // 页面内容
<Toasts />              // 全局通知
<SplashAnimation />     // 首页打字机遮罩（仅首次访问 /）
```

**TitleBar 导航逻辑：**
- 非比赛页（GlobalNav）：知识 | 训练 | 赛事 | 公告 | 管理（按权限显示）
- 比赛页（GameNav）：题目 | 积分板 | 队伍管理/加入比赛 | 比赛管理（管理员）| 返回
- 比赛进行中：顶栏显示当前 timeline 阶段标签 + 倒计时 Timer + TimeProgress 进度条
- 训练场模式：显示「永久开放」TimeProgress

---

### 4.2 首页 `/`

全屏单页 snap 滚动，内容垂直居中：
- 大标题：`[ 西电 CTF 终端 ]_`（3xl bold，主色闪烁光标 `_`）
- 红色外链副标题：「为世界上所有美好而战」→ /magic/sakana
- 底部 Footer：(C) 2022-当前年 + 网安学部链接 + ICP 备案号
- Info Popover（ⓘ）：Ret2Shell 版本卡（LogoAnimate + REL/DEV 标签）、support@ret.sh.cn、GitHub、ret.sh.cn
- 若配置 zen_game 则自动跳转该比赛

---

### 4.3 账号模块 `/account/*`

#### 登录 `/account/login`
双栏 Card（max-w-3xl，移动端上下堆叠）：
- 左栏表单：账号(≥4字符)、密码(8-40位含大小写+数字)、图形验证码 Captcha
- 校验失败：清空密码并刷新验证码
- 忘记密码链接 → /account/forgot
- 右栏：LogoAnimate 大尺寸 + 注册引导链接
- OAuth：单提供者直链，多提供者 Popover 列表
- 登录成功：redirect 参数同源校验后跳转，否则回首页
- 已登录自动重定向

#### 注册 `/account/register`
同登录布局，字段：账号、昵称、密码、确认密码、邮箱、验证码、图形验证码

#### 忘记/重置 `/account/forgot`、`/account/reset`
居中 Card，邮箱/账号 + 验证码发送；reset 页 token 验证 + 新密码表单

#### 用户设置 `/account/settings/*`（Sidebar 布局）
侧边栏菜单：
- 用户信息 `/info`
- 修改密码 `/password`
- 第三方认证服务 `/oauth`
- 删号跑路 `/mov-esp-ebp-pop-ebp`（开发者彩蛋）

`/info` 表单字段：
- 用户名（disabled 只读）
- 昵称（可编辑）
- 头像上传（Avatar 字母 fallback，如 "A"）
- 邮箱（必填）
- 个人简介（Ace Markdown 编辑器，角标 MARKDOWN）
- 保存按钮

#### OAuth/验证中转 `/account/oauth`、`/account/verify`
极简 Loading 页 → 成功/失败 Toast → 自动跳转

#### 用户菜单 Popover（顶栏 Avatar 触发）
```
用户信息卡：昵称 + 0x{6位hex} ID（如 0x001f11）
├── 临时用户识别码（Popover）
├── 用户设置 → /account/settings
└── 登出
```

---

### 4.4 赛事列表 `/games`

大屏左右分栏 snap 滚动：

**左侧 1/4（lg 可见）：**
- Host 权限显示「创建比赛」按钮（?create=true）
- 重点赛事分页列表（每页 5 个），URL ?key-page= & ?selected= 同步
- 条目：Mini L-CTF 2026、NewYear CTF 2026、MoeCTF 2025 等
- 底部「其他赛事」按钮

**右侧 3/4 Cover 区：**
- 背景大图（暗色 stars / 亮色 suzume 模糊背景）
- 比赛 logo + 名称 + 描述 + 时间范围
- 状态 Tag：已结束 / 进行中 / 报名中等
- 加载态：Spin 动画 + 随机提示文案

**底部 OtherGames 区：**
- 次要比赛网格卡片（托管赛：NewStar CTF、TGCTF、NPC²CTF 等）
- 标注「（托管）」
- 分页导航

---

### 4.5 比赛详情 `/games/:id`

Cover banner 落地页：
- 比赛 banner 图 + logo + 名称 + 描述
- 倒计时 Timer（根据阶段显示：报名/开始/结束/归档）
- 状态 Tag + 时间轴说明
- Markdown 比赛说明（Article 组件，管理员 ?edit=true 可 inline 编辑）
- 参赛 CTA：报名 / 进入题目 / 查看积分板
- 队伍被封禁：全屏红色 BannedWarning 遮罩
- 已归档：引导跳转 /training/:id

---

### 4.6 题目做题页（核心）`/games/:id/challenges`（需登录）

**布局：SidebarLayout**

**左侧 ChallengeList：**
- 搜索框：「搜索名称或者标签」
- 分类 Tab 按钮组：
  - 安全杂项 | 从此开始 | 二进制漏洞审计 | 密码学 | 逆向工程 | Web安全与渗透测试
- 题目卡片列表（分数、解出状态、一血标记）
- URL ?challenge= 同步选中

**右侧 Splitter 上下分栏：**

*上半 — Intro 题面：*
- Markdown 渲染（代码高亮、数学公式、外链）
- 题目标题 banner：名称 + solve 计数（如 "0 solve"）
- 附件区：「附件:」+ 可点击下载按钮（如 handbook_2025.pdf）
- 标签 Tag（如「从此开始」）

*下半 — BottomPanel Tab 栏：*

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
- 底部 flag 提交（提示 ctrl+shift+V 粘贴）
- 显示容器连接信息
- 题目上方文件名和「启动」按钮可点击（下载附件 / 启动在线环境）
- tcp 类服务标注 tcp，提示使用 netcat

**顶部额外区域（比赛模式）：**
- Welcome 组件（比赛欢迎/规则摘要 Tab）
- Team 组件（当前队伍信息）
- Notifications（比赛公告推送）

**交互逻辑：**
- 未登录跳转 /account/login?redirect=...
- 比赛未开始且非管理员：Toast 警告并退回
- 已归档自动跳转 /training/:id
- 未读 Hammer 消息 Toast 提醒，点击跳转对应题目
- 管理员可一键上/下架题目（Popover 确认对话框）
- URL ?tab= 同步当前 Tab

---

### 4.7 训练场 `/training` 及 `/training/:game`

**Sidebar：**
- 标题链接：「练习场列表」
- 分组「训练」：Web 安全审计、强壮密码人、安全杂项、二进制漏洞审计、Flare-on Mirrors、密码技术能力提升
- 分组「赛事」（归档比赛）：Mini L-CTF、MoeCTF 等
- 快捷链接：查看比赛信息 | 返回

**`/training` 主区默认：**
- 哑铃图标（w-24 h-24）+ 文案「开始今日份的训练！」
- ?create=true 时显示 CreatePlayground 表单（Host 权限）

**`/training/:game` 主区：**
- 复用 Challenge 组件（training=true）
- 永久开放，顶栏 TimeProgress 显示「永久开放」
- 欢迎页 Markdown 内容：
  - 「欢迎来到练习场！」
  - 无时间限制、无限重试、不计分
  - 归档比赛迁移规则（已解决/未解决标记说明）
  - 提示自动解锁、题解已开放、禁止抄题
  - 🔨 锤子不可用，请用其他反馈途径

---

### 4.8 积分板 `/games/:id/scoreboard`

三栏 + 图表布局：

**左侧 — 排名卡片列表：**
- 每队：名次徽章 + 队名（链接）+ 分数 pts
- 进度条 + 「N / 100 已解决」

**中间 — ECharts：**
- 积分随时间变化折线图（Canvas）
- 操作栏：刷新 | 导出(xlsx) | 显示隐藏队伍 toggle
- 筛选：「选择组织...」下拉（学院/组织 filter）

**右侧：**
- 标题 h1「积分板」
- 队伍详情列表
- Loading 文案：「正在除以 0...」
- 分页导航

**进入动画：**
- Cover 层：「{用户名} 登场！」+ 用户头像 + 比赛 logo

---

### 4.9 队伍模块 `/games/:id/teams/*`

| 路由 | 功能 |
|------|------|
| /choose | 选择创建或加入队伍 |
| /create | 创建队伍（队名、标签、邀请码） |
| /join | 输入邀请码加入 |
| / | 队伍公开列表 |
| /:teamId | 队伍详情管理 |

**队伍管理页 `/teams/:teamId`（Sidebar + 主内容）：**

*左侧队伍卡：*
- 队名 + 比赛 #hex ID
- 组织 Tag（如「无组织」）
- 成员列表（Avatar + 昵称 + 账号 #hex）

*主区「队伍管理」：*
- **队伍密钥**：readonly 文本框 + 复制按钮
- **队伍名称**：input（比赛结束后 disabled）
- **所属组织**：Select 下拉（可清除）
- **标签文字**：input（显示在排行榜昵称下方，可自由填写）
- 按钮：保存 | 离开（Popover 二次确认）
- **得分曲线**：ECharts Canvas
- **解题状况**：时间线列表
  - 格式：「成员 {昵称} 解出了题目 {题目名}。 {分数} pts {时间}」
  - 可点击跳转对应题目
- **额外分数变动**：空态「没有额外分数变动」

---

### 4.10 知识库 `/wiki`

Sidebar 目录树：
- 如何使用这个平台？
- 从零开始的CTF之路
- 外链：「开发者文档」→ https://docs.ret.sh.cn/

主区默认：「想了解些什么？」

文章页 `/wiki/:article`：
- Markdown 渲染 + TOC 目录 + 锚点
- 西电特有文章：连接器使用教程、netcat 教程等

创建页 `/wiki/create`（编辑权限）

---

### 4.11 公告 `/bulletin`

列表页：
- 标题 h1「公告」
- 条目：标题 + 日期（如「服务器系统升级通知 2026-07-08」）
- 分页（1/2 ...）

详情页 `/bulletin/:article`：Markdown 渲染

创建页 `/bulletin/create`（管理员权限）

---

### 4.12 用户主页 `/users` 及 `/users/:id`

**列表 `/users`：** 用户搜索/排行

**详情 `/users/:id`（Sidebar + 主内容）：**

*Sidebar 用户卡：*
- Avatar（字母 fallback）+ 昵称 + 账号#hex（如 alnILam#001f11）
- 邮箱 mailto 链接
- 组织 Tag（如「无组织」）
- 权限 Tag：基础 | 已验证
- 注册日期（如「注册于 2024-08-10」）

*主区：*
- **生涯数据**：双 ECharts Canvas + 「全部赛事」筛选下拉
- **参与赛事**：时间线（「作为 {队名} 成员参与了 {比赛名}。 {时间}」）
- 空态文案：「生命不息，探索不止……」
- **个人介绍**：Article 渲染（默认「这位神秘的黑客什么也没有留下...」）

---

### 4.13 Magic 彩蛋 `/magic/*`

**/magic/about：**
- Ret2Shell Logo + 版本 + REL/DEV 标签
- 许可证说明 Tag 组（GPL / copyleft / 商用限制 / 禁止用户收费）
- Developers / Contributors 名单（Reverier-Xu 等）
- 「感谢使用」SVG 插图 + Reverier 动画角色

**/magic/sakana：**
- sakana-widget 互动页（首页副标题链入）
- 文案：「为世界上所有美好而战」

---

### 4.14 平台管理 `/admin/*`（需管理员权限）

Sidebar 导航：
- 统计 `/admin/statistics`（默认跳转）
- 用户管理 `/admin/users`
- 验证码策略 `/admin/captcha`
- 邮件配置 `/admin/email`
- 平台信息编辑 `/admin/edit`
- 操作日志 `/admin/logs`
- K8s 集群 `/admin/cluster`
- 数据同步 `/admin/sync`
- 媒体管理 `/admin/media`
- OAuth 配置 `/admin/oauth`
- 流量统计 `/admin/traffic`
- 生命周期 `/admin/lifecycle`

统一 SidebarLayout + 表格/表单/图表

---

### 4.15 比赛管理 `/games/:id/admin/*`（需比赛管理员权限）

Sidebar 导航：
- 概览 dashboard + 实时聊天 ChatList
- 统计 `/statistics`
- 编辑 `/edit`
- 规则 `/rules`
- 访问策略 `/policies`
- 组织架构 `/organize`
- Hammer 管理 `/hammers`
- 队伍管理 `/teams`
- 实时监控 `/monitor`
- 事件日志 `/events`
- Git 集成 `/git`
- 流量分析 `/traffic`（Rune 脚本）
- 生命周期 `/lifecycle`
- Flag 提交记录 `/captures`
- 时间线编辑 `/timeline`
- 删除比赛 `/delete`

---

### 4.16 错误页 `/sigtrap/*`

极客风格 HTTP 错误页系列（统一 sigtrap layout）：

| 路由 | 含义 |
|------|------|
| /sigtrap/401 | 未授权 |
| /sigtrap/403 | 权限不足，拒绝访问 |
| /sigtrap/404 | 未找到 |
| /sigtrap/412 | 前提条件失败 |
| /sigtrap/418 | 我是茶壶（彩蛋） |
| /sigtrap/500 | 服务器错误 |
| /sigtrap/502 | 网关错误 |
| /sigtrap/unknown | 未知错误 |

每页：大号 HTTP 状态码 + 技术风/幽默文案 + 返回首页按钮

---

## 五、共享组件详细规格

### 5.1 Terminal（做题终端）
```
- xterm.js + FitAddon + WebLinksAddon + CanvasAddon
- ANSI 颜色渲染（ansi_up）
- WebSocket 实时输出
- 底部 flag 提交 Input
- 提示：ctrl+shift+V 粘贴 flag 后回车提交
```

### 5.2 Markdown Article
```
unified 流水线：
  remark-gfm → remark-math → remark-rehype
  → rehype-katex → rehype-pretty-code(Shiki)
  → rehype-slug → rehype-autolink-headings
  → rehype-external-links → rehype-sanitize → rehype-stringify
支持：TOC 目录、代码块复制、数学公式、打印友好
```

### 5.3 Captcha（图形验证码）
```
- 点击图片刷新
- captcha_id + captcha_answer 双字段
- 登录/注册必填，最少 4 字符
```

### 5.4 InstanceBox / WebSocket Reflector X
```
@xdsec/wsrx 动态容器状态指示器（顶栏按钮）
Popover 显示：
- 实例列表（运行中/启动中/已停止）
- 延期、销毁操作
- 西电环境连接题目必需此连接器
```

### 5.5 ThemeBox（主题切换）
```
Popover：
- 深色/浅色切换按钮（月亮/太阳图标）
- 「跟随系统」toggle
```

### 5.6 NotificationBox（提示消息）
```
Popover 显示 Toast 历史列表
有未读时图标变为 alert-badge 填充态 + 主色
```

### 5.7 Toasts（全局通知）
```
level: info | warning | error
支持 accept/reject 按钮 + 自定义标签
自动消失或手动关闭
```

### 5.8 Scoreboard Charts
```
ECharts 折线图：队伍积分随时间变化
支持按组织/学院筛选
导出 xlsx（@e965/xlsx）
```

### 5.9 Challenge Hammer（🔨 锤子反馈）
```
题目内 Tab，选手与出题人/裁判聊天
实时消息推送 → Toast 提醒
训练场模式 disabled
```

### 5.10 LoadingTips
```
随机技术风加载文案，如：
- 「正在除以 0...」
- 其他 randomTips 数组文案
```

---

## 六、API 对接约定

前端通过 REST API 与 Ret2Shell 后端通信（ky 客户端）：

```
GET  /api/platform/info     → 平台名、banner、footer、zen_game 等配置
GET  /api/platform/version  → 版本号（前后端兼容性检查）
POST /api/account/login     → 登录
GET  /api/account/profile   → 用户信息
GET  /api/game              → 比赛列表
GET  /api/game/:id          → 比赛详情
GET  /api/game/:id/challenge→ 题目列表
GET  /api/game/:id/challenge/:cid → 题目详情
POST /api/game/:id/challenge/:cid/submit → 提交 flag
GET  /api/game/:id/scoreboard → 排行榜
GET  /api/team/self         → 当前用户队伍
GET  /api/media?hash=...    → 媒体文件（logo/banner/头像）
```

权限模型：
- 普通用户：做题、队伍、训练
- Host：创建比赛/训练场
- 比赛管理员：/games/:id/admin/*
- 平台管理员（Statistics/DevOps/User 权限）：/admin/*

---

## 七、响应式断点

```
sm: 640px   → 移动端汉堡菜单
md: 768px
lg: 1024px  → 切换为水平导航 + 左右分栏
xl: 1280px
2xl: 1536px
```

移动端：
- TitleBar 左侧汉堡 Popover 收纳全部导航 + 主题/通知/语言子面板
- Card/表单改为全宽堆叠
- 排行榜/做题页改为上下堆叠

---

## 八、交付要求

1. **完整性**：实现第四节全部路由，不可遗漏 sigtrap 错误页和 magic 彩蛋
2. **一致性**：所有页面共用 Layout/TitleBar/Background/Toasts，视觉风格统一
3. **中文**：所有用户可见文案使用中文（导航、按钮、提示、空态文案）
4. **西电定制**：平台名、导航文案、Footer、维护横幅、连接器提示必须与第三节配置一致
5. **可扩展**：通过 `/api/platform/info` 动态加载平台配置，硬编码仅作为 fallback
6. **无障碍**：按钮带 title/aria-label，表单字段带 label，颜色对比度达标

---

## 九、参考资源

- 开源代码：https://github.com/ret2shell/ret2shell （web/src 目录）
- 官方文档：https://docs.ret.sh.cn/
- 西电实例：https://ctf.xidian.edu.cn/
- MoeCTF 题目仓库：https://github.com/XDSEC/MoeCTF_2025

---

*此 Prompt 由 ctf.xidian.edu.cn 前端逆向分析生成，整合 Ret2Shell 源码审计与线上实测结果。*
