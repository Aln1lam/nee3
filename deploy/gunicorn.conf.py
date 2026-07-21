"""Gunicorn 生产配置 — 单机部署默认参数。"""
import multiprocessing
import os

# 项目根目录（deploy/ 的上一级）
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

bind = os.environ.get("NEPU_GUNICORN_BIND", "127.0.0.1:5000")
workers = int(os.environ.get("NEPU_GUNICORN_WORKERS", min(4, multiprocessing.cpu_count())))
worker_class = "gthread"
threads = int(os.environ.get("NEPU_GUNICORN_THREADS", 4))
timeout = 120
keepalive = 5
max_requests = 2000
max_requests_jitter = 200

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("NEPU_GUNICORN_LOG_LEVEL", "info")

# 在 WorkingDirectory=/opt/neepu 下启动时，模块路径为 backend.app:app
wsgi_app = "backend.app:app"
