#!/usr/bin/env python3
"""创建 NEEPU CTF 平台管理员账号（幂等）"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.app import app
from backend.server.extensions import db
from backend.server.db_models import User

ADMIN_EMAIL = os.environ.get('NEEPU_ADMIN_EMAIL', 'admin@neepu.edu.cn')
ADMIN_USERNAME = os.environ.get('NEEPU_ADMIN_USERNAME', 'neepu_admin')
ADMIN_PASSWORD = os.environ.get('NEEPU_ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise SystemExit(
        '请设置环境变量 NEEPU_ADMIN_PASSWORD 后再创建管理员（禁止使用内置默认口令）'
    )
ADMIN_NICKNAME = os.environ.get('NEEPU_ADMIN_NICKNAME', 'NEEPU 运维')


def main():
    with app.app_context():
        user = User.query.filter(
            (User.email == ADMIN_EMAIL) | (User.username == ADMIN_USERNAME)
        ).first()

        if user:
            user.is_admin = True
            user.email_verified = True
            user.nickname = ADMIN_NICKNAME
            user.set_password(ADMIN_PASSWORD)
            action = '更新'
        else:
            user = User(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                nickname=ADMIN_NICKNAME,
                is_admin=True,
                email_verified=True,
            )
            user.set_password(ADMIN_PASSWORD)
            db.session.add(user)
            action = '创建'

        db.session.commit()
        print(f'[OK] {action} admin success')
        print(f'  邮箱: {ADMIN_EMAIL}')
        print(f'  用户名: {ADMIN_USERNAME}')
        print(f'  密码: {ADMIN_PASSWORD}')
        print(f'  登录: http://localhost:5173/auth')


if __name__ == '__main__':
    main()
