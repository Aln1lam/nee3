# NEEPU CTF 单机部署指南

目标架构（长期维护优先）：

```text
Nginx + Gunicorn(Flask) + MySQL(本机) + Redis(Docker) + 本地文件 + Docker(容器题)
```

适用场景：一台 Linux 服务器长期维护校内 CTF 靶场。

---

## 1. 服务器要求

| 项目 | 建议 |
|------|------|
| 系统 | Ubuntu 22.04 LTS / Debian 12 |
| 配置 | 4C8G 起步；容器题多建议 8C16G |
| 磁盘 | 100GB+ SSD |
| 域名 | 一个，如 `ctf.example.edu.cn` |
| 公网端口 | 仅 **80 / 443**（容器题另按需开端口段） |

---

## 2. 目录约定

```text
/opt/neepu/                     项目根（git clone）
├── backend/.env                生产配置（从 .env.production.example 复制）
├── backend/static/uploads/     用户上传
├── backend/captures/             流量包
├── frontend/dist/              前端构建产物
├── deploy/                     Nginx / systemd / Gunicorn 模板
├── docker-compose.yml          仅 Redis
└── scripts/backup.sh           备份脚本

/var/backups/neepu/             备份输出目录
```

---

## 3. 安装系统依赖

```bash
sudo apt update
sudo apt install -y nginx mysql-server python3.11 python3.11-venv \
  nodejs npm docker.io docker-compose-plugin certbot python3-certbot-nginx

sudo systemctl enable --now nginx mysql docker
```

---

## 4. MySQL 初始化

```bash
sudo mysql
```

```sql
CREATE DATABASE neepu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'neepu_user'@'localhost' IDENTIFIED BY '你的强密码';
GRANT ALL ON neepu.* TO 'neepu_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 5. 拉取代码与 Python 环境

```bash
sudo mkdir -p /opt/neepu
sudo chown "$USER":"$USER" /opt/neepu
git clone <你的仓库地址> /opt/neepu
cd /opt/neepu

python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

---

## 6. 生产配置

```bash
cp backend/.env.production.example backend/.env
nano backend/.env
```

**必须修改：**

- `NEPU_DATABASE_URL` — MySQL 账号密码
- `NEPU_JWT_SECRET` — `openssl rand -hex 32` 生成，上线后不要随意更换
- `NEPU_DEBUG=0`
- `FRONTEND_URL` — 你的 HTTPS 域名
- `NEPU_CONTAINER_PUBLIC_HOST` — 容器题公网 IP 或域名

---

## 7. Redis（Docker）

```bash
cd /opt/neepu
docker compose up -d
docker compose ps
```

Redis 已绑定 `127.0.0.1:6379`，不暴露公网。

---

## 8. 初始化数据库与管理员

```bash
cd /opt/neepu
source .venv/bin/activate
python -c "from backend.app import create_app; create_app()"
python backend/scripts/create_admin.py
```

---

## 9. 构建前端

```bash
cd /opt/neepu/frontend
npm ci
npm run build
```

生产环境 API 走同域 `/api`，无需设置 `VITE_API_BASE`。

---

## 10. Gunicorn + systemd

```bash
# 试运行
cd /opt/neepu
source .venv/bin/activate
gunicorn -c deploy/gunicorn.conf.py

# 另开终端验证
curl -s http://127.0.0.1:5000/api/health/ready
```

安装 systemd 服务：

```bash
sudo cp /opt/neepu/deploy/neepu-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now neepu-api
sudo systemctl status neepu-api
```

**容器题需要 Docker 权限：**

```bash
sudo usermod -aG docker www-data
sudo systemctl restart neepu-api
```

---

## 11. Nginx + HTTPS

```bash
sudo cp /opt/neepu/deploy/nginx.conf.example /etc/nginx/sites-available/neepu
sudo nano /etc/nginx/sites-available/neepu   # 改 server_name 与证书路径
sudo ln -sf /etc/nginx/sites-available/neepu /etc/nginx/sites-enabled/neepu
sudo nginx -t
sudo systemctl reload nginx

# Let's Encrypt（示例）
sudo certbot --nginx -d ctf.example.edu.cn
```

---

## 12. 防火墙

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

**不要**对公网开放：3306（MySQL）、6379（Redis）、5000（Gunicorn）。

---

## 13. 备份（每周）

```bash
chmod +x /opt/neepu/scripts/backup.sh
sudo mkdir -p /var/backups/neepu
/opt/neepu/scripts/backup.sh
```

加入 cron（每周日凌晨 3 点）：

```bash
sudo crontab -e
```

```cron
0 3 * * 0 /opt/neepu/scripts/backup.sh >> /var/log/neepu-backup.log 2>&1
```

备份内容：MySQL 全库、`backend/static/uploads/`、`backend/captures/`。

---

## 14. 日常巡检

```bash
chmod +x /opt/neepu/scripts/health-check.sh
/opt/neepu/scripts/health-check.sh
```

或手动：

```bash
systemctl status neepu-api nginx mysql
docker compose -f /opt/neepu/docker-compose.yml ps
curl -s http://127.0.0.1:5000/api/health/ready
df -h
docker ps
```

---

## 15. 发版更新流程

```bash
cd /opt/neepu
/opt/neepu/scripts/backup.sh          # 先备份

git pull
source .venv/bin/activate
pip install -r requirements.txt

cd frontend && npm ci && npm run build

sudo systemctl restart neepu-api
sudo systemctl reload nginx
```

---

## 16. 组件说明

| 组件 | 作用 | 挂了会怎样 |
|------|------|------------|
| Nginx | HTTPS、静态前端、反代 `/api` | 站点不可访问 |
| Gunicorn | 运行 Flask API | 接口全部失败 |
| MySQL | 用户/比赛/提交等主数据 | 平台不可用 |
| Redis | 限流、验证码、读缓存 | 可降级内存模式，多 worker 时不一致 |
| 本地文件 | 头像、附件、PCAP | 上传/下载异常 |
| Docker | 动态容器题 | 仅容器题受影响 |

---

## 17. 常见问题

### Cookie 登录失败

- 必须 HTTPS（生产 `NEPU_DEBUG=0`）
- `FRONTEND_URL` 与浏览器访问域名一致

### 容器题连不上

- 检查 `NEPU_CONTAINER_PUBLIC_HOST`
- 检查防火墙是否放行对应端口
- `www-data` 是否在 `docker` 组

### Redis 连接失败

```bash
docker compose logs redis
redis-cli -h 127.0.0.1 ping
```

---

## 18. 相关文件

| 文件 | 说明 |
|------|------|
| `deploy/gunicorn.conf.py` | Gunicorn 配置 |
| `deploy/neepu-api.service` | systemd 单元 |
| `deploy/nginx.conf.example` | Nginx 站点模板 |
| `backend/.env.production.example` | 生产环境变量模板 |
| `scripts/backup.sh` | 备份脚本 |
| `scripts/health-check.sh` | 巡检脚本 |
| `docker-compose.yml` | Redis 服务 |
