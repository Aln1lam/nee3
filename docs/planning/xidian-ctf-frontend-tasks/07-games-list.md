# Task 07：赛事列表 `/games`

> **状态**：✅ 已完成
> **实现文件**：`components/GamesHub.vue`
---

## 本任务目标

实现赛事列表页，大屏左右分栏 snap 滚动布局。

## 左侧 1/4（lg 可见）

- Host 权限显示「创建比赛」按钮（`?create=true`）
- 重点赛事分页列表（每页 5 个）
- URL 同步：`?key-page=`、`?selected=`
- 条目示例：Mini L-CTF 2026、NewYear CTF 2026、MoeCTF 2025
- 底部「其他赛事」按钮滚动至 OtherGames 区

## 右侧 3/4 Cover 区

- 背景大图（暗色 stars / 亮色 suzume 模糊）
- 比赛 logo + 名称 + 描述 + 时间范围
- 状态 Tag：已结束 / 进行中 / 报名中等
- 加载态：Spin + LoadingTips 随机文案

## 底部 OtherGames 区

- 次要比赛网格卡片（NewStar CTF、TGCTF、NPC²CTF 等）
- 标注「（托管）」
- 分页导航

## API

- `GET /api/game` → 比赛列表
- 选中项 `GET /api/game/:id` → 详情展示

## 验收标准

- [ ] 左右分栏 lg 断点切换
- [ ] URL 参数与选中状态同步
- [ ] 点击比赛跳转 `/games/:id`
- [ ] Host 才显示创建按钮
- [ ] 加载态 LoadingTips 随机
