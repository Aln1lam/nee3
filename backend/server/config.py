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
    SQLALCHEMY_DATABASE_URI = os.environ.get('NEPU_DATABASE_URL', 'mysql+pymysql://neepu_user:123456@localhost:3306/neepu')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('NEEPU_JWT_SECRET', 'change-me')
    DEBUG = os.environ.get('NEPU_DEBUG', '1') in ('1', 'true', 'True')
    
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


settings = Settings()
