# Task 04：功能型共享组件

> **技术栈**：Vue 3 + Naive UI + marked + xterm.js + ECharts
> **前置依赖**：Task 03
> **后续任务**：09-challenges、11-scoreboard、13-wiki 等
> **状态**：✅ 已完成 — 演示见 `/dev/components` 下半部分

## 组件目录

统一从 `@/components/shared` 导出：

| 组件 | 文件 | 说明 |
|------|------|------|
| `Terminal` / `FlagTerminal` | `shared/Terminal.vue` | xterm.js + WebSocket + flag 提交 |
| `Article` | `shared/Article.vue` | Markdown + TOC + 代码复制 |
| `Captcha` | `shared/Captcha.vue` | 图形验证码 |
| `InstanceBox` | `shared/InstanceBox.vue` | WSRX 连接器 |
| `ScoreboardChart` | `shared/ScoreboardChart.vue` | 积分折线图 + 导出 |
| `HammerPanel` | `shared/HammerPanel.vue` | 🔨 锤子反馈 |
| `SidebarLayout` | `shared/SidebarLayout.vue` | 侧边栏布局 |

根目录 `Captcha.vue`、`FlagTerminal.vue`、`InstanceBox.vue` 等为兼容 re-export。
## 4.1 Terminal（做题终端）

```
- xterm.js + FitAddon + WebLinksAddon + CanvasAddon
- ANSI 颜色渲染（ansi_up）
- WebSocket 实时输出
- 底部 flag 提交 Input
- 提示：ctrl+shift+V 粘贴 flag 后回车提交
- 容器 resize 时 FitAddon 自适应
```

## 4.2 Markdown Article

```
unified 流水线：
  remark-gfm → remark-math → remark-rehype
  → rehype-katex → rehype-pretty-code(Shiki)
  → rehype-slug → rehype-autolink-headings
  → rehype-external-links → rehype-sanitize → rehype-stringify

支持：TOC 目录、代码块复制按钮、数学公式、打印友好
```

Props 建议：`content: string`、`showToc?: boolean`、`editable?: boolean`（管理员 inline 编辑预留）

## 4.3 Captcha（图形验证码）

```
- 点击图片刷新
- captcha_id + captcha_answer 双字段
- 登录/注册必填，答案最少 4 字符
- API: GET /api/captcha（按实际后端调整）
```

## 4.4 InstanceBox / WebSocket Reflector X

```
顶栏按钮，Popover 显示：
- 实例列表（运行中/启动中/已停止）
- 延期、销毁操作
- 西电环境连接题目必需此连接器
- 可先用 mock 数据，接口 @xdsec/wsrx
```

## 4.5 Scoreboard Charts

```
ECharts 折线图：队伍积分随时间变化
支持按组织/学院筛选
导出 xlsx（@e965/xlsx）
```

## 4.6 Challenge Hammer（🔨 锤子反馈）

```
题目内 Tab 组件
选手与出题人/裁判聊天
实时消息推送 → 触发全局 Toast
训练场模式 props.disabled = true
```

## 4.7 SidebarLayout

通用侧边栏 + 主内容布局，供做题、设置、管理页复用：
- 左侧固定宽度 Sidebar（移动端可折叠）
- 右侧 `{children}` 主区

## 验收标准

- [ ] Article 正确渲染 GFM、代码高亮、数学公式
- [ ] Terminal 可连接 mock WebSocket 并显示输出
- [ ] Captcha 刷新与表单字段联动
- [ ] Hammer 收发消息 + Toast 提醒
- [ ] SidebarLayout 在移动端可折叠
