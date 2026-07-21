# Task 06：账号模块 `/account/*`

> **状态**：✅ 已完成
> **技术栈**：Vue 3 + Naive UI + shared/Captcha
---

## 本任务目标

实现完整账号体系：登录、注册、忘记/重置密码、用户设置、OAuth 中转。

## 6.1 登录 `/account/login`

双栏 Card（max-w-3xl，移动端上下堆叠）：
- **左栏**：账号(≥4字符)、密码(8-40位含大小写+数字)、Captcha
- 校验失败：清空密码并刷新验证码
- 忘记密码 → `/account/forgot`
- **右栏**：LogoAnimate 大尺寸 + 注册引导
- **OAuth**：单提供者直链，多提供者 Popover
- 登录成功：redirect 同源校验后跳转，否则首页
- 已登录自动重定向

## 6.2 注册 `/account/register`

同登录布局，字段：账号、昵称、密码、确认密码、邮箱、验证码、图形验证码

## 6.3 忘记/重置 `/account/forgot`、`/account/reset`

居中 Card：
- forgot：邮箱/账号 + 验证码发送
- reset：token 验证 + 新密码表单

## 6.4 用户设置 `/account/settings/*`（Sidebar 布局）

侧边栏菜单：
- 用户信息 `/info`
- 修改密码 `/password`
- 第三方认证 `/oauth`
- 删号跑路 `/mov-esp-ebp-pop-ebp`（开发者彩蛋）

**`/info` 表单：**
- 用户名（disabled）
- 昵称、头像上传（Avatar fallback）
- 邮箱（必填）
- 个人简介（Markdown 编辑器，角标 MARKDOWN）
- 保存按钮

## 6.5 OAuth/验证 `/account/oauth`、`/account/verify`

极简 Loading 页 → Toast → 自动跳转

## 6.6 用户菜单 Popover（顶栏 Avatar）

```
用户信息卡：昵称 + 0x{6位hex} ID
├── 临时用户识别码（Popover）
├── 用户设置 → /account/settings
└── 登出
```

## 验收标准

- [ ] 表单校验与 @modular-forms/solid 集成
- [ ] Captcha 失败刷新逻辑
- [ ] redirect 参数防开放重定向
- [ ] 设置页 Sidebar 导航
- [ ] Avatar 上传预览
- [ ] 用户菜单 Popover 完整
