#!/usr/bin/env python
"""检查数据库中的用户数据"""

from app import app
from backend.db_models import User

with app.app_context():
    # 查询第一个用户（ID=1）
    user = User.query.get(1)
    if user:
        print(f"用户ID: {user.id}")
        print(f"用户昵称: {user.nickname}")
        print(f"用户头像: {user.avatar}")
        print(f"用户签名: {user.signature}")
        print(f"\nto_dict() 返回:")
        import json
        print(json.dumps(user.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("没有找到ID为1的用户")
        print("\n所有用户:")
        all_users = User.query.all()
        for u in all_users:
            print(f"ID: {u.id}, 昵称: {u.nickname}, 头像: {u.avatar}")
