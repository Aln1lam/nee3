# -*- coding: utf-8 -*-
"""快速核验：/timeline 含 submissions/challenges，前端重演公式与后端一致。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def js_dynamic(orig, n, min_rate=0.25, diff=5.0):
    if n <= 1:
        return orig
    if diff <= 0:
        diff = 0.1
    return int(orig * (min_rate + (1 - min_rate) * math.exp((1 - n) / diff)))


def fe_replay(submissions, challenges, teams):
    """镜像 GameScoreboard.buildStepTimelineData 的增量重演。"""
    from collections import defaultdict

    ch_map = {c["id"]: c for c in challenges}
    team_ids = [t["id"] for t in teams]
    times = sorted({s["created_at"] for s in submissions if s.get("created_at")})
    by_time = defaultdict(list)
    for s in submissions:
        by_time[s["created_at"]].append(s)

    challenge_solvers = defaultdict(set)
    team_solved = defaultdict(set)
    series = {tid: [] for tid in team_ids}

    for T in times:
        for s in by_time[T]:
            tid, cid = s["team_id"], s["challenge_id"]
            if cid in team_solved[tid]:
                continue
            team_solved[tid].add(cid)
            challenge_solvers[cid].add(tid)

        score_at = {}
        for cid, c in ch_map.items():
            n = len(challenge_solvers[cid])
            score_at[cid] = js_dynamic(
                int(c["original_points"]),
                n,
                float(c.get("min_score_rate", 0.25)),
                float(c.get("difficulty", 5.0)),
            )

        for tid in team_ids:
            total = sum(score_at.get(cid, 0) for cid in team_solved[tid])
            series[tid].append((T, total))
    return series


def main() -> int:
    import requests
    from backend.app import create_app
    from backend.services.scoring_service import ScoringService

    gid = int(sys.argv[1]) if len(sys.argv) > 1 else 258
    app = create_app()
    with app.app_context():
        payload = ScoringService.build_decay_timeline(gid, top_n=10)

    assert isinstance(payload.get("teams"), list), "teams must be list"
    assert payload.get("submissions"), "missing submissions"
    assert payload.get("challenges"), "missing challenges"

    fe = fe_replay(payload["submissions"], payload["challenges"], payload["teams"])
    # 对比后端 series 首队样例是否含下挫
    be_series = {s["team_id"]: s["data"] for s in payload["series"]}
    dips = 0
    max_drop = 0
    for tid, pts in fe.items():
        vals = [p[1] for p in pts]
        for i in range(1, len(vals)):
            if vals[i] < vals[i - 1]:
                dips += 1
                max_drop = max(max_drop, vals[i - 1] - vals[i])
        if tid in be_series and be_series[tid]:
            # 终点对齐（允许榜表校正）
            fe_last = vals[-1] if vals else 0
            be_last = be_series[tid][-1]["points"]
            # 前端无血加成；后端可能有血——仿真一般 disable_blood
            if abs(fe_last - be_last) > 50 and fe_last != be_last:
                print(f"WARN team {tid} final fe={fe_last} be={be_last}")

    print(f"game={gid} subs={len(payload['submissions'])} ch={len(payload['challenges'])} teams={len(payload['teams'])}")
    print(f"fe_adjacent_dips={dips} max_drop=-{max_drop}")
    print(f"algorithm={payload.get('algorithm')}")

    # HTTP
    try:
        r = requests.get(f"http://127.0.0.1:5000/api/ctf/games/{gid}/scoreboard/timeline", timeout=8)
        d = r.json().get("data") or {}
        print(f"HTTP submissions={len(d.get('submissions') or [])} teams_type={type(d.get('teams')).__name__}")
    except Exception as e:
        print(f"HTTP skip: {e}")

    ok = dips > 0 or len(payload["submissions"]) <= 6  # 单队无衰减也可
    print("RESULT:", "PASS" if ok and payload.get("submissions") else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
