# -*- coding: utf-8 -*-
"""S1 live checks via Flask test client + JWT（避开 login 限流）。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from backend.app import app
from backend.server.db_models import User
from flask_jwt_extended import create_access_token

with app.app_context():
    admin = User.query.filter(
        (User.email == "admin@neepu.edu.cn") | (User.username == "neepu_admin")
    ).first()
    if not admin:
        admin = User.query.filter_by(is_admin=True).first()
    assert admin, "no admin user in DB"
    token = create_access_token(identity=str(admin.id))

client = app.test_client()
client.set_cookie("localhost", "neepu_token", token)

r = client.get("/api/admin/dynamic-packages/challenges/1/packages")
assert r.status_code == 200, r.data
body = r.get_json()
assert body["meta"]["status"] == "stub"
assert body["data"] == []
print("dyn_pkg OK")

r = client.post("/api/admin/dynamic-packages/challenges/1/upload")
assert r.status_code == 501
print("dyn_upload 501 OK")

r = client.post("/api/teams/", json={"name": "官方战队"})
assert r.status_code == 400
assert "不允许" in (r.get_json() or {}).get("msg", "")
print("team_sensitive OK")

r = client.get("/api/challenges/1/container-status")
assert r.status_code != 404
print("container_status", r.status_code)

r = client.get("/api/platform/instances")
assert r.status_code == 200
print("instances", r.status_code, "n=", len((r.get_json() or {}).get("data") or []))

r = client.post("/api/challenges/1/submit", json={"flag": "flag{x}"})
assert r.status_code != 404
print("submit", r.status_code)

# hint / hammer routes exist
r = client.get("/api/challenges/1/hints")
print("hints", r.status_code)
r = client.get("/api/challenges/1/hammer")
print("hammer_get", r.status_code)

print("CLIENT_LIVE_OK")
