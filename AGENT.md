# NEEPU CTF 平台项目硬性开发规范 (Project Style Guidelines)

你现在是 NEEPU CTF 项目的专属核心 Agent。你编写的任何前端/后端代码、重构逻辑或样式修改，都**必须 100% 严格遵守**以下项目画像与技术规范：

# Agent 硬性前置工作流 (Execution SOP)

你在执行任何 UI/UX 修改或代码重构任务前，**必须首先读取以下两份文档**：
1. `docs/user-aesthetic-profile.md` (用户审美偏好、人物画像、反模式对照表)
2. `docs/ui-style.md` (Design Tokens 与工程规范)

## 强制检查清单 (Pre-flight Checklist)
在给出代码或完成修改后，你必须隐式完成以下自检：
- [ ] 视觉：是否符合 Obsidian HUD + 薄荷绿微光？（严禁霓虹过曝、全绿、悬空标题）
- [ ] UX：返回按钮是否钉在 248px 左侧 Sidebar 底部？（严禁 TOC 内返回）
- [ ] 编码：Vue 文件改动是否通过 Python UTF-8 机制处理？
- [ ] 构建：改完代码后是否必须在终端执行 `npm run build` 验证通过？

**任何违反 `user-aesthetic-profile.md` 中“反模式对照表”的代码将被直接判定为不合格。**

## 一、 项目画像与基调 (Project Identity & Aesthetics)

- **项目类型**：网络安全 / CTF 竞赛与实训平台。
- **UI/UX 风格**：极具科技感、赛博朋克/霓虹暗黑风（Cyberpunk/Neon Dark/Futuristic Minimal），兼顾高效的比赛和学习操控体验。
- **规范来源**：代码库中 `.cursor/skills/`（如 `awesome-design`, `neon`, `futuristic`, `immersive`）中的 UI 设计约束。

---

## 二、 前端开发规范 (Frontend Guidelines)

### 1. 架构与技术栈
- **框架**：Vue 3 (Composition API / `<script setup>`) + Vite + TypeScript (或严谨 JS)。
- **样式方案**：Tailwind CSS，必须配合项目预设的暗黑/霓虹科技风 Color Palette（如玻璃拟态 `backdrop-blur`、发光边框 `glow-border`、科技感渐变）。
- **组件划分**：
  - 基础 UI 组件统一存放在 `@/components/ui/`，保持无状态/高复用。
  - 业务通用组件存放在 `@/components/shared/`。
  - 路由视图存放在 `@/views/`，按模块（`challenge`, `game`, `training`, `admin`）拆分。

### 2. 代码约束与修改规则
- **状态管理**：使用 Pinia 或响应式 `reactive/ref`，禁止在组件深层内联跨组件状态。
- **API 请求**：所有后端接口交互必须收设在 `@/api/` 目录下，禁止在 Vue 组件中直接书写 `axios/fetch` URL。
- **样式约束**：
  - 优先使用 Tailwind 类名，禁止写硬编码的内联 style（除非需要动态计算属性）。
  - 保持极客/赛博朋克视觉，按钮、Card、Modal 需统一圆角、发光特效及 Hover 动画。
  - 严禁破坏已有的全局主题变量（参见 `patch_global_theme.py` 及 Golden Theme 设定）。

---

## 三、 后端架构规范 (Backend Guidelines)

### 1. 架构与技术栈
- **框架**：Flask (Python 3)，遵循 Blueprint (蓝图) 模块化路由架构。
- **模块分层**：
  - 路由层 (`backend/route/`)：仅处理 HTTP 状态码、请求参数校验与响应封装。
  - 服务层 (`backend/services/`)：处理核心业务逻辑（如 Flag 生成、容器调度、计分逻辑、防作弊检测等）。
  - 中间件层 (`backend/middleware_refactored/`)：统一处理限流 (`rate_limiting`)、缓存 (`caching`)、鉴权与安全响应头 (`security`)。
  - 模型层 (`backend/server/db_models.py`)：SQLAlchemy 统一模型定义。

### 2. 代码约束与修改规则
- **重构原则**：严格保持 middleware_refactored 的解耦设计，禁止把缓存、限流或安全校验逻辑直接硬编码到路由函数中。
- **API 接口规范**：
  - 接口响应格式必须统一：`{"code": 200, "msg": "...", "data": {...}}` 或标准 JSON 格式。
  - 所有涉及容器/Docker 调度的修改，必须通过 `backend/services/container_service.py` 调度，不得直接在 Route 层操作 Docker SDK。
- **安全性**：敏感词过滤（`sensitive_words`）、Flag 掩码 (`flag_redact`) 以及提交锁 (`submit_lock`) 必须在服务层强校验。

---

## 四、 Agent 行为通用约束 (Agent Rule)
1. **禁止破坏性修改**：修改前端时不得破坏后端接口约定；修改后端时不得更改前端依赖的字段名称（如有改动，必须双向同步修改）。
2. **测试与验证**：每次修改后端 Route 或 Service，需确保通过或编写对应的 Smoke Test / E2E 验证脚本（参照 `backend/scripts/` 下的自动化测试模式）。
3. **保持模块干净**：新增文件必须严格按上述目录结构归位，禁止在根目录新建临时脚本或乱放样式文件。