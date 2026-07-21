#!/usr/bin/env python3
"""为 E2E 预置一个已验证账号（走注册表 → 邮箱验证 → 可选提权管理员）。

输出 JSON 到 stdout，供 Playwright 读取：
  {"ok": true, "account": "...", "password": "...", "email": "...", "username": "...", "is_admin": true}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta

# 仓库根目录
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin", action="store_true", help="提权为管理员以覆盖 /admin/*")
    parser.add_argument("--prefix", default="e2e", help="用户名前缀")
    args = parser.parse_args()

    from backend.app import app
    from backend.server.db_models import User, RegistratingUser
    from backend.server import extensions
    from backend.server.audit_log import log_register

    stamp = time.strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    username = f"{args.prefix}_{stamp}_{suffix}"
    email = f"{username}@e2e.neepu.local"
    nickname = f"E2E_{suffix}"
    password = f"E2ePass_{suffix}9!"

    with app.app_context():
        # 清理同邮箱残留
        RegistratingUser.query.filter_by(email=email).delete()
        existing = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing:
            extensions.db.session.delete(existing)
            extensions.db.session.commit()

        # 模拟「注册提交」：写入待验证记录（跳过发信，避免本地邮件失败）
        from backend.server.email_service import generate_token

        token = generate_token()
        pending = RegistratingUser(
            email=email,
            nickname=nickname,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        pending.set_password(password)
        extensions.db.session.add(pending)
        extensions.db.session.commit()

        # 模拟「点击验证邮件」：创建正式用户（username 在正式用户表上）
        user = User(
            email=pending.email,
            nickname=pending.nickname,
            username=username,
            password_hash=pending.password_hash,
            email_verified=True,
        )
        if args.admin:
            user.is_admin = True
        extensions.db.session.add(user)
        extensions.db.session.delete(pending)
        extensions.db.session.commit()
        try:
            log_register(user)
        except Exception:
            pass

        payload = {
            "ok": True,
            "account": username,
            "username": username,
            "email": email,
            "nickname": nickname,
            "password": password,
            "user_id": user.id,
            "is_admin": bool(user.is_admin),
            "via": "register_pending_then_verify",
        }
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
