# NEEPU CTF

校内 CTF / 网络安全实训平台。

- **前端**：Vue 3 + Vite
- **后端**：Flask + Gunicorn
- **数据**：MySQL + Redis
- **容器题**：Docker（可选，不开也能跑平台主体）

---

## 给接手的人看这里

**协作与开发：** 请先阅读 **[项目约定.md](项目约定.md)**（先读再做）和 **[功能说明书](docs/功能说明书.md)**。

如果你是第一次部署这套系统，**不要猜命令**，按下面这份文档一步一步做即可：

👉 **[完整部署手册（小白版）](docs/deploy-single-server.md)**

文档已经按「复制命令 → 回车 → 检查有没有报错」写好了，预计熟悉 Linux 的同学约半天，完全新手建议预留一天。

---

## 你最终会搭成什么

```text
浏览器
  │
  ▼
Nginx（80/443）── 静态前端 frontend/dist
  │
  └─ /api/* ──► Gunicorn(Flask) :5000
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       MySQL      Redis     Docker（动态容器题）
```

---

## 仓库结构（只需关心这些）

| 路径 | 说明 |
|------|------|
| `backend/` | Flask 后端源码 |
| `frontend/` | Vue 前端源码 |
| `deploy/` | Nginx / systemd / Gunicorn 模板 |
| `docker-compose.yml` | 只启动 Redis |
| `docs/deploy-single-server.md` | **部署手册（必读）** |
| `backend/.env.production.example` | 生产环境变量模板 |
| `scripts/backup.sh` | 备份 |
| `scripts/health-check.sh` | 巡检 |
| `docker_templates/` | 示例容器题镜像 |

---

## 服务器最低要求

| 项目 | 建议 |
|------|------|
| 系统 | **Ubuntu 22.04 LTS**（强烈推荐，文档按它写的） |
| 配置 | 4 核 8G 内存起；容器题多建议 8 核 16G |
| 磁盘 | 100GB+ SSD |
| 网络 | 一台能 SSH 上去的公网/校园网服务器 |
| 域名 | 有最好（方便 HTTPS）；暂时没有也能先用 IP + HTTP 调试 |

---

## 三分钟了解部署顺序

1. 装系统软件：Nginx、MySQL、Python、Node、Docker  
2. 建数据库账号  
3. 把代码放到 `/opt/neepu`  
4. 配 `.env`（数据库密码、JWT、域名）  
5. 启动 Redis  
6. 初始化数据库 + 创建管理员  
7. 构建前端  
8. 用 systemd 拉起后端  
9. 配 Nginx（先 HTTP，再上 HTTPS）  
10. 开防火墙、做备份  

每一步的**完整命令、预期输出、失败怎么办**都在部署手册里。

---

## 本地开发（可选）

仅当你要改代码时才需要。正式给别人用平台，请走生产部署手册。

```bash
# 后端（需本机 MySQL / Redis，并准备好 .env）
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 配置项目根目录 .env 后：
python -c "from backend.app import create_app; create_app()"

# 前端
cd frontend
npm ci
npm run dev
```

---

## 常用运维入口

部署完成后：

```bash
# 服务状态
sudo systemctl status neepu-api nginx mysql

# 健康检查
/opt/neepu/scripts/health-check.sh
curl -s http://127.0.0.1:5000/api/health/ready

# 备份
/opt/neepu/scripts/backup.sh
```

更细的更新发版、排错见：[部署手册](docs/deploy-single-server.md)。

---

## 安全提醒（交接必看）

1. **不要把别人的 `.env` 直接拿去用**，尤其不要提交到 git。  
2. 上线后立刻改掉管理员密码。  
3. 公网不要开放 `3306`（MySQL）、`6379`（Redis）、`5000`（Gunicorn）。  
4. 生产必须 `NEPU_DEBUG=0`。  

---

## 许可证 / 归属

内部校用项目。对外分发前请确认你们团队的授权约定。
