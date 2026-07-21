# Task 02：全局 Layout + TitleBar

> **前置依赖**：Task 01
> **技术栈**：Vue 3 + Naive UI + Axios（沿用 `frontend/` 现有工程）
> **后续任务**：03-ui-components、各页面任务

---

## 本任务目标

实现全局壳层 Layout，包含 Background、TitleBar、Toasts、SplashAnimation，以及导航切换逻辑。

## 壳层结构

```
<Background />          // SVG 电路背景
<TitleBar />            // 顶栏（含横幅）
{children}              // 页面内容（Outlet）
<Toasts />              // 全局通知
<SplashAnimation />     // 首页打字机遮罩（仅首次访问 /）
```

## Background

- 固定全屏 SVG 电路走线动画（draw-line 描边，opacity 10%）
- 半透明遮罩 `bg-layer/90`

## TitleBar（sticky，高 64px）

- `bg-layer/60` + `backdrop-blur-sm`
- **左侧**：LogoAnimate（24×24），比赛页切换为比赛 logo；平台名/比赛名打字机宽度动画
- **中间**：导航链接（见下方逻辑）
- **右侧**：Timer + TimeProgress | WSRX 占位 | 通知 | 主题 | 语言 | Avatar
- **highlight_banner**：警告色横幅，可关闭
- **打印模式**：显示平台名 + 当前时间

### 导航逻辑

**非比赛页（GlobalNav）：**
知识 | 训练 | 赛事 | 公告 | 管理（按权限）

**比赛页（GameNav）：**
题目 | 积分板 | 队伍管理/加入比赛 | 比赛管理（管理员）| 返回

**比赛进行中**：显示 timeline 阶段标签 + 倒计时 Timer + TimeProgress
**训练场模式**：TimeProgress 显示「永久开放」

### 响应式

- `lg` 以下：汉堡菜单 Popover 收纳全部导航 + 主题/通知/语言
- `lg` 以上：水平导航

## Toasts（全局通知）

- level: info | warning | error
- 支持 accept/reject 按钮
- 自动消失或手动关闭

**全局 Toast 触发逻辑（本任务实现 hook/store）：**
- 前后端版本不匹配 → 警告
- 未验证邮箱 → 引导设置页
- 首次访问 → Cookie 策略

## SplashAnimation

- 仅首次访问 `/` 时显示
- 全屏打字机：`[ 西电 CTF 终端 ]_` 光标闪烁
- 结束后写入 localStorage 标记

## LogoAnimate

- 品牌动画组件（可先做简化版 CSS 动画，后续可加强）

## 验收标准

- [ ] 所有页面共享同一 Layout
- [ ] 进入 `/games/:id/challenges` 时导航切换为 GameNav
- [ ] 移动端汉堡菜单可用
- [ ] Toasts 可手动触发测试
- [ ] 首页首次访问显示 SplashAnimation
- [ ] 主题切换影响 TitleBar 样式
