# Task 05：首页 `/`

> **状态**：✅ 已完成
> **实现文件**：`components/PlatformLanding.vue`
---

## 本任务目标

实现西电 CTF 终端首页，全屏单页 snap 滚动。

## 页面内容

- **大标题**：`[ 西电 CTF 终端 ]_`（3xl bold，主色闪烁光标 `_`）
- **红色外链副标题**：「为世界上所有美好而战」→ `/magic/sakana`
- **底部 Footer**：
  - (C) 2022-当前年
  - 西安电子科技大学 网络安全与密码学部 → https://ce.xidian.edu.cn/
  - 陕ICP备05016463号 → https://beian.miit.gov.cn/
- **Info Popover（ⓘ）**：
  - Ret2Shell 版本卡（LogoAnimate + REL/DEV 标签）
  - support@ret.sh.cn
  - GitHub、ret.sh.cn 链接

## 交互逻辑

- 内容垂直居中，全屏 snap 滚动
- 若 `platform.info.zen_game` 配置存在，自动跳转该比赛
- SplashAnimation 由 Layout 处理（Task 02），本页无需重复

## 验收标准

- [ ] 标题光标闪烁动画
- [ ] 副标题链接跳转 `/magic/sakana`
- [ ] Footer 链接正确
- [ ] Info Popover 内容完整
- [ ] zen_game 配置时自动重定向
