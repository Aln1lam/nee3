# Task 10：训练场 `/training` 及 `/training/:game`

> **前置依赖**：Task 09（复用 Challenge 组件）
> **可并行**：与 11-scoreboard、12-teams 并行

---

## 本任务目标

实现练习场列表与训练模式做题（复用 Challenge 组件，`training=true`）。

## Sidebar

- 标题：「练习场列表」
- 分组「训练」：Web 安全审计、强壮密码人、安全杂项、二进制漏洞审计、Flare-on Mirrors、密码技术能力提升
- 分组「赛事」（归档）：Mini L-CTF、MoeCTF 等
- 快捷链接：查看比赛信息 | 返回

## `/training` 主区默认

- 哑铃图标（w-24 h-24）+「开始今日份的训练！」
- `?create=true` 时显示 CreatePlayground 表单（Host 权限）

## `/training/:game` 主区

- 复用 Challenge 组件（`training=true`）
- 顶栏 TimeProgress 显示「永久开放」
- 欢迎页 Markdown：
  - 「欢迎来到练习场！」
  - 无时间限制、无限重试、不计分
  - 归档比赛迁移规则说明
  - 提示自动解锁、题解已开放、禁止抄题
  - 🔨 锤子不可用

## 验收标准

- [x] Sidebar 分组与链接正确
- [x] 训练模式 Hammer Tab disabled
- [x] 提示 Tab 自动解锁
- [x] Host 可创建训练场
- [x] 与比赛做题页视觉一致
