# Task 03：基础 UI 组件库

> **前置依赖**：Task 01、Task 02
> **技术栈**：Vue 3 + Naive UI + CSS 变量主题（沿用 `frontend/` 现有工程）
> **后续任务**：04-shared-feature-components、各页面任务
> **状态**：✅ 已完成 — 演示页 `/dev/components`
---

## 本任务目标

实现统一封装的基础 UI 组件，供全站复用。风格遵循 `00-common-context.md` 设计系统。

## 需实现的组件

| 组件 | 要点 |
|------|------|
| **Button** | 主色/次要/危险变体，loading 态，disabled |
| **Card** | 毛玻璃半透明，圆角，可选 header/footer |
| **Link** | 内部路由 + 外链区分，主色 hover |
| **Input** | label、error 提示、disabled |
| **Popover** | 点击触发，定位，移动端友好 |
| **Divider** | 水平/垂直 |
| **Avatar** | 图片 + 字母 fallback（如 "A"） |
| **Tag** | 语义色：success/warning/error/info/默认 |
| **Select** | 下拉选择，可清除 |
| **Tabs** | 水平 Tab 栏，支持 disabled |
| **Splitter** | 上下/左右可拖拽分栏 |
| **Timer** | 倒计时显示（luxon） |
| **TimeProgress** | 进度条 + 阶段标签；训练场显示「永久开放」 |
| **LoadingTips** | 随机技术风文案（如「正在除以 0...」） |
| **Picture** | 媒体 hash 加载 `/api/media?hash=...` |
| **Chart** | ECharts 封装（传入 option 即可渲染） |

## ThemeBox

```
Popover：
- 深色/浅色切换（月亮/太阳图标）
- 「跟随系统」toggle
```

## NotificationBox

```
Popover 显示 Toast 历史
有未读时图标 alert-badge 填充态 + 主色
```

## 样式约定

- 使用 TailwindCSS + clsx
- 支持 dark: 变体
- 按钮/卡片 hover 微交互，不过度花哨

## 验收标准

- [ ] 每个组件有独立文件，统一从 `components/ui/index.js` 导出
- [ ] 深色/浅色主题下视觉正常
- [ ] Splitter 可拖拽调整比例
- [ ] Timer 倒计时到 0 触发回调
- [ ] Chart 可渲染简单折线图

## 输出

提供组件 Story/演示页（可选 `/dev/components` 路由）便于后续任务调试。
