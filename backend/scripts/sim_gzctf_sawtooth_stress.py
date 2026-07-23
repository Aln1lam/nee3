# -*- coding: utf-8 -*-
"""
高频锯齿下挫压测数据注入（GZCTF Snapshot Replay）

- 5 题：original=1000, difficulty=2.0, min_rate=0.2
- 50 队
- 60 分钟窗口内密集 unique AC（队×题唯一；上限 250）
- 相邻提交间隔 3~15 秒；热门题 30+ 队连解
- 落库后全员重算 + Timeline 快照

用法:
  python backend/scripts/sim_gzctf_sawtooth_stress.py
"""
from __future__ import annotations

import random
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 不在标题末尾挂纯数字时间戳，避免被 ephemeral 过滤器隐藏
GAME_TITLE = "[GZCTF-SIM] 高频锯齿下挫演示"
TEAM_COUNT = 50
CHALLENGE_SPECS = [
    ("HotWeb", "Web"),      # 热门：尽量 50 队全解
    ("HotPwn", "Pwn"),      # 热门：尽量 50 队全解
    ("CryptoX", "Crypto"),  # 中热：35+
    ("RevY", "Reverse"),    # 中热：30+
    ("MiscZ", "Misc"),      # 尾部：25+
]
TARGET_MIN, TARGET_MAX = 600, 800  # 目标提交行数（含可计分 AC + 同题重复 AC 填充）
INTERVAL_LO, INTERVAL_HI = 3, 15
WINDOW_MINUTES = 60
RNG = random.Random(20260723)


def main() -> int:
    from backend.app import create_app
    from backend.server.extensions import db
    from backend.server.db_models import (
        User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
        CtfParticipation, CtfParticipatingUser,
    )
    from backend.services.scoring_service import ScoringService
    from backend.services.redis_service import get_redis, ScoreboardCache

    uid = uuid.uuid4().hex[:8]
    app = create_app()
    print("=" * 64)
    print("  GZCTF Sawtooth Stress Injection")
    print("=" * 64)

    with app.app_context():
        now = datetime.utcnow().replace(microsecond=0)
        # 比赛窗口：已开始 90 分钟，注入落在「开赛后 20~80 分钟」共 60 分钟
        game_start = now - timedelta(minutes=90)
        game_end = now + timedelta(days=2)
        t0 = game_start + timedelta(minutes=20)  # 密集区起点

        game = CtfGame(
            title=GAME_TITLE,
            description="高频并发 AC → 密集垂直下挫锯齿折线（diff=2.0 / rate=0.2）",
            summary="sawtooth stress",
            start_time=game_start,
            end_time=game_end,
            is_public=True,
            status="ongoing",
            game_type="official",
        )
        db.session.add(game)
        db.session.flush()
        gid = game.id
        print(f"[1] 赛事 id={gid}  title={GAME_TITLE}")

        challenges = []
        for title, cat in CHALLENGE_SPECS:
            ch = CtfChallenge(
                game_id=gid,
                title=title,
                category=cat,
                description=f"sawtooth {title}",
                original_points=1000,
                min_score_rate=0.20,
                difficulty=2.0,
                flag=f"flag{{saw_{uid}_{title.lower()}}}",
                challenge_type=0,
                is_enabled=True,
                disable_blood_bonus=True,
            )
            db.session.add(ch)
            challenges.append(ch)
        db.session.flush()
        print("[2] 题目 5 道: pts=1000 rate=0.2 diff=2.0")
        for ch in challenges:
            print(f"     - {ch.title} id={ch.id}")

        teams, users = [], []
        # 统一密码哈希一次，加速 50 用户创建
        pw_probe = User(
            email=f"saw_probe_{uid}@sim.local",
            username=f"saw_probe_{uid}",
            nickname="probe",
            email_verified=True,
        )
        pw_probe.set_password("SawTooth2025!")
        shared_hash = pw_probe.password_hash

        for i in range(1, TEAM_COUNT + 1):
            u = User(
                email=f"saw_{uid}_u{i:02d}@sim.local",
                username=f"saw_{uid}_u{i:02d}",
                nickname=f"Saw{i:02d}",
                email_verified=True,
                password_hash=shared_hash,
            )
            db.session.add(u)
            db.session.flush()
            t = Team(name=f"Saw-{uid}-{i:02d}", invite_code=uuid.uuid4().hex[:16])
            db.session.add(t)
            db.session.flush()
            u.team_id = t.id
            part = CtfParticipation(game_id=gid, team_id=t.id, status="confirmed")
            db.session.add(part)
            db.session.flush()
            db.session.add(CtfParticipatingUser(
                user_id=u.id, game_id=gid, team_id=t.id, participation_id=part.id,
            ))
            teams.append(t)
            users.append(u)
        db.session.commit()
        print(f"[3] 队伍 {TEAM_COUNT} 支")

        # ── 构造事件：优先热门题全覆盖，再铺满其余队×题 ──
        # 热度权重：题 0,1 全员；2→40；3→35；4→30 → 约 50+50+40+35+30=205 unique
        # 再随机补齐到 250
        coverage = [TEAM_COUNT, TEAM_COUNT, 40, 35, 30]
        events = []  # (team_idx, ch_idx)
        seen = set()
        for ci, n_teams in enumerate(coverage):
            order = list(range(TEAM_COUNT))
            RNG.shuffle(order)
            for ti in order[:n_teams]:
                key = (ti, ci)
                if key in seen:
                    continue
                seen.add(key)
                events.append((ti, ci))

        # 补齐剩余 unique 到 250
        all_pairs = [(ti, ci) for ti in range(TEAM_COUNT) for ci in range(len(challenges))]
        RNG.shuffle(all_pairs)
        for ti, ci in all_pairs:
            if len(events) >= TEAM_COUNT * len(challenges):
                break
            if (ti, ci) in seen:
                continue
            seen.add((ti, ci))
            events.append((ti, ci))

        # 打乱后按「热门优先小幅重排」：前 1/3 事件偏向 HotWeb/HotPwn，制造连挫
        hot = [e for e in events if e[1] <= 1]
        cold = [e for e in events if e[1] > 1]
        RNG.shuffle(hot)
        RNG.shuffle(cold)
        # 交错：hot 密集插入
        merged = []
        hi = ci = 0
        while hi < len(hot) or ci < len(cold):
            # 连续塞 2~4 个热门，再 1 个冷门
            burst = RNG.randint(2, 4)
            for _ in range(burst):
                if hi < len(hot):
                    merged.append(hot[hi])
                    hi += 1
            if ci < len(cold):
                merged.append(cold[ci])
                ci += 1
        while hi < len(hot):
            merged.append(hot[hi])
            hi += 1
        while ci < len(cold):
            merged.append(cold[ci])
            ci += 1
        events = merged

        unique_n = len(events)
        print(f"[4] 计划 unique AC={unique_n}（5×50 理论上限 250）")

        # 时间轴：3~15 秒间隔，塞进 60 分钟
        timestamps = []
        cursor = t0
        window_end = t0 + timedelta(minutes=WINDOW_MINUTES)
        for i in range(len(events)):
            timestamps.append(cursor)
            gap = RNG.randint(INTERVAL_LO, INTERVAL_HI)
            cursor = cursor + timedelta(seconds=gap)
            if cursor > window_end and i < len(events) - 1:
                # 压缩剩余到窗口内：均分剩余秒
                remain = len(events) - i - 1
                left = max(1, int((window_end - timestamps[-1]).total_seconds()))
                step = max(1, left // max(1, remain))
                # 后续用更小间隔
                cursor = timestamps[-1] + timedelta(seconds=min(INTERVAL_HI, max(INTERVAL_LO, step)))

        # 落库 unique AC
        print("[5] 写入 unique 正确提交…")
        batch = []
        for idx, ((ti, ci), ts) in enumerate(zip(events, timestamps)):
            team, user, ch = teams[ti], users[ti], challenges[ci]
            batch.append(CtfChallengeSubmission(
                user_id=user.id,
                team_id=team.id,
                challenge_id=ch.id,
                game_id=gid,
                answer=ch.flag,
                is_correct=True,
                points_earned=0,
                status=0,
                submitted_at=ts,
                correct_dedupe_key=f"saw:{uid}:c{ch.id}:t{team.id}",
            ))
            if len(batch) >= 100:
                db.session.add_all(batch)
                db.session.flush()
                batch = []
        if batch:
            db.session.add_all(batch)
            db.session.flush()
        db.session.commit()
        unique_written = unique_n

        # 填充到 600~800：同题重复 AC（NULL dedupe，不推进状态机，仅抬高行数）
        # Timeline 仍只吃 unique；重复行不改变锯齿，但满足「600~800 条 correct」压测落库量
        pad_target = RNG.randint(TARGET_MIN, TARGET_MAX)
        pad_need = max(0, pad_target - unique_written)
        print(f"[6] 填充重复 correct 行 → 目标总量≈{pad_target}（再写 {pad_need}）…")
        pad_batch = []
        pad_ts = timestamps[-1] if timestamps else t0
        for k in range(pad_need):
            ti = RNG.randint(0, TEAM_COUNT - 1)
            ci = RNG.randint(0, 1)  # 热门题上堆重复提交
            team, user, ch = teams[ti], users[ti], challenges[ci]
            pad_ts = pad_ts + timedelta(seconds=RNG.randint(1, 3))
            # correct_dedupe_key=NULL 允许多条；timeline 会跳过同队同题
            pad_batch.append(CtfChallengeSubmission(
                user_id=user.id,
                team_id=team.id,
                challenge_id=ch.id,
                game_id=gid,
                answer=ch.flag,
                is_correct=True,
                points_earned=0,
                status=0,
                submitted_at=min(pad_ts, window_end),
                correct_dedupe_key=None,
            ))
            if len(pad_batch) >= 150:
                db.session.add_all(pad_batch)
                db.session.flush()
                pad_batch = []
        if pad_batch:
            db.session.add_all(pad_batch)
            db.session.flush()
        db.session.commit()

        total_correct = CtfChallengeSubmission.query.filter_by(
            game_id=gid, is_correct=True,
        ).count()
        print(f"     落库 correct 总计={total_correct}（unique≈{unique_written}）")

        # 全员重算（按题）
        print("[7] recalculate_challenge_scores × 5 …")
        for ch in challenges:
            ScoringService.recalculate_challenge_scores(ch.id)
        db.session.commit()

        # 清缓存并生成 Timeline
        try:
            rs = get_redis()
            if rs and rs.is_available():
                ScoreboardCache.invalidate_scoreboard(rs, gid)
        except Exception:
            pass

        payload = ScoringService.generate_gzctf_style_timeline(gid, top_n=10)
        try:
            rs = get_redis()
            if rs and rs.is_available():
                ScoreboardCache.cache_timeline(rs, gid, payload)
        except Exception:
            pass

        series = payload.get("series") or []
        dips = 0
        max_drop = 0
        for s in series:
            pts = [p["points"] for p in (s.get("data") or [])]
            for i in range(1, len(pts)):
                if pts[i] < pts[i - 1]:
                    dips += 1
                    max_drop = max(max_drop, pts[i - 1] - pts[i])

        # 热门题解题数
        print("[8] 热门题 solvers:")
        for ch in challenges:
            n = ScoringService.count_accepted_solvers(ch.id)
            sc = ScoringService.challenge_base_dynamic_score(ch, n)
            print(f"     {ch.title}: N={n}  dynamic={sc}")

        print("\n[9] Timeline:")
        print(f"     algorithm={payload.get('algorithm')}")
        print(f"     events={payload.get('events')}  dip_events={payload.get('dip_events')}")
        print(f"     top_series_adj_dips={dips}  max_drop=-{max_drop}")
        if series:
            s0 = series[0]
            sample = [p["points"] for p in (s0.get("data") or [])[:16]]
            print(f"     sample[{s0.get('team_name')}]={sample} … n={len(s0.get('data') or [])}")

        print("\n" + "=" * 64)
        print("  RESULT: READY — 请打开前端积分榜查看密集锯齿下挫")
        print("=" * 64)
        print(f"\n>>> 赛事: {GAME_TITLE}")
        print(f">>> 游戏 ID: {gid}")
        print(f">>> 直达: /games/{gid}/scoreboard")
        print(f">>> 或: http://127.0.0.1:5173/games/{gid}/scoreboard\n")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"FATAL: {exc}")
        raise SystemExit(2)
