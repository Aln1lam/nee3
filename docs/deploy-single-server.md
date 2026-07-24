# NEEPU CTF 单机部署手册（小白版）

> 目标：一台 Linux 服务器，按顺序复制命令，就能把平台跑起来。  
> 适合人群：会 SSH 登录服务器、会复制粘贴的同学。  
> 推荐系统：**Ubuntu 22.04 LTS**（本文命令按它写）。

如果你中途报错，先看文末「常见问题」，再往下做。不要跳步。

---

## 0. 先搞清楚你在搭什么

最终架构：

```text
用户浏览器
    │
    ▼
Nginx（对外 80 / 443）
    ├── 静态页面  →  /opt/neepu/frontend/dist
    └── /api/*    →  Gunicorn(Flask) 本机 127.0.0.1:5000
                          │
                ┌─────────┼──────────┐
                ▼         ▼          ▼
             MySQL      Redis      Docker
           （必装）   （Docker起） （容器题才需要）
```

**预计耗时**

| 情况 | 时间 |
|------|------|
| 有过一点 Linux 经验 | 2～4 小时 |
| 完全新手 | 半天～一天（含等包、排错） |

**开始前请准备**

1. 一台 Ubuntu 22.04 服务器，能用 SSH 登录，有 `sudo` 权限  
2. 项目代码（git 仓库地址，或别人给你的压缩包）  
3. 一个你自己定的 **MySQL 密码**（下文用 `你的数据库密码` 表示，请整篇统一替换）  
4. 一个你自己定的 **管理员密码**（下文用 `你的管理员密码` 表示）  
5. （可选）域名，例如 `ctf.example.edu.cn`；没有域名也可以先用服务器 IP

---

## 1. 登录服务器

在你自己的电脑上：

```bash
ssh 你的用户名@服务器IP
```

登录成功后，建议确认系统：

```bash
lsb_release -a
```

看到类似 `Ubuntu 22.04` 即可继续。若是 Debian 12，大部分命令也能用，个别包名可能略有差异。

---

## 2. 安装系统依赖

一行一行执行（可以整段复制）：

```bash
sudo apt update
sudo apt install -y nginx mysql-server python3.11 python3.11-venv \
  curl ca-certificates gnupg docker.io docker-compose-plugin \
  certbot python3-certbot-nginx
```

### 2.1 安装较新的 Node.js（重要）

Ubuntu 自带的 `nodejs` 往往太旧，Vite 构建会失败。请安装 **Node.js 20 LTS**：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

`node -v` 应显示 `v20.x.x` 或更高。

### 2.2 启动基础服务

```bash
sudo systemctl enable --now nginx mysql docker
sudo systemctl status nginx mysql docker --no-pager
```

三个都显示 `active (running)` 就对了。  
如果 `docker` 提示当前用户不在 docker 组，先执行：

```bash
sudo usermod -aG docker "$USER"
```

然后 **重新 SSH 登录一次**，再执行：

```bash
docker ps
```

能列出（哪怕是空表）即可。

---

## 3. 创建 MySQL 数据库

进入 MySQL：

```bash
sudo mysql
```

进入后你会看到 `mysql>` 提示符。把下面整段粘贴进去（**把密码改成你的**）：

```sql
CREATE DATABASE neepu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'neepu_user'@'localhost' IDENTIFIED BY '你的数据库密码';
GRANT ALL PRIVILEGES ON neepu.* TO 'neepu_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

验证能否登录：

```bash
mysql -u neepu_user -p -e "SHOW DATABASES;"
```

输入你刚设的数据库密码，列表里应能看到 `neepu`。

---

## 4. 放置项目代码

### 方式 A：用 git（推荐）

```bash
sudo mkdir -p /opt/neepu
sudo chown "$USER":"$USER" /opt/neepu
git clone <你的仓库地址> /opt/neepu
cd /opt/neepu
ls
```

应能看到 `backend`、`frontend`、`deploy`、`docker-compose.yml`、`README.md` 等。

### 方式 B：别人给了压缩包

```bash
sudo mkdir -p /opt/neepu
sudo chown "$USER":"$USER" /opt/neepu
# 假设压缩包在家目录：~/neepu.zip
unzip ~/neepu.zip -d /opt/neepu
# 如果解压后多套了一层目录，把内容挪到 /opt/neepu 根下
cd /opt/neepu
ls
```

确认存在：

```bash
test -f /opt/neepu/requirements.txt && echo OK_requirements
test -f /opt/neepu/frontend/package.json && echo OK_frontend
test -f /opt/neepu/backend/.env.production.example && echo OK_env_example
test -f /opt/neepu/deploy/neepu-api.service && echo OK_systemd
```

四行都应打印 `OK_...`。

---

## 5. 创建 Python 虚拟环境并安装依赖

```bash
cd /opt/neepu
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

成功后，提示符前面通常会出现 `(.venv)`。  
以后每次手动跑 Python 命令前，都要先：

```bash
cd /opt/neepu
source .venv/bin/activate
```

---

## 6. 配置环境变量（最容易出错的一步）

### 6.1 为什么要配两份？

| 文件 | 谁在读 |
|------|--------|
| `/opt/neepu/.env` | 后端 Python 代码（`load_dotenv`） |
| `/opt/neepu/backend/.env` | systemd 服务启动时注入环境变量 |

两边内容保持一致最省事。按下面做：

```bash
cd /opt/neepu
cp backend/.env.production.example .env
cp .env backend/.env
```

### 6.2 生成一个随机 JWT 密钥

```bash
openssl rand -hex 32
```

把输出的一长串字符复制下来（下文用 `你的JWT密钥` 表示）。

### 6.3 编辑配置

```bash
nano /opt/neepu/.env
```

至少改成下面这样（域名/IP、密码按你的实际情况替换）：

```bash
# --- 数据库 ---
NEPU_DATABASE_URL=mysql+pymysql://neepu_user:你的数据库密码@127.0.0.1:3306/neepu
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# --- 安全（必须改）---
NEPU_JWT_SECRET=你的JWT密钥
NEPU_DEBUG=0

# --- 站点（有域名用 https://你的域名；暂时用 IP 可先写 http://服务器IP）---
FRONTEND_URL=https://ctf.example.edu.cn

# --- 容器题学生访问地址（通常填域名或公网 IP，不要带 http://）---
NEPU_CONTAINER_PUBLIC_HOST=ctf.example.edu.cn

# --- Redis ---
REDIS_ENABLED=true
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# --- 中间件 ---
ENABLE_COMPRESSION=true
SECURITY_POLICY=moderate
```

保存退出：`Ctrl+O` → 回车 → `Ctrl+X`。

**立刻同步到 backend：**

```bash
cp /opt/neepu/.env /opt/neepu/backend/.env
```

以后只要改了其中一份，就再执行一次上面的 `cp`，保持两边一致。

### 6.4 配置检查清单

- [ ] `NEPU_DATABASE_URL` 里的密码和 MySQL 一致  
- [ ] `NEPU_JWT_SECRET` 不是 `CHANGE_ME...`  
- [ ] `NEPU_DEBUG=0`  
- [ ] `FRONTEND_URL` 和用户将来浏览器访问的地址一致（协议、域名都要对）  
- [ ] 根目录 `.env` 与 `backend/.env` 已同步  

---

## 7. 启动 Redis

```bash
cd /opt/neepu
docker compose up -d
docker compose ps
```

应看到 `neepu-redis` 状态为 `running` / `healthy`。

测连通：

```bash
docker exec neepu-redis redis-cli ping
```

应返回 `PONG`。

> Redis 只绑定本机 `127.0.0.1:6379`，不会直接暴露到公网。

---

## 8. 准备运行目录权限

后端用 `www-data` 用户跑，需要能写上传目录和流量包目录：

```bash
cd /opt/neepu
mkdir -p backend/static/uploads captures
sudo chown -R www-data:www-data backend/static/uploads captures
sudo chmod -R u+rwX,g+rwX backend/static/uploads captures

# 让当前用户也能维护这些目录（可选）
sudo usermod -aG www-data "$USER"
```

给 Docker 权限给后端用户（容器题需要）：

```bash
sudo usermod -aG docker www-data
```

---

## 9. 初始化数据库表 + 创建管理员

```bash
cd /opt/neepu
source .venv/bin/activate

# 初始化表结构（第一次会自动建表）
python -c "from backend.app import create_app; create_app(); print('DB_OK')"
```

看到 `DB_OK` 且没有 Traceback 才继续。

创建管理员（**必须设置密码环境变量**，脚本禁止空密码）：

```bash
export NEEPU_ADMIN_PASSWORD='你的管理员密码'
# 可选：自定义邮箱/用户名
# export NEEPU_ADMIN_EMAIL='admin@你的学校.edu.cn'
# export NEEPU_ADMIN_USERNAME='admin'

python backend/scripts/create_admin.py
```

成功会打印类似：

```text
[OK] 创建 admin success
  邮箱: admin@neepu.edu.cn
  用户名: neepu_admin
  密码: ...
```

**把用户名和密码记下来**，后面登录后台要用。

---

## 10. 构建前端

```bash
cd /opt/neepu/frontend
npm ci
npm run build
ls dist
```

`dist` 目录里应有 `index.html` 等文件。  
生产环境前端通过同域名 `/api` 访问后端，**一般不用**设置 `VITE_API_BASE`。

如果 `npm ci` 很慢：多半是网络问题，可配置国内 npm 镜像后再试：

```bash
npm config set registry https://registry.npmmirror.com
npm ci
npm run build
```

---

## 11. 先手动试跑后端（强烈建议）

```bash
cd /opt/neepu
source .venv/bin/activate
gunicorn -c deploy/gunicorn.conf.py
```

另开一个 SSH 窗口：

```bash
curl -s http://127.0.0.1:5000/api/health/ready
```

正常大致会看到：

```json
{"status":"ok","checks":{"database":"ok","redis":...}}
```

若 `"status":"ok"`，回到第一个窗口按 `Ctrl+C` 停掉手动进程，继续装 systemd。  
若失败，先别装服务，去文末排错。

---

## 12. 用 systemd 托管后端（开机自启）

```bash
sudo cp /opt/neepu/deploy/neepu-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now neepu-api
sudo systemctl status neepu-api --no-pager
```

应显示 `active (running)`。再测一次：

```bash
curl -s http://127.0.0.1:5000/api/health/ready
```

看日志（出问题时很有用）：

```bash
sudo journalctl -u neepu-api -n 80 --no-pager
```

---

## 13. 配置 Nginx

分两种情况。**小白建议先做 13.A（HTTP），确认网页能开，再做 HTTPS。**

### 13.A 先用 HTTP（方便验证）

创建临时站点配置：

```bash
sudo tee /etc/nginx/sites-available/neepu >/dev/null <<'EOF'
upstream neepu_api {
    server 127.0.0.1:5000;
    keepalive 8;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    root /opt/neepu/frontend/dist;
    index index.html;
    client_max_body_size 32m;

    location /api/ {
        proxy_pass http://neepu_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_read_timeout 120s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/neepu /etc/nginx/sites-enabled/neepu
# 去掉默认站点，避免冲突
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

浏览器访问：

```text
http://服务器IP/
```

应能看到平台页面。接口探测：

```bash
curl -s http://127.0.0.1/api/health/live
```

> 注意：生产环境登录 Cookie 更推荐 HTTPS。HTTP 仅用于先把链路跑通。若你暂时只有 IP，可把 `.env` 里 `FRONTEND_URL` 写成 `http://服务器IP`，并 `cp` 同步到 `backend/.env`，然后 `sudo systemctl restart neepu-api`。

### 13.B 上 HTTPS（有域名时）

前提：

1. 域名已解析到这台服务器公网 IP  
2. 防火墙已放行 80/443（见第 14 节）  
3. 上面 HTTP 站点已经能打开  

申请证书并自动改 Nginx：

```bash
sudo certbot --nginx -d ctf.example.edu.cn
```

按提示输入邮箱、同意条款。成功后浏览器访问：

```text
https://ctf.example.edu.cn/
```

然后把 `.env` 改回正式值并重启：

```bash
nano /opt/neepu/.env
# FRONTEND_URL=https://ctf.example.edu.cn
# NEPU_CONTAINER_PUBLIC_HOST=ctf.example.edu.cn
cp /opt/neepu/.env /opt/neepu/backend/.env
sudo systemctl restart neepu-api
```

仓库里还有一份更完整的 HTTPS 模板：`deploy/nginx.conf.example`，证书路径按 Let's Encrypt 默认位置写好了，需要时可以对照修改：

```bash
sudo nano /etc/nginx/sites-available/neepu
sudo nginx -t && sudo systemctl reload nginx
```

---

## 14. 防火墙（UFW）

**先确保 SSH 放行，再启用防火墙**，否则可能把自己锁在门外。

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 容器题端口（按需）

如果比赛要用动态容器，且题目映射到宿主机端口段（例如 `20000-21000`），需要额外放行：

```bash
# 示例：按你们实际端口段改
sudo ufw allow 20000:21000/tcp
```

### 绝对不要对公网开放

- `3306` MySQL  
- `6379` Redis  
- `5000` Gunicorn  

这些只应本机访问，由 Nginx 反代对外。

---

## 15. 登录验收（部署完成标志）

1. 浏览器打开你的站点（`http://IP` 或 `https://域名`）  
2. 进入登录页  
3. 用第 9 步创建的管理员账号登录  
4. 能进管理后台，即部署成功  

可选再查健康：

```bash
curl -s http://127.0.0.1:5000/api/health/ready
/opt/neepu/scripts/health-check.sh
```

---

## 16. 备份（强烈建议马上做）

```bash
chmod +x /opt/neepu/scripts/backup.sh /opt/neepu/scripts/health-check.sh
sudo mkdir -p /var/backups/neepu
/opt/neepu/scripts/backup.sh
ls /var/backups/neepu
```

设置每周日凌晨 3 点自动备份：

```bash
sudo crontab -e
```

在文件末尾加一行：

```cron
0 3 * * 0 /opt/neepu/scripts/backup.sh >> /var/log/neepu-backup.log 2>&1
```

备份内容：

- MySQL 全库  
- `backend/static/uploads/`（上传文件）  
- 流量包目录（脚本默认看 `backend/captures`；运行时默认写项目根 `captures/`。若你只用根目录 `captures/`，可把该目录软链过去，或改备份脚本路径）

一键对齐流量包目录（推荐执行一次）：

```bash
cd /opt/neepu
mkdir -p captures backend/captures
# 若希望备份脚本也能打到同一份数据，可把 backend/captures 指到根 captures：
sudo rm -rf backend/captures
sudo ln -s /opt/neepu/captures /opt/neepu/backend/captures
sudo chown -R www-data:www-data /opt/neepu/captures
```

---

## 17. 以后如何更新版本

```bash
cd /opt/neepu
/opt/neepu/scripts/backup.sh          # 先备份

# 若用 git：
git pull

source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm ci
npm run build

# 若改过 .env，记得两边同步
# cp /opt/neepu/.env /opt/neepu/backend/.env

sudo systemctl restart neepu-api
sudo systemctl reload nginx
curl -s http://127.0.0.1:5000/api/health/ready
```

---

## 18. 日常巡检命令

```bash
sudo systemctl status neepu-api nginx mysql --no-pager
docker compose -f /opt/neepu/docker-compose.yml ps
curl -s http://127.0.0.1:5000/api/health/ready
df -h
docker ps
/opt/neepu/scripts/health-check.sh
```

看后端错误日志：

```bash
sudo journalctl -u neepu-api -f
```

---

## 19. 组件说明（挂了会怎样）

| 组件 | 作用 | 挂了会怎样 |
|------|------|------------|
| Nginx | 对外提供网页 + 反代 API | 网站打不开 |
| Gunicorn / neepu-api | 后端 API | 页面可能开，但接口全挂 |
| MySQL | 用户/比赛/提交等主数据 | 平台基本不可用 |
| Redis | 限流、验证码、缓存 | 可降级，但多进程下行为不一致 |
| 本地上传目录 | 头像、附件 | 上传/下载异常 |
| Docker | 动态容器题 | 仅容器题受影响，其余功能仍可用 |

---

## 20. 常见问题（排错）

### Q1：`pip install` 失败 / 找不到 `python3.11`

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential default-libmysqlclient-dev
```

本项目主要用 `pymysql`，一般不需要编译 MySQL 客户端；若仍失败，把完整报错贴给维护者。

### Q2：`npm run build` 报错 Node 版本太低

回到 [第 2.1 节](#21-安装较新的-nodejs重要) 重装 Node 20。

### Q3：`create_admin.py` 提示必须设置密码

```bash
export NEEPU_ADMIN_PASSWORD='你的管理员密码'
python backend/scripts/create_admin.py
```

### Q4：`neepu-api` 启动失败

```bash
sudo journalctl -u neepu-api -n 100 --no-pager
```

最常见原因：

1. `.env` 数据库密码错  
2. 根目录 `.env` 与 `backend/.env` 不一致  
3. MySQL 没启动：`sudo systemctl start mysql`  
4. Redis 没启动：`cd /opt/neepu && docker compose up -d`  
5. 虚拟环境路径不对 / 依赖没装进 `.venv`

### Q5：网页能开，但登录失败 / 一直跳回登录

1. 生产环境优先用 **HTTPS**  
2. `FRONTEND_URL` 必须和浏览器地址栏一致（含 `http/https`、域名、有无端口）  
3. 改完 `.env` 后：

```bash
cp /opt/neepu/.env /opt/neepu/backend/.env
sudo systemctl restart neepu-api
```

### Q6：健康检查 database error

```bash
mysql -u neepu_user -p -e "USE neepu; SHOW TABLES;"
```

能连上却没表：重新执行第 9 节初始化。  
连不上：检查密码、MySQL 服务、`NEPU_DATABASE_URL`。

### Q7：Redis 连不上

```bash
cd /opt/neepu
docker compose ps
docker compose logs redis --tail 50
docker exec neepu-redis redis-cli ping
```

### Q8：容器题启不来 / 学生连不上

1. `www-data` 是否在 docker 组：

```bash
groups www-data
sudo usermod -aG docker www-data
sudo systemctl restart neepu-api
```

2. `.env` 里 `NEPU_CONTAINER_PUBLIC_HOST` 是否是学生能访问到的 IP/域名（不要写 `127.0.0.1` 给校外用户）  
3. 防火墙是否放行题目端口段  
4. `docker ps` 看容器是否真的起来了  

### Q9：Nginx 报证书文件不存在

说明你直接套了 HTTPS 模板，但还没申请证书。请先按 [13.A](#13a-先用-http方便验证) 用 HTTP，再按 [13.B](#13b-上-https有域名时) 用 certbot。

### Q10：权限错误（Permission denied）写 uploads / captures

```bash
sudo chown -R www-data:www-data /opt/neepu/backend/static/uploads /opt/neepu/captures
sudo chmod -R u+rwX,g+rwX /opt/neepu/backend/static/uploads /opt/neepu/captures
sudo systemctl restart neepu-api
```

### Q11：502 Bad Gateway

通常是后端没起来：

```bash
sudo systemctl status neepu-api --no-pager
curl -s http://127.0.0.1:5000/api/health/live
sudo journalctl -u neepu-api -n 50 --no-pager
```

---

## 21. 关键文件速查

| 文件 | 说明 |
|------|------|
| `README.md` | 项目入口说明 |
| `docs/deploy-single-server.md` | 本手册 |
| `backend/.env.production.example` | 生产环境变量模板 |
| `/opt/neepu/.env` 与 `backend/.env` | 你的真实配置（勿泄露、勿提交 git） |
| `deploy/gunicorn.conf.py` | Gunicorn 配置 |
| `deploy/neepu-api.service` | systemd 服务 |
| `deploy/nginx.conf.example` | Nginx HTTPS 模板 |
| `docker-compose.yml` | Redis |
| `scripts/backup.sh` | 备份 |
| `scripts/health-check.sh` | 巡检 |
| `backend/scripts/create_admin.py` | 创建/重置管理员 |

---

## 22. 一页纸检查清单（做完请打勾）

- [ ] Nginx / MySQL / Docker 均为 running  
- [ ] Node.js ≥ 20，`npm run build` 成功，`frontend/dist` 存在  
- [ ] Python venv 已建，`pip install -r requirements.txt` 成功  
- [ ] MySQL 库 `neepu` + 用户 `neepu_user` 可用  
- [ ] `/opt/neepu/.env` 与 `backend/.env` 一致，且关键密钥已改  
- [ ] `docker compose up -d` 后 Redis 返回 PONG  
- [ ] `create_admin.py` 成功，管理员密码已保存  
- [ ] `systemctl status neepu-api` 为 active  
- [ ] `curl 127.0.0.1:5000/api/health/ready` 为 ok  
- [ ] 浏览器能打开站点并管理员登录成功  
- [ ] 防火墙已开 SSH + Nginx，未对公网开放 3306/6379/5000  
- [ ] 备份脚本已跑通（可选：已加 cron）  

全部打勾，就可以把服务器交给业务使用了。
