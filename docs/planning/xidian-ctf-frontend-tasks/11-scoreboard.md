# Task 11：积分板 `/games/:id/scoreboard`

> **前置依赖**：Task 04（Scoreboard Charts）、Task 03
> **可并行**：与 10-training、12-teams 并行

---

## 本任务目标

实现三栏积分板布局 + 进入 Cover 动画。

## 布局

### 左侧 — 排名卡片列表

- 每队：名次徽章 + 队名（链接）+ 分数 pts
- 进度条 + 「N / 100 已解决」

### 中间 — ECharts

- 积分随时间折线图（Canvas）
- 操作栏：刷新 | 导出(xlsx) | 显示隐藏队伍 toggle
- 筛选：「选择组织...」下拉

### 右侧

- 标题 h1「积分板」
- 队伍详情列表
- LoadingTips：「正在除以 0...」
- 分页导航

## 进入动画

Cover 层：「{用户名} 登场！」+ 用户头像 + 比赛 logo（首次进入播放）

## API

- `GET /api/game/:id/scoreboard`

## 验收标准

- [x] 折线图随数据更新
- [x] 组织筛选生效
- [x] xlsx 导出可用
- [x] Cover 动画播放一次
- [x] 移动端三栏改上下堆叠
