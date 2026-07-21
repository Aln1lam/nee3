"""P0 regression: first-blood race must not assign multiple blood_level=0."""
import threading
import uuid
import sys

sys.path.insert(0, r"E:\neepu")

from flask_jwt_extended import create_access_token
from backend.app import create_app
from backend.server.extensions import db
from backend.server.db_models import User, CtfChallenge, CtfSolves, CtfChallengeSubmission
from backend.services.team_service import ensure_user_has_team
from tests.auth_helpers import set_auth_cookie


def auth_client(app, user_id):
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity=str(user_id))
    set_auth_cookie(client, token)
    return client


def main():
    app = create_app()
    tag = uuid.uuid4().hex[:8]
    flag = f"flag{{p0race_{tag}}}"
    user_ids = []

    with app.app_context():
        ch = CtfChallenge(
            game_id=68,
            title=f"p0-race-{tag}",
            description="p0",
            category="Misc",
            original_points=500,
            flag=flag,
            challenge_type=0,
            is_enabled=True,
        )
        db.session.add(ch)
        db.session.flush()
        cid = ch.id
        for i in range(3):
            uname = f"p0race_{tag}_{i}"
            u = User(email=f"{uname}@test.local", username=uname, nickname=uname, email_verified=True)
            u.set_password("RaceTest2025!")
            db.session.add(u)
            db.session.flush()
            ensure_user_has_team(u)
            user_ids.append(u.id)
        db.session.commit()

    for uid in user_ids:
        c = auth_client(app, uid)
        assert c.post("/api/competitions/68/join", json={}).status_code == 200

    results = []
    barrier = threading.Barrier(3)

    def worker(uid):
        client = auth_client(app, uid)
        barrier.wait()
        r = client.post(f"/api/challenges/{cid}/submit", json={"flag": flag})
        results.append((uid, r.status_code, r.get_json()))

    threads = [threading.Thread(target=worker, args=(uid,)) for uid in user_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("RESULTS")
    for uid, code, body in results:
        data = (body or {}).get("data") or {}
        print(uid, code, "blood=", data.get("blood_level"), "correct=", data.get("is_correct"), "msg=", (body or {}).get("msg"))

    with app.app_context():
        solves = CtfSolves.query.filter_by(challenge_id=cid).order_by(CtfSolves.blood_level).all()
        corrects = CtfChallengeSubmission.query.filter_by(challenge_id=cid, is_correct=True).all()
        levels = [s.blood_level for s in solves]
        print("solves", [(s.blood_level, s.user_id) for s in solves])
        print("correct_count", len(corrects))
        multi_first = levels.count(0) > 1
        print("PASS_NO_MULTI_FIRST", not multi_first)
        print("PASS_UNIQUE_LEVELS", len(levels) == len(set(levels)))
        # legacy /api/games 已 410，不应再产生重复正确提交
        client = auth_client(app, user_ids[0])
        r = client.post(f"/api/games/challenges/{cid}/submit", json={"flag": flag})
        print("legacy_status", r.status_code)
        n2 = CtfChallengeSubmission.query.filter_by(challenge_id=cid, user_id=user_ids[0], is_correct=True).count()
        print("PASS_LEGACY_GONE", r.status_code == 410)
        print("PASS_LEGACY_NO_DUP", n2 == 1)
        return 0 if (not multi_first and len(levels) == len(set(levels)) and r.status_code == 410 and n2 == 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
