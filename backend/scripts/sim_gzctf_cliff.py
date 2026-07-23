# -*- coding: utf-8 -*-
"""多人连解同一高分题 → 验证垂直下挫。"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from backend.app import create_app
    from backend.server.extensions import db
    from backend.server.db_models import (
        User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
        CtfParticipation, CtfParticipatingUser,
    )
    from backend.services.scoring_service import ScoringService

    tag = datetime.utcnow().strftime("%H%M%S")
    app = create_app()
    with app.app_context():
        start = datetime.utcnow() - timedelta(hours=1)
        game = CtfGame(
            title=f"[GZCTF-SIM] cliff {tag}",
            description="multi-solve cliff",
            start_time=start,
            end_time=start + timedelta(days=1),
            is_public=True,
            status="ongoing",
        )
        db.session.add(game)
        db.session.flush()

        ch = CtfChallenge(
            game_id=game.id,
            title="BossWeb",
            category="Web",
            description="high value decay",
            original_points=1000,
            min_score_rate=0.20,
            difficulty=1.0,
            flag=f"flag{{cliff_{tag}}}",
            challenge_type=0,
            is_enabled=True,
            disable_blood_bonus=True,
        )
        db.session.add(ch)
        db.session.flush()

        teams = []
        users = []
        for i in range(1, 6):
            u = User(
                email=f"cliff_{tag}_u{i}@sim.local",
                username=f"cliff_{tag}_u{i}",
                nickname=f"C{i}",
                email_verified=True,
            )
            u.set_password("Cliff2025!")
            db.session.add(u)
            db.session.flush()
            t = Team(name=f"Cliff-{tag}-{i}", invite_code=uuid.uuid4().hex[:16])
            db.session.add(t)
            db.session.flush()
            u.team_id = t.id
            part = CtfParticipation(game_id=game.id, team_id=t.id, status="confirmed")
            db.session.add(part)
            db.session.flush()
            db.session.add(CtfParticipatingUser(
                user_id=u.id, game_id=game.id, team_id=t.id, participation_id=part.id,
            ))
            teams.append(t)
            users.append(u)
        db.session.commit()

        t0 = start + timedelta(minutes=5)
        for i, (team, user) in enumerate(zip(teams, users)):
            ts = t0 + timedelta(minutes=i * 3)
            sub = CtfChallengeSubmission(
                user_id=user.id,
                team_id=team.id,
                challenge_id=ch.id,
                game_id=game.id,
                answer=ch.flag,
                is_correct=True,
                points_earned=0,
                status=0,
                submitted_at=ts,
                correct_dedupe_key=f"cliff:{tag}:c{ch.id}:t{team.id}",
            )
            db.session.add(sub)
            db.session.flush()
            ScoringService.recalculate_challenge_scores(ch.id)
            db.session.commit()

        payload = ScoringService.generate_gzctf_style_timeline(game.id, top_n=5)
        print(f"game_id={game.id} algo={payload.get('algorithm')}")
        print(f"events={payload.get('events')} dip_events={payload.get('dip_events')}")

        # Team1 应先 1000，随后连续下挫
        s0 = (payload.get("series") or [None])[0]
        if not s0:
            print("FAIL: no series")
            return 1
        pts = [p["points"] for p in s0["data"]]
        print(f"team1[{s0['team_name']}] trajectory={pts}")
        has_cliff = any(pts[i] < pts[i - 1] for i in range(1, len(pts)))
        big_drop = max((pts[i - 1] - pts[i] for i in range(1, len(pts)) if pts[i] < pts[i - 1]), default=0)
        print(f"has_vertical_cliff={has_cliff} biggest_drop=-{big_drop}")
        print(f"BossWeb final dynamic={ScoringService.challenge_base_dynamic_score(ch)}")

        ok = has_cliff and big_drop >= 100 and pts[0] == 1000
        print("RESULT:", "PASS" if ok else "FAIL")
        print(f">>> open scoreboard game {game.id}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
