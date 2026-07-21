import os
from dotenv import load_dotenv

# 加载 .env 文件（从项目根目录）
# 路径: backend/server/config.py -> 需要往上 3 级到项目根
config_dir = os.path.dirname(__file__)  # e:\neepu\backend\server
server_dir = os.path.dirname(config_dir)  # e:\neepu\backend
backend_dir = os.path.dirname(server_dir)  # e:\neepu
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)


class Settings:
    # 支持通过环境变量覆盖数据库连接，便于开发时使用 SQLite 或不同的 DB
    # 优先使用环境变量 NEPU_DATABASE_URL，否则回退到默认的本地 MySQL（请根据本地环境修改）
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'NEPU_DATABASE_URL',
        'mysql+pymysql://neepu_user:change-me@localhost:3306/neepu',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
    }
    JWT_SECRET_KEY = os.environ.get('NEPU_JWT_SECRET') or (
        'dev-only-insecure-jwt-secret-do-not-use' if os.environ.get('NEPU_DEBUG', '0') in ('1', 'true', 'True')
        else ''
    )
    # 登录 token 有效期（默认 7 天，避免频繁过期）
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.environ.get('NEPU_JWT_EXPIRES_HOURS', 24 * 7))
    DEBUG = os.environ.get('NEPU_DEBUG', '0') in ('1', 'true', 'True')
    # Cookie CSRF：生产默认开；开发可用 NEPU_JWT_CSRF=0 关闭
    JWT_COOKIE_CSRF_PROTECT = os.environ.get(
        'NEPU_JWT_CSRF',
        '0' if DEBUG else '1',
    ).lower() in ('1', 'true', 'yes')
    MAX_RUNNING_INSTANCES = int(os.environ.get('NEPU_MAX_RUNNING_INSTANCES', '2'))

    # 邮件服务配置 (SMTP)
    # 支持 QQ邮箱、163邮箱、Gmail 等
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')  # 发件邮箱
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')  # SMTP授权码（不是邮箱密码）
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')  # 默认发件人
    MAIL_SENDER_NAME = os.environ.get('MAIL_SENDER_NAME', 'NEEPU CTF')

    # 前端地址（用于生成邮件中的链接）
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    # 动态容器对外访问主机（比赛时填服务器公网 IP 或域名）
    CONTAINER_PUBLIC_HOST = os.environ.get('NEPU_CONTAINER_PUBLIC_HOST', '127.0.0.1')

    # 动态容器流量包存储目录（项目根目录 captures/）
    CAPTURES_DIR = os.environ.get('NEPU_CAPTURES_DIR', os.path.join(backend_dir, 'captures'))
    PCAP_RETENTION_DAYS = int(os.environ.get('PCAP_RETENTION_DAYS', 30))
    # 0 = 不限制；默认总配额 20GB，单赛 2GB
    PCAP_MAX_TOTAL_BYTES = int(os.environ.get('PCAP_MAX_TOTAL_BYTES', 20 * 1024 * 1024 * 1024))
    PCAP_MAX_BYTES_PER_GAME = int(os.environ.get('PCAP_MAX_BYTES_PER_GAME', 2 * 1024 * 1024 * 1024))
    PCAP_PRUNE_ORPHAN_FILES = os.environ.get('PCAP_PRUNE_ORPHAN_FILES', 'false').lower() in ('1', 'true', 'yes')

    # 启容器队列（Redis）
    CONTAINER_START_MAX_CONCURRENT = int(os.environ.get('CONTAINER_START_MAX_CONCURRENT', 2))
    CONTAINER_START_QUEUE_WAIT_SEC = int(os.environ.get('CONTAINER_START_QUEUE_WAIT_SEC', 90))

    # 上传存储：local | s3（s3 需配 bucket）
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'local').strip().lower()
    STORAGE_LOCAL_ROOT = os.environ.get(
        'STORAGE_LOCAL_ROOT',
        os.path.join(backend_dir, 'backend', 'static', 'uploads'),
    )
    STORAGE_S3_BUCKET = os.environ.get('STORAGE_S3_BUCKET', '')
    STORAGE_S3_PREFIX = os.environ.get('STORAGE_S3_PREFIX', 'uploads/')
    STORAGE_S3_ENDPOINT = os.environ.get('STORAGE_S3_ENDPOINT', '')  # 可选兼容 MinIO
    STORAGE_PUBLIC_URL_PREFIX = os.environ.get('STORAGE_PUBLIC_URL_PREFIX', '/static/uploads')

    # Redis 缓存配置
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'true').lower() in ('true', '1', 'yes')
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '') or None

    # 中间件开关
    ENABLE_COMPRESSION = os.environ.get('ENABLE_COMPRESSION', 'true').lower() in ('true', '1', 'yes')
    SECURITY_POLICY = os.environ.get('SECURITY_POLICY', 'moderate')  # strict | moderate | permissive


settings = Settings()
