# -*- coding: utf-8 -*-
"""Append MCP audit checklist to frontend-ui-harness.md"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'docs' / 'frontend-ui-harness.md'
text = p.read_text(encoding='utf-8')

marker = '*最后更新：2026-07-20 — 全站主题审计 + golden-ratio 扩展*'
append = '''*最后更新：2026-07-20 — ChallengeWorkspace MatrixShell + MCP 全站验收*

---

## 13. ChallengeWorkspace MatrixShell（2026-07-20）

### 结构

`ChallengeWorkspace.vue` 根节点改为 `MatrixShell`：

- **#sidebar**：`LinuxPrompt` + 题目树（`.tree-panel--matrix`）
- **#sidebar-footer**：返回练习场 / 赛事 / 排行榜链接
- **主区**：`workspace-dock` + 终端 / Tab 工作区
- **embedded 模式**：嵌入 `Training.vue` 时隐藏 Matrix 页头，避免与欢迎条重复

脚本：

```powershell
python E:\\neepu\\frontend\\patch_challenge_matrix.py
python E:\\neepu\\frontend\\patch_workspace_embedded.py
```

CSS：`golden-ratio.css` → `.challenge-workspace-matrix` 全高、零 padding 主区。

---

## 14. MCP 截图验收清单（2026-07-20）

截图保存在 Cursor 临时目录：`audit-01-*.png` … `audit-13-*.png`。

| # | 路由 | 截图 | 检查点 | 结果 |
|---|------|------|--------|------|
| 01 | `/` | audit-01-landing | Hero φ 三栏；feature 4 列 gap 34px；卡片比 ≈1.615 | ✅ |
| 02 | `/training` | audit-02-training-list | Matrix 侧栏 + quick-card 网格 | ✅ |
| 03 | `/training/69` | audit-03/04 | **MatrixShell 做题台**：LinuxPrompt、题目树、终端 Tab | ✅ |
| 05 | `/home` | audit-05-home | 个人工作台侧栏 + 日历/公告 φ 分栏 | ✅ |
| 06 | `/wiki` | audit-06-wiki | Wiki 侧栏 + matrix-page-head | ✅ |
| 07 | `/admin/dashboard` | audit-07-admin-dashboard | 运维侧栏 + metrics-grid | ✅ |
| 08 | `/bulletin` | audit-08-bulletin | Bulletin Matrix 双栏 | ✅ |
| 09 | `/forgot-password` | audit-09-forgot-password | auth-aux + LinuxPrompt | ✅ |
| 10 | `/archive` | audit-10-archive | MatrixShell 归档列表 | ✅ |
| 11 | `/games` | audit-11-games | GamesHub 侧栏 + 海报区 | ✅ |
| 12 | `/events` | audit-12-events | 日历 + 赛程双栏 | ✅ |
| 13 | `/teams` | audit-13-teams | MatrixShell 战队页 | ✅ |

### CDP 量化（首页 `/`）

- 卡片宽高比：**1.615**（目标 1.55–1.65）
- feature-grid gap：**34px**
- Hero 列：`1462px : 278px` ≈ **5.26:1**（三栏含中间 quick 面板）

### CDP 量化（做题台 `/training/69`）

- `.challenge-workspace-matrix` 存在：**true**
- LinuxPrompt：**true**
- Matrix 页头（embedded 前）：**true**；embedded 后由 Training 欢迎条承担标题

### 待补截图（可选）

- `/games/:id/challenges`（CTFCompetitions legacy 容器）
- `/games/:id/scoreboard`、`/games/:id/teams`
- `/submissions`、`/verify-email`、`/reset-password`
'''

if '## 13. ChallengeWorkspace MatrixShell' in text:
    print('SKIP harness: section 13 already exists')
else:
    if marker not in text:
        raise SystemExit('marker not found')
    text = text.replace(marker, append)
    p.write_text(text, encoding='utf-8', newline='\n')
    print('ok frontend-ui-harness.md section 13-14')
