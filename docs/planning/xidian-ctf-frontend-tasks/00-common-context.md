# 公共上下文（所有任务共用，只读参考）

> 执行任何子任务前请先阅读本文件。各任务文件不再重复完整技术栈说明。

---

## 技术栈与工程约束

> **本项目实际技术栈（沿用 `frontend/` 现有工程，不迁移 SolidJS）**

**框架与库：**
- Vue 3 + Vue Router 4（路由懒加载）
- Vite 5 构建
- Naive UI 组件库 + @vicons 图标
- Axios HTTP 客户端（含 401/502/503 拦截）
- marked + vditor（Markdown 渲染/编辑）
- ECharts（图表）、vue-command（终端模拟）
- clsx / tailwind-merge（样式组合，按需）
- 主题：CSS 变量 + `/public/themes/{light,dark}.css`，支持跟随系统

**目标平台参考（Ret2Shell 西电实例）：**
- 视觉与交互对齐 https://ctf.xidian.edu.cn/
- 开源参考：https://github.com/ret2shell/ret2shell （web/src）

**全局交互原则：**
- 路由懒加载，页面切换使用 fade/dive 过渡动画
- API 离线/502 跳转 /sigtrap 错误页；503 显示维护状态
- 前后端版本不匹配时 Toast 警告
- 未验证邮箱用户 Toast 引导至设置页
- 首次访问 Cookie 策略 Toast
- 响应式：lg 以下汉堡菜单 Popover，lg 以上水平导航

---

## 视觉设计系统

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
- 中间：导航链接
- 右侧：比赛倒计时 + TimeProgress | WebSocket Reflector X | 提示消息 | 主题 | 语言 | 用户 Avatar
- 可选高亮横幅 highlight_banner（警告色，可关闭）
- 打印模式：顶栏显示平台名 + 当前时间

**动画：**
- 首页首次加载全屏打字机遮罩：[ 平台名 ]_ 光标闪烁
- LogoAnimate 品牌动画
- 排行榜进入时 Cover 动画：「{用户名} 登场！」

---

## 西电平台定制配置

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

## API 对接约定

前端通过 REST API 与 Flask 后端通信（**Axios** 客户端，`main.js` 全局注入）：

**本项目已有接口（优先对接）：**
```
GET  /api/platform/info       → 平台配置（name/nav/footer/banner 等）
GET  /api/platform/version    → 版本兼容性检查
GET  /api/competitions/:id    → 比赛详情（TitleBar 倒计时等）
GET  /api/captcha             → 图形验证码
POST /api/auth/login          → 登录
GET  /api/auth/me             → 当前用户
```

**Ret2Shell 参考接口（逐步对齐）：**

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

**权限模型：**
- 普通用户：做题、队伍、训练
- Host：创建比赛/训练场
- 比赛管理员：/games/:id/admin/*
- 平台管理员（Statistics/DevOps/User 权限）：/admin/*

---

## 响应式断点

```
sm: 640px   → 移动端汉堡菜单
md: 768px
lg: 1024px  → 切换为水平导航 + 左右分栏
xl: 1280px
2xl: 1536px
```

移动端：TitleBar 汉堡 Popover、Card 全宽堆叠、排行榜/做题页上下堆叠。

---

## 交付要求（全局）

1. **完整性**：实现全部路由，不可遗漏 sigtrap 错误页和 magic 彩蛋
2. **一致性**：所有页面共用 Layout/TitleBar/Background/Toasts
3. **中文**：所有用户可见文案使用中文
4. **西电定制**：平台名、导航、Footer、连接器提示与上文配置一致
5. **可扩展**：通过 `/api/platform/info` 动态加载配置，硬编码仅 fallback
6. **无障碍**：按钮带 title/aria-label，表单字段带 label
