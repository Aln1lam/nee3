# -*- coding: utf-8 -*-
"""Patch scoring_service.py: GZCTF Snapshot Replay Timeline."""
from pathlib import Path

NEW = r'''
    @staticmethod
    def generate_gzctf_style_timeline(game_id: int, top_n: int = 10) -> Dict:
        """
        GZCTF 式 ScoreTimeLine：基于事件的快照重演（Snapshot Replay）。

        彻底废弃「累加 points_earned」：每个正确提交事件 T，
        按当时唯一解题队数 N 重算每题动态分，再对每队 Σ 得到绝对总分。
        允许 TotalScore_T < TotalScore_{T-1}（真实垂直下挫）。
        """
        from collections import defaultdict

        challenges = {
            c.id: c
            for c in CtfChallenge.query.filter_by(game_id=game_id).all()
        }
        rows = (
            CtfChallengeSubmission.query.filter_by(game_id=game_id, is_correct=True)
            .order_by(
                CtfChallengeSubmission.submitted_at.asc(),
                CtfChallengeSubmission.id.asc(),
            )
            .all()
        )

        team_names: Dict[int, str] = {}
        for sb in CtfScoreboard.query.filter_by(game_id=game_id).all():
            if not sb.team_id:
                continue
            t = Team.query.get(sb.team_id)
            team_names[sb.team_id] = t.name if t else f"Team #{sb.team_id}"

        solve_counts: Dict[int, int] = {cid: 0 for cid in challenges}
        team_solved: Dict[int, set] = defaultdict(set)
        # timeline_data[team_id] = [[iso, score], ...]
        timeline_data: Dict[int, List] = defaultdict(list)
        prev_score: Dict[int, int] = {}
        event_count = 0
        dip_events = 0

        def challenge_score_now(cid: int, count: int) -> int:
            ch = challenges.get(cid)
            if not ch or count <= 0:
                return 0
            original = int(getattr(ch, "original_points", None) or 0)
            if count <= 1:
                return original
            min_rate = getattr(ch, "min_score_rate", None)
            min_rate = 0.25 if min_rate is None else float(min_rate)
            diff = getattr(ch, "difficulty", None)
            diff = 5.0 if diff is None else float(diff)
            if diff <= 0:
                diff = 0.1
            decay = math.exp((1 - count) / diff)
            raw = original * (min_rate + (1 - min_rate) * decay)
            floor = int(original * min_rate)
            return max(int(raw), floor)

        for sub in rows:
            tid = sub.team_id
            cid = sub.challenge_id
            if not tid or cid not in challenges:
                continue
            if tid not in team_names:
                t = Team.query.get(tid)
                team_names[tid] = t.name if t else f"Team #{tid}"

            # 同队同题重复 AC：不推进
            if cid in team_solved[tid]:
                continue

            team_solved[tid].add(cid)
            solvers = {t for t, solved in team_solved.items() if cid in solved}
            solve_counts[cid] = len(solvers)
            event_count += 1

            timestamp = sub.submitted_at.isoformat() if sub.submitted_at else None

            current_challenge_scores: Dict[int, int] = {}
            for solved_cid, count in solve_counts.items():
                if count <= 0:
                    continue
                current_challenge_scores[solved_cid] = challenge_score_now(solved_cid, count)

            # 结算全场已上场队伍绝对总分（允许下挫，禁止 Math.max 防降）
            for team_id, solved_set in team_solved.items():
                total_score = sum(
                    current_challenge_scores.get(c, 0) for c in solved_set
                )
                prev = prev_score.get(team_id)
                if prev is not None and total_score < prev:
                    dip_events += 1
                hist = timeline_data[team_id]
                if hist and hist[-1][0] == timestamp and hist[-1][1] == total_score:
                    continue
                hist.append([timestamp, int(total_score)])
                prev_score[team_id] = int(total_score)

        ranked = sorted(prev_score.items(), key=lambda x: (-x[1], x[0]))[: max(1, int(top_n))]
        top_ids = [tid for tid, _ in ranked]

        series = []
        for tid in top_ids:
            pts = timeline_data.get(tid) or []
            series.append({
                "team_id": tid,
                "team_name": team_names.get(tid, f"Team #{tid}"),
                "data": [{"time": p[0], "points": p[1]} for p in pts],
                "points": pts,
                "final_points": prev_score.get(tid, 0),
            })

        submissions_payload = []
        seen_pair = set()
        for r in rows:
            if not r.team_id:
                continue
            key = (r.team_id, r.challenge_id)
            if key in seen_pair:
                continue
            seen_pair.add(key)
            submissions_payload.append({
                "team_id": r.team_id,
                "challenge_id": r.challenge_id,
                "created_at": r.submitted_at.isoformat() if r.submitted_at else None,
            })

        challenges_payload = [
            {
                "id": c.id,
                "title": c.title,
                "original_points": int(c.original_points or 0),
                "min_score_rate": float(c.min_score_rate if c.min_score_rate is not None else 0.25),
                "difficulty": float(c.difficulty if c.difficulty is not None else 5.0),
            }
            for c in challenges.values()
        ]
        teams_payload = [
            {"id": tid, "name": team_names.get(tid, f"Team #{tid}")}
            for tid in sorted(team_names.keys())
        ]

        timeline_map = {str(tid): timeline_data.get(tid, []) for tid in top_ids}

        return {
            "series": series,
            "timeline_data": timeline_map,
            "teams": teams_payload,
            "team_count": len(team_solved),
            "challenges": challenges_payload,
            "submissions": submissions_payload,
            "algorithm": "gzctf_snapshot_replay",
            "events": event_count,
            "dip_events": dip_events,
        }

    @staticmethod
    def build_decay_timeline(game_id: int, top_n: int = 10) -> Dict:
        """兼容别名 → GZCTF Snapshot Replay。"""
        return ScoringService.generate_gzctf_style_timeline(game_id, top_n=top_n)

    @staticmethod
    def get_timeline_cached(game_id: int, top_n: int = 10) -> Dict:
        """ScoreboardCacheHandler：优先读 Redis Timeline 快照。"""
        try:
            from backend.services.redis_service import get_redis, ScoreboardCache
            rs = get_redis()
            if rs and rs.is_available():
                cached = ScoreboardCache.get_cached_timeline(rs, game_id)
                if cached and isinstance(cached, dict) and cached.get("series") is not None:
                    out = dict(cached)
                    out["from_cache"] = True
                    return out
        except Exception:
            pass

        payload = ScoringService.generate_gzctf_style_timeline(game_id, top_n=top_n)
        payload["from_cache"] = False
        try:
            from backend.services.redis_service import get_redis, ScoreboardCache
            rs = get_redis()
            if rs and rs.is_available():
                ScoreboardCache.cache_timeline(rs, game_id, payload)
        except Exception:
            pass
        return payload

'''

def main():
    path = Path(r"E:\neepu\backend\services\scoring_service.py")
    text = path.read_text(encoding="utf-8")
    start = text.find("    @staticmethod\n    def build_decay_timeline(")
    end = text.find("    @staticmethod\n    def resolve_last_submission_time(")
    if start < 0 or end < 0:
        raise SystemExit(f"markers not found start={start} end={end}")
    # keep leading newline consistency
    new_text = text[:start] + NEW.lstrip("\n") + text[end:]
    path.write_text(new_text, encoding="utf-8")
    print("OK patched", path)
    # syntax check
    compile(new_text, str(path), "exec")
    print("OK syntax")

if __name__ == "__main__":
    main()
