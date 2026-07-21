# Playwright E2E · 按路由拓扑全量扫描

依据 [`docs/route-architecture-topology.md`](../docs/route-architecture-topology.md) **§2 前端页面路由**。

## 流程

1. **自动创建账号**（`helpers/provision_user.py`：待验证注册 → 邮箱验证 → 提权 admin）
2. **用新账号登录**
3. 按章节扫描：**2.1 → 2.2 → 2.3 → 2.4 → 2.5**

无需手动设置 `E2E_USER` / `E2E_PASSWORD`。

## 运行

```powershell
cd E:\neepu\frontend; npm run dev:3000   # 另开终端

cd E:\neepu\e2e
$env:E2E_GAME_ID="68"   # 可选
npm test
```

## 报告

`e2e/e2e-report/index.html`
