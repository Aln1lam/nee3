# -*- coding: utf-8 -*-
"""
动态积分衰减 & ECharts timeline 下挫 — 全流程仿真压测

用法:
  python backend/scripts/sim_dynamic_decay_stress.py

流程:
  1) 创建测试赛事 + 5 题（难度 1.0~2.0，最小分率 0.20，原始分 1000）
  2) 创建 12 支队伍
  3) 在 2 小时时间线上模拟 50+ 次正确提交，每次调用 recalculate_challenge_scores
  4) 检验 timeline 是否存在「后段分 < 前段分」的下挫点
"""
from __future__ import annotations

import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Windows 控制台 UTF-8，避免中文概览乱码
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TAG = datetime.utcnow().strftime("%m%d%H%M%S")
TEAM_COUNT = 12
TARGET_SOLVES = 55
RNG = random.Random(20260723)


def _dedupe_key(challenge_id: int, team_id: int) -> str:
    return f"sim:{TAG}:c{challenge_id}:t{team_id}"


def analyze_timeline_dips(series: list[dict]) -> dict:
    """统计各队时间线上的最大下挫幅度。"""
    max_drop = 0
    drop_events = 0
    worst = None  # (team, from, to, drop)
    samples = []

    for team in series:
        name = team.get("team_name") or f"Team#{team.get('team_id')}"
        pts = [p.get("points") for p in (team.get("data") or []) if p.get("points") is not None]
        times = [p.get("time") for p in (team.get("data") or [])]
        peak = None
        for i, v in enumerate(pts):
            if peak is None or v > peak:
                peak = v
            if peak is not None and v < peak:
                drop = peak - v
                drop_events += 1
                if drop > max_drop:
                    max_drop = drop
                    worst = (name, peak, v, drop, times[i] if i < len(times) else None)
                if len(samples) < 8 and drop >= 50:
                    samples.append(f"{name}: {peak} -> {v} ({times[i] if i < len(times) else ''})")

        # 相邻点下挫
        for i in range(1, len(pts)):
            if pts[i] < pts[i - 1]:
                drop = pts[i - 1] - pts[i]
                if drop > max_drop:
                    max_drop = drop
                    worst = (name, pts[i - 1], pts[i], drop, times[i] if i < len(times) else None)

    return {
        "max_drop": max_drop,
        "drop_events": drop_events,
        "worst": worst,
        "samples": samples,
        "teams_with_series": len(series),
    }


def main() -> int:
    from backend.app import create_app
    from backend.server.extensions import db
    from backend.server.db_models import (
        User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
        CtfParticipation, CtfParticipatingUser, CtfScoreboard,
    )
    from backend.services.scoring_service import ScoringService

    app = create_app()
    print("=" * 64)
    print(f"  Dynamic Decay Stress Simulation  tag={TAG}")
    print("=" * 64)

    with app.app_context():
        # ── 1. 赛事 ──
        start = datetime.utcnow().replace(microsecond=0) - timedelta(hours=3)
        end = start + timedelta(days=2)
        game = CtfGame(
            title=f"[SIM] 动态衰减压测 {TAG}",
            description="仿真：难度 1~2 / 分率 0.20 / 折线下挫",
            start_time=start,
            end_time=end,
            is_public=True,
            status="ongoing",
        )
        # optional fields
        if hasattr(game, "summary"):
            game.summary = "decay stress"
        db.session.add(game)
        db.session.flush()
        gid = game.id
        print(f"\n[1] 创建赛事 id={gid}  title={game.title}")

        # ── 2. 5 道题 ──
        ch_specs = [
            ("Web1", "Web", 1.0),
            ("Web2", "Web", 1.2),
            ("Pwn1", "Pwn", 1.5),
            ("Crypto1", "Crypto", 1.8),
            ("Misc1", "Misc", 2.0),
        ]
        challenges = []
        for title, cat, diff in ch_specs:
            flag = f"flag{{sim_{TAG}_{title.lower()}}}"
            ch = CtfChallenge(
                game_id=gid,
                title=title,
                category=cat,
                description=f"SIM {title} decay={diff}",
                original_points=1000,
                min_score_rate=0.20,
                difficulty=diff,
                flag=flag,
                challenge_type=0,
                is_enabled=True,
                disable_blood_bonus=True,  # 压测聚焦衰减，关闭血加成干扰
            )
            db.session.add(ch)
            challenges.append(ch)
        db.session.flush()
        print("[2] 创建题目:")
        for ch in challenges:
            print(f"     - {ch.title}: pts=1000 rate={ch.min_score_rate} diff={ch.difficulty} id={ch.id}")

        # ── 3. 队伍 + 用户 + 报名 ──
        teams = []
        users = []
        for i in range(1, TEAM_COUNT + 1):
            uname = f"sim_decay_{TAG}_u{i}"
            tname = f"SIM-Team-{TAG}-{i:02d}"
            u = User(
                email=f"{uname}@sim.local",
                username=uname,
                nickname=f"Sim{i}",
                email_verified=True,
            )
            u.set_password("SimDecay2025!")
            db.session.add(u)
            db.session.flush()
            team = Team(name=tname, invite_code=uuid.uuid4().hex[:16])
            db.session.add(team)
            db.session.flush()
            u.team_id = team.id
            part = CtfParticipation(game_id=gid, team_id=team.id, status="confirmed")
            db.session.add(part)
            db.session.flush()
            db.session.add(CtfParticipatingUser(
                user_id=u.id, game_id=gid, team_id=team.id, participation_id=part.id,
            ))
            teams.append(team)
            users.append(u)
        db.session.commit()
        print(f"[3] 创建队伍 {len(teams)} 支（每队 1 用户）")

        # ── 4. 构造时间线事件（2 小时）──
        t0 = start + timedelta(hours=1)  # 比赛开赛后 1h 起跑
        # 剧本：Web1 连续被多队解出，制造明确下挫
        scripted = [
            (0, 5, 0),    # Team1 @ +5min  Web1
            (1, 12, 0),   # Team2 @ +12min Web1  → Team1 下挫
            (2, 20, 0),   # Team3 Web1
            (3, 25, 0),   # Team4 Web1
            (4, 28, 0),   # Team5 Web1
            (0, 32, 2),   # Team1 Pwn1 抬升
            (5, 35, 0),   # Team6 Web1
            (1, 40, 2),   # Team2 Pwn1
            (6, 45, 1),   # Team7 Web2
            (2, 50, 2),   # Team3 Pwn1 → Pwn 衰减
        ]
        events = []  # (minute_offset, team_idx, ch_idx)
        seen = set()
        for ti, minute, ci in scripted:
            key = (ti, ci)
            if key not in seen:
                seen.add(key)
                events.append((minute, ti, ci))

        # 随机填充至 TARGET_SOLVES
        while len(events) < TARGET_SOLVES:
            ti = RNG.randint(0, TEAM_COUNT - 1)
            ci = RNG.randint(0, len(challenges) - 1)
            key = (ti, ci)
            if key in seen:
                continue
            seen.add(key)
            minute = RNG.randint(55, 119)
            events.append((minute, ti, ci))

        events.sort(key=lambda x: (x[0], x[1], x[2]))
        print(f"[4] 计划提交事件 {len(events)} 次（含剧本 Web1 连解）")

        # ── 5. 逐条提交 + 全员重算 ──
        ok_count = 0
        for minute, ti, ci in events:
            team = teams[ti]
            user = users[ti]
            ch = challenges[ci]
            ts = t0 + timedelta(minutes=minute, seconds=RNG.randint(0, 40))
            sub = CtfChallengeSubmission(
                user_id=user.id,
                team_id=team.id,
                challenge_id=ch.id,
                game_id=gid,
                answer=ch.flag,
                is_correct=True,
                points_earned=0,
                status=0,
                submitted_at=ts,
                correct_dedupe_key=_dedupe_key(ch.id, team.id),
            )
            db.session.add(sub)
            db.session.flush()
            ScoringService.recalculate_challenge_scores(ch.id)
            db.session.commit()
            ok_count += 1

        print(f"[5] 已落库正确提交 {ok_count} 次，并触发 recalculate_challenge_scores")

        # ── 6. Scoreboard 快照 ──
        boards = (
            CtfScoreboard.query.filter_by(game_id=gid)
            .order_by(CtfScoreboard.total_points.desc())
            .limit(8)
            .all()
        )
        print("\n[6] 排行榜 TOP8:")
        for i, sb in enumerate(boards, 1):
            tname = next((t.name for t in teams if t.id == sb.team_id), f"#{sb.team_id}")
            print(f"     #{i}  {tname}: {sb.total_points} pts  solved={sb.solved_challenges}")

        # ── 7. Timeline 下挫检验 ──
        payload = ScoringService.build_decay_timeline(gid, top_n=10)
        series = payload.get("series") or []
        stats = analyze_timeline_dips(series)

        print("\n[7] Timeline 下挫分析:")
        print(f"     总提交数: {ok_count}")
        print(f"     时间线队伍数: {stats['teams_with_series']}")
        print(f"     检测到下挫事件数: {stats['drop_events']}")
        print(f"     最高下挫幅度: -{stats['max_drop']}pts")
        if stats["worst"]:
            name, hi, lo, drop, when = stats["worst"]
            print(f"     最深下挫: {name}  {hi} -> {lo}  (-{drop}) @ {when}")
        if stats["samples"]:
            print("     样例:")
            for s in stats["samples"][:5]:
                print(f"       · {s}")

        # 验证 Web1 当前动态分确实远低于 1000
        web1 = challenges[0]
        n = ScoringService.count_accepted_solvers(web1.id)
        cur = ScoringService.challenge_base_dynamic_score(web1, n)
        print(f"\n[8] Web1 当前: solvers={n}  dynamic_score={cur} (original=1000, diff={web1.difficulty})")

        has_dip = stats["max_drop"] > 0
        significant = stats["max_drop"] >= 100

        print("\n" + "=" * 64)
        if has_dip and significant:
            print("  RESULT: PASS — 检测到显著积分下挫，衰减链路生效")
        elif has_dip:
            print("  RESULT: WEAK PASS — 有下挫但幅度较小")
        else:
            print("  RESULT: FAIL — timeline 未出现下挫点")
        print("=" * 64)
        print(f"\n>>> 请打开前端: 赛场 -> 比赛「{game.title}」-> 积分榜")
        print(f">>> 游戏 ID: {gid}")
        print(">>> 观察阶梯折线的下挫与排名交错波动效果。\n")

        # 可选：HTTP 核验（若本机服务指向同一库）
        try:
            import requests
            r = requests.get(
                f"http://127.0.0.1:5000/api/ctf/games/{gid}/scoreboard/timeline",
                timeout=8,
            )
            if r.status_code == 200:
                body = r.json()
                data = body.get("data") or body
                http_series = data.get("series") or []
                http_stats = analyze_timeline_dips(http_series)
                print(f"[HTTP] /timeline 下挫检测: max_drop=-{http_stats['max_drop']}pts  teams={http_stats['teams_with_series']}")
            else:
                print(f"[HTTP] timeline status={r.status_code} (可忽略，以内核结果为准)")
        except Exception as e:
            print(f"[HTTP] 跳过 ({e})")

        return 0 if has_dip else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"\nFATAL: {exc}")
        raise SystemExit(2)
