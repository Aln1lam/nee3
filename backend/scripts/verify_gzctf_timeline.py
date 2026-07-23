# -*- coding: utf-8 -*-
"""
GZCTF 式 Snapshot Replay Timeline —— 写入 scoring_service 核心算法补丁说明。
本脚本不直接改文件，仅作核验；实际算法已内嵌于 ScoringService.generate_gzctf_style_timeline。
"""
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


def gzctf_challenge_score(original_points: int, count: int, min_rate: float, diff: float) -> int:
    if count <= 0:
        return 0
    if count <= 1:
        return int(original_points)
    if diff <= 0:
        diff = 0.1
    decay = math.exp((1 - count) / diff)
    score = original_points * (min_rate + (1 - min_rate) * decay)
    floor = int(original_points * min_rate)
    return max(int(score), floor)


def main() -> int:
    from backend.app import create_app
    from backend.services.scoring_service import ScoringService

    app = create_app()
    gid = int(sys.argv[1]) if len(sys.argv) > 1 else 258
    with app.app_context():
        payload = ScoringService.generate_gzctf_style_timeline(gid, top_n=10)
        assert payload.get("algorithm") == "gzctf_snapshot_replay"
        series = payload.get("series") or []
        dips = 0
        max_drop = 0
        for s in series:
            pts = [p["points"] for p in (s.get("data") or [])]
            for i in range(1, len(pts)):
                if pts[i] < pts[i - 1]:
                    dips += 1
                    max_drop = max(max_drop, pts[i - 1] - pts[i])
        print(f"game={gid} algo={payload.get('algorithm')} dips={dips} max_drop=-{max_drop}")
        print(f"events={payload.get('events')} cached_hint={payload.get('from_cache')}")
        if series:
            sample = [p["points"] for p in (series[0].get("data") or [])[:10]]
            print(f"sample[{series[0].get('team_name')}]={sample}")
        ok = dips > 0 or int(payload.get("events") or 0) < 3
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
