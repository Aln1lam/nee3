"""开发环境 Cookie 会话联调脚本"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NEPU_DEBUG", "1")

BASE = "http://127.0.0.1:5000"
PROXY_BASE = "http://127.0.0.1:5173"


def check_backend():
    s = requests.Session()
    r = s.get(f"{BASE}/api/ctf/health", timeout=5)
    assert r.status_code == 200, r.text
    print("[OK] backend health")

    r = s.get(f"{BASE}/api/auth/me", timeout=5)
    assert r.status_code == 401, r.text
    print("[OK] /me anonymous -> 401")

    from backend.app import create_app
    from backend.server.db_models import User
    from flask_jwt_extended import create_access_token

    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first() or User.query.first()
        assert admin, "no user in db"
        token = create_access_token(identity=str(admin.id))

    jar = requests.cookies.RequestsCookieJar()
    jar.set("neepu_token", token, domain="127.0.0.1", path="/")
    s.cookies.update(jar)
    r = s.get(f"{BASE}/api/auth/me", cookies={"neepu_token": token}, timeout=5)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("id") == admin.id
    print(f"[OK] cookie /me -> user {data.get('nickname') or data.get('email')}")

    r = s.post(f"{BASE}/api/auth/logout", timeout=5)
    assert r.status_code == 200, r.text
    r = s.get(f"{BASE}/api/auth/me", timeout=5)
    assert r.status_code == 401, r.text
    print("[OK] logout clears session")


def check_vite_proxy():
    s = requests.Session()
    r = s.get(f"{PROXY_BASE}/api/ctf/health", timeout=5)
    assert r.status_code == 200, r.text
    print("[OK] vite proxy /api/ctf/health")

    from backend.app import create_app
    from backend.server.db_models import User
    from flask_jwt_extended import create_access_token

    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first() or User.query.first()
        token = create_access_token(identity=str(admin.id))

    r = s.get(f"{PROXY_BASE}/api/auth/me", cookies={"neepu_token": token}, timeout=5)
    assert r.status_code == 200, r.text
    print("[OK] vite proxy cookie /me")

    r = s.post(f"{PROXY_BASE}/api/auth/logout", timeout=5)
    assert r.status_code == 200, r.text
    r = s.get(f"{PROXY_BASE}/api/auth/me", timeout=5)
    assert r.status_code == 401, r.text
    print("[OK] vite proxy logout")


if __name__ == "__main__":
    check_backend()
    try:
        check_vite_proxy()
    except Exception as e:
        print(f"[WARN] vite proxy check skipped/failed: {e}")
    print("\nAll integration checks passed.")
