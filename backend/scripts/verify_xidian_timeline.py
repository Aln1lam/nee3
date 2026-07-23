# -*- coding: utf-8 -*-
"""核验西电式 Replay Timeline：下挫点 + 终点与排行榜一致。"""
from __future__ import annotations

import sys
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
    from backend.server.db_models import CtfScoreboard
    from backend.services.scoring_service import ScoringService

    app = create_app()
    gid = int(sys.argv[1]) if len(sys.argv) > 1 else 257

    with app.app_context():
        payload = ScoringService.build_decay_timeline(gid, top_n=10)
        assert payload.get("algorithm") == "xidian_replay", payload
        series = payload.get("series") or []
        boards = {
            sb.team_id: int(sb.total_points or 0)
            for sb in CtfScoreboard.query.filter_by(game_id=gid).all()
            if sb.team_id
        }

        max_drop = 0
        adj_dips = 0
        mismatches = []

        for s in series:
            pts = [p["points"] for p in (s.get("data") or [])]
            tid = s.get("team_id")
            for i in range(1, len(pts)):
                if pts[i] < pts[i - 1]:
                    adj_dips += 1
                    max_drop = max(max_drop, pts[i - 1] - pts[i])
            if pts and tid in boards:
                # 榜表已回写时应对齐；陈旧 0 分不强制
                if boards[tid] > 0 and pts[-1] != boards[tid]:
                    mismatches.append((s.get("team_name"), pts[-1], boards[tid]))
                elif boards[tid] == 0 and pts[-1] > 0:
                    pass  # stale board — timeline 以重演为准

        print(f"game={gid} algorithm={payload.get('algorithm')}")
        print(f"events={payload.get('events')} dip_events={payload.get('dip_events')}")
        print(f"series_teams={len(series)} adjacent_dips={adj_dips} max_drop=-{max_drop}")
        if series:
            s0 = series[0]
            sample = [p["points"] for p in (s0.get("data") or [])[:12]]
            print(f"sample[{s0.get('team_name')}]={sample}")
        print(f"endpoint_board_mismatches={len(mismatches)}")
        for m in mismatches[:5]:
            print("  mismatch", m)

        ok = adj_dips > 0 and not mismatches
        # 无多队同题时可能无下挫（如 game 248）；仅检查算法字段与终点一致
        if payload.get("dip_events", 0) == 0 and not mismatches:
            print("NOTE: 无下挫（可能每题仅 1 队解出）；算法与终点校验通过")
            ok = True
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
