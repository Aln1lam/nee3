# NEEPU CTF 文档

## 目录

- [`route-architecture-topology.md`](route-architecture-topology.md) — **路由与架构拓扑**（前端页面 / 后端 API / 覆盖度缺口）
- [`deploy-single-server.md`](deploy-single-server.md) — **单机生产部署**（Nginx + Gunicorn + MySQL + Redis + Docker）
- [`ui-style-guide.md`](ui-style-guide.md) — **UI 风格指南**（配色、字体、侧栏、φ 布局、组件模式、Agent Prompt）
- [`frontend-ui-harness.md`](frontend-ui-harness.md) — **前端 UI Harness**（黄金分割布局、中文安全编辑、MCP 验收、Agent Prompt）
- [`api-frontend-checklist.md`](api-frontend-checklist.md) — 后端已测 API 与前端对接清单

## 项目结构（简要）

```
neepu/
├── backend/          Flask API、服务、数据库模型
├── frontend/         Vue 3 + Vite 前端
├── deploy/           生产部署模板（Nginx、systemd、Gunicorn）
├── tests/            自动化测试
├── scripts/          运维与维护脚本（backup、health-check）
├── docker_templates/ 容器题 Docker 模板
├── docs/             文档与规划
└── docker-compose.yml  Redis 服务
```

运行时数据（不入库）：`instance/`、`captures/`、`backend/static/uploads/`
