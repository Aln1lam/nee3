# -*- coding: utf-8 -*-
"""前后端联调冒烟：容器销毁幽灵 / 动态包 / PCAP / 实例列表"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from backend.app import app
from backend.server.db_models import User, CtfGameInstance, CtfChallenge
from backend.services.container_service import container_service
from flask_jwt_extended import create_access_token

results = []

def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("OK" if cond else "FAIL"), name, detail)


with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    assert admin, "no admin"
    token = create_access_token(identity=str(admin.id))

    # 1) 幽灵对账
    ghosts = container_service.reconcile_ghost_instances()
    running = CtfGameInstance.query.filter_by(is_running=True).count()
    ok("ghost_reconcile", True, f"fixed={ghosts} still_running={running}")

    # 2) destroy 对不存在的 container_id 应成功并清库
    ghost = CtfGameInstance.query.filter(
        CtfGameInstance.container_id.isnot(None)
    ).order_by(CtfGameInstance.id.desc()).first()
    if ghost:
        fake_id = "a69666ba447cdb5e11bdd44cafdcc1718fbcdb60191425cc71a2f002e36b6499"
        old_cid, old_run = ghost.container_id, ghost.is_running
        ghost.container_id = fake_id
        ghost.is_running = True
        from backend.server.extensions import db
        db.session.commit()
        success, msg = container_service.destroy_container(ghost)
        ghost2 = CtfGameInstance.query.get(ghost.id)
        ok("destroy_missing_container", success and ghost2.is_running is False, msg)
        # restore cid for history (optional leave stopped)
        ghost2.container_id = old_cid
        db.session.commit()
    else:
        ok("destroy_missing_container", False, "no instance row to test")

    client = app.test_client()
    client.set_cookie("localhost", "neepu_token", token)

    # 3) API routes
    r = client.get("/api/admin/dynamic-packages/challenges/1/packages")
    body = r.get_json() or {}
    ok("dyn_pkg_stub", r.status_code == 200 and body.get("meta", {}).get("status") == "stub", r.status_code)

    r = client.post("/api/teams/", json={"name": "官方战队"})
    ok("team_sensitive", r.status_code == 400 and "不允许" in (r.get_json() or {}).get("msg", ""), r.status_code)

    r = client.get("/api/platform/instances")
    data = (r.get_json() or {}).get("data") or []
    ok("instances_list", r.status_code == 200, f"n={len(data)}")

    r = client.get("/api/competitions/admin/1/traffic-captures?sync=0")
    pj = r.get_json() or {}
    total = (pj.get("data") or {}).get("total")
    ok("pcap_list", r.status_code == 200 and total is not None, f"total={total}")

    # stop a stopped instance should still 200 if exists
    inst = CtfGameInstance.query.order_by(CtfGameInstance.id.desc()).first()
    if inst:
        r = client.post(f"/api/challenges/instances/{inst.id}/stop")
        ok("stop_instance_api", r.status_code == 200, f"id={inst.id} status={r.status_code} {(r.get_json() or {}).get('msg')}")
    else:
        ok("stop_instance_api", False, "no instance")

    # container-status for challenge 1
    r = client.get("/api/challenges/1/container-status")
    ok("container_status", r.status_code == 200, str((r.get_json() or {}).get("data", {}).get("status")))

failed = [n for n, c, _ in results if not c]
print("SUMMARY", f"{len(results)-len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
