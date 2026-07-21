# Task 08：比赛详情 `/games/:id`

> **前置依赖**：Task 04（Article）、Task 07
> **后续任务**：09-challenges

---

## 本任务目标

实现比赛 Cover banner 落地页。

## 页面内容

- 比赛 banner 图 + logo + 名称 + 描述
- 倒计时 Timer（报名/开始/结束/归档各阶段）
- 状态 Tag + 时间轴说明
- Markdown 比赛说明（Article 组件）
- 管理员 `?edit=true` 可 inline 编辑说明
- **参赛 CTA**：报名 / 进入题目 / 查看积分板

## 特殊状态

- **队伍被封禁**：全屏红色 BannedWarning 遮罩
- **已归档**：引导跳转 `/training/:id`

## TitleBar 联动

- 进入本页及子路由时切换 GameNav
- 顶栏 Logo 切换为比赛 logo
- 比赛名打字机动画

## 验收标准

- [x] Timer 根据 timeline 阶段切换文案
- [x] CTA 按钮根据状态显示（未报名/已报名/进行中/已结束）
- [x] 封禁遮罩阻止操作
- [x] 归档比赛显示训练场引导
- [x] 编辑模式保存后刷新 Article
