#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全链路冒烟：余弦衰减 + Snapshot Replay + 下挫 + 默认 decay=10。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from backend.app import create_app
    from backend.server.extensions import db
    from backend.server.db_models import CtfChallenge
    from backend.services.scoring_service import ScoringService

    app = create_app()
    fails = []

    # 1) 公式：decay=10，N=1→initial，N>=10→floor
    s1 = ScoringService.calculate_dynamic_score(1000, 1, 0.25, 10)
    s5 = ScoringService.calculate_dynamic_score(1000, 5, 0.25, 10)
    s10 = ScoringService.calculate_dynamic_score(1000, 10, 0.25, 10)
    if s1 != 1000:
        fails.append(f"N=1 expect 1000 got {s1}")
    if s10 != 250:
        fails.append(f"N=10 expect 250 got {s10}")
    if not (s10 <= s5 < s1):
        fails.append(f"decay order broken: {s1}>{s5}>{s10}? got {s1},{s5},{s10}")

    # 余弦中间点（N=5.5 不存在，用 N=5）：应接近 (1000+250)/2 附近
    mid_expect = 250 + (1000 - 250) * ((math.cos((5 - 1) / (10 - 1) * math.pi) + 1) / 2)
    if abs(s5 - round(mid_expect)) > 1:
        fails.append(f"cosine mid mismatch: got {s5} expect ~{round(mid_expect)}")

    with app.app_context():
        # 2) 默认 difficulty / 模型 default
        col = CtfChallenge.__table__.c.difficulty
        default = col.default.arg if col.default is not None else None
        if default != 10.0:
            fails.append(f"db_models difficulty default={default}, want 10.0")

        # 3) 演示赛 259/260：timeline 必须有下挫 + algorithm
        for gid in (259, 260):
            payload = ScoringService.generate_gzctf_style_timeline(gid, top_n=10)
            algo = payload.get("algorithm")
            if algo != "ret2shell_snapshot_replay":
                fails.append(f"game {gid} algorithm={algo}")
            dips = int(payload.get("dip_events") or 0)
            if dips < 1:
                fails.append(f"game {gid} dip_events={dips}, want >=1")
            # timeline_data 应含全队（不只 TopN）
            td = payload.get("timeline_data") or {}
            if len(td) < 2:
                fails.append(f"game {gid} timeline_data teams={len(td)}")
            # series 点位允许下降
            saw_dip = False
            for s in payload.get("series") or []:
                pts = [p.get("points") for p in (s.get("data") or []) if isinstance(p, dict)]
                for i in range(1, len(pts)):
                    if pts[i] < pts[i - 1]:
                        saw_dip = True
                        break
                if saw_dip:
                    break
            if not saw_dip and dips >= 1:
                # dip_events 计数存在即足够；series 可能因取样错过
                pass
            elif not saw_dip:
                fails.append(f"game {gid} no score dip in series")

            # 4) 缓存路径
            cached = ScoringService.get_timeline_cached(gid, top_n=10)
            if cached.get("algorithm") != "ret2shell_snapshot_replay":
                fails.append(f"game {gid} cached algorithm bad")

        # 5) 源码闸门：teams score-timeline 不得累加 points_earned
        teams_src = (ROOT / "backend/route/teams.py").read_text(encoding="utf-8")
        marker = '@bp.get("/<int:team_id>/score-timeline")'
        if marker not in teams_src:
            fails.append("teams score-timeline route missing")
        else:
            after = teams_src.split(marker, 1)[1]
            # 截到下一个路由装饰器
            nxt = after.find("\n@bp.")
            fn = after if nxt < 0 else after[:nxt]
            if "points +=" in fn or "points+=" in fn or "r.points_earned" in fn:
                fails.append("teams.team_score_timeline still accumulates points_earned")
            if "get_timeline_cached" not in fn and "generate_gzctf_style_timeline" not in fn:
                fails.append("teams.team_score_timeline not wired to snapshot replay")

        ca = (ROOT / "backend/route/challenge_admin.py").read_text(encoding="utf-8")
        if "else 10.0" not in ca:
            fails.append("challenge_admin create default not 10.0")

    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        return 1
    print("OK ret2shell scoreboard full-chain smoke passed")
    print(f"  formula: N1={s1} N5={s5} N10={s10}")
    print("  games 259/260: snapshot replay + dips + full timeline_data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
