"""
CTF 核心功能服务
包含：排分系统、Flag检查、血液奖励、动态分数计算
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from enum import IntFlag, IntEnum
import math
from backend.server.extensions import db
from backend.server.db_models import (
    CtfChallenge, CtfChallengeSubmission, CtfScoreboard, CtfSolves,
    CtfGame, CtfParticipation, User, Team
)


class GamePermission(IntFlag):
    """游戏权限标志"""
    JOIN_GAME = 1                  # 加入比赛权限
    RANK_OVERALL = 1 << 1          # 全局排名权限
    REQUIRE_REVIEW = 1 << 2        # 参赛审核权限
    VIEW_CHALLENGE = 1 << 8        # 查看题目权限
    SUBMIT_FLAG = 1 << 9           # 提交Flag权限
    GET_SCORE = 1 << 10            # 获得分值权限
    GET_BLOOD = 1 << 11            # 获得血液奖励权限
    AFFECT_DYNAMIC_SCORE = 1 << 12 # 影响动态分值权限


class ChallengeCType(IntEnum):
    """题目类型
    二进制位标志：
    0b00 = StaticAttachment
    0b01 = StaticContainer
    0b10 = DynamicAttachment
    0b11 = DynamicContainer
    """
    STATIC_ATTACHMENT = 0b00       # 所有队伍相同答案
    STATIC_CONTAINER = 0b01        # 所有队伍共享容器
    DYNAMIC_ATTACHMENT = 0b10      # 动态答案，使用文件
    DYNAMIC_CONTAINER = 0b11       # 每队独立容器和动态答案


class AnswerResult(IntEnum):
    """提交结果"""
    ACCEPTED = 0                   # 正确
    WRONG_ANSWER = 1              # 答案错误
    DUPLICATE = 2                 # 重复提交
    CHEAT_DETECTED = 3            # 检测到作弊


class ScoringService:
    """
    排分系统服务 - 实现动态分数算法和血液奖励
    """

    @staticmethod
    def calculate_ret2shell_score(
        initial: int,
        minimum: int,
        decay: int,
        accepted_count: int,
    ) -> int:
        """
        ret2shell maintain_score 标准公式（余弦插值）：

        - N < 1 → initial
        - N >= decay → minimum
        - 否则：
            ratio = (N - 1) / (decay - 1)
            score = round(minimum + (initial - minimum) * (cos(ratio * π) + 1) / 2)
        """
        initial = int(initial or 0)
        minimum = int(minimum or 0)
        if minimum > initial:
            minimum = initial
        n = int(accepted_count or 0)
        decay = int(decay or 0)
        if decay < 2:
            decay = 2
        if n < 1:
            return initial
        if n >= decay:
            return minimum
        relative_ratio = (n - 1) / (decay - 1)
        cos_theta = math.cos(relative_ratio * math.pi)
        normalized = (cos_theta + 1.0) / 2.0
        score_f = minimum + (initial - minimum) * normalized
        return int(round(score_f))

    @staticmethod
    def calculate_dynamic_score(
        original_score: int,
        accepted_count: int,
        min_score_rate: float = 0.25,
        difficulty: float = 10.0
    ) -> int:
        """
        动态分入口 —— 对齐 ret2shell score_rule：

        - initial = original_score
        - minimum = floor(original_score * min_score_rate)
        - decay   = clamp(round(difficulty), 2..50)
          （本平台 difficulty 字段复用为 ret2shell 的 decay：到达最低分所需解题队数）
        """
        initial = int(original_score or 0)
        try:
            rate = float(min_score_rate)
        except (TypeError, ValueError):
            rate = 0.25
        rate = max(0.0, min(1.0, rate))
        minimum = int(initial * rate)
        try:
            decay = int(round(float(difficulty)))
        except (TypeError, ValueError):
            decay = 10
        decay = max(2, min(50, decay))
        return ScoringService.calculate_ret2shell_score(
            initial, minimum, decay, int(accepted_count or 0),
        )

    @staticmethod
    def calculate_blood_bonus(
        base_score: int,
        blood_bonus_config: int = (50 << 20) | (30 << 10) | 10,
        blood_level: int = 0
    ) -> Tuple[int, float]:
        """
        兼容旧接口：返回「加成后总分」= base + 额外血奖。

        对齐 ret2shell：血奖是基于 initial 的固定额外分（extra），
        不随动态分衰减而缩放；本题动态分全队共享。
        """
        extra, multiplier = ScoringService.calculate_blood_extra(
            base_score, blood_bonus_config=blood_bonus_config, blood_level=blood_level
        )
        return int(base_score) + int(extra), multiplier

    @staticmethod
    def calculate_blood_extra(
        initial_or_base: int,
        blood_bonus_config: int = (50 << 20) | (30 << 10) | 10,
        blood_level: int = 0,
    ) -> Tuple[int, float]:
        """
        ret2shell 血奖：extra = initial * award_rate / 1000（千分比配置）。

        blood_level: 0=一血, 1=二血, 2=三血
        返回 (额外分, 1+rate) —— 额外分不随当前动态分变化。
        """
        if blood_level > 2:
            return 0, 1.0

        first_blood = (blood_bonus_config >> 20) & 0x3FF
        second_blood = (blood_bonus_config >> 10) & 0x3FF
        third_blood = blood_bonus_config & 0x3FF
        blood_values = [first_blood, second_blood, third_blood]
        bonus_rate = blood_values[blood_level] / 1000.0
        extra = int(round(int(initial_or_base or 0) * bonus_rate))
        return extra, 1.0 + bonus_rate

    @staticmethod
    def record_first_solve(
        game_id: int,
        challenge_id: int,
        user_id: int,
        team_id: Optional[int] = None
    ) -> Optional[int]:
        """
        记录首解/二解/三解（调用方须已持有题目行锁）。

        Returns:
            血液等级（0=一血, 1=二血, 2=三血, None=无血）
        """
        from sqlalchemy.exc import IntegrityError

        # 同队/同人已拿过该题血则不再记
        dup_q = CtfSolves.query.filter_by(challenge_id=challenge_id)
        if team_id:
            if dup_q.filter_by(team_id=team_id).first():
                return None
        elif dup_q.filter_by(user_id=user_id).first():
            return None

        existing_solves = (
            CtfSolves.query.filter_by(challenge_id=challenge_id)
            .with_for_update()
            .count()
        )
        if existing_solves >= 3:
            return None

        for blood_level in range(existing_solves, 3):
            try:
                with db.session.begin_nested():
                    db.session.add(CtfSolves(
                        game_id=game_id,
                        challenge_id=challenge_id,
                        user_id=user_id,
                        team_id=team_id,
                        blood_level=blood_level,
                        solved_at=datetime.utcnow(),
                    ))
                    db.session.flush()
                return blood_level
            except IntegrityError:
                continue
        return None

    @staticmethod
    def count_accepted_solvers(challenge_id: int) -> int:
        """已解唯一队伍数（无 team_id 时回退到唯一用户数）。"""
        from sqlalchemy import func

        team_cnt = db.session.query(
            func.count(func.distinct(CtfChallengeSubmission.team_id))
        ).filter(
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.is_correct.is_(True),
            CtfChallengeSubmission.team_id.isnot(None),
        ).scalar()
        team_cnt = int(team_cnt or 0)
        if team_cnt > 0:
            return team_cnt

        user_cnt = db.session.query(
            func.count(func.distinct(CtfChallengeSubmission.user_id))
        ).filter(
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.is_correct.is_(True),
        ).scalar()
        return int(user_cnt or 0)

    @staticmethod
    def challenge_base_dynamic_score(
        challenge: CtfChallenge,
        accepted_count: Optional[int] = None,
    ) -> int:
        """按题目自身 original_points / min_score_rate / difficulty 计算当前基础动态分。"""
        if accepted_count is None:
            accepted_count = ScoringService.count_accepted_solvers(challenge.id)
        original = int(
            getattr(challenge, "original_points", None)
            or getattr(challenge, "points", None)
            or 0
        )
        # 仅在字段缺失时回落默认；禁止覆盖管理员已写入的真实配置
        min_rate = getattr(challenge, "min_score_rate", None)
        if min_rate is None:
            min_rate = 0.25
        else:
            min_rate = float(min_rate)
        difficulty = getattr(challenge, "difficulty", None)
        if difficulty is None:
            difficulty = 10.0
        else:
            difficulty = float(difficulty)
        if difficulty <= 0:
            difficulty = 0.1  # 防止除零；极小值 = 极快衰减
        return ScoringService.calculate_dynamic_score(
            original,
            int(accepted_count),
            float(min_rate),
            float(difficulty),
        )

    @staticmethod
    def score_with_blood_for_solver(
        challenge: CtfChallenge,
        accepted_count: int,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """
        ret2shell 计分：本题当前动态分（全队共享）+ 固定血奖额外分。

        血奖基于 original_points（initial），不随衰减缩小 —— 与 ret2shell extra 表一致。
        """
        base = ScoringService.challenge_base_dynamic_score(challenge, accepted_count)
        if getattr(challenge, "disable_blood_bonus", False):
            return base
        q = CtfSolves.query.filter_by(challenge_id=challenge.id)
        blood = None
        if team_id:
            blood = q.filter_by(team_id=team_id).first()
        elif user_id:
            blood = q.filter_by(user_id=user_id).first()
        if blood is None:
            return base
        initial = int(getattr(challenge, "original_points", None) or base or 0)
        extra, _ = ScoringService.calculate_blood_extra(
            initial, blood_level=int(blood.blood_level or 0)
        )
        return int(base) + int(extra)

    @staticmethod
    def recalculate_challenge_scores(challenge_id: int) -> int:
        """
        题目被解出后：按最新 accepted_count 回写所有已解提交的 points_earned，
        并刷新所有受影响队伍的 CtfScoreboard。
        Returns: 当前基础动态分（不含血奖励）
        """
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return 0

        accepted = ScoringService.count_accepted_solvers(challenge_id)
        base = ScoringService.challenge_base_dynamic_score(challenge, accepted)

        submissions = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id,
            is_correct=True,
        ).all()

        # 预加载血榜，避免 score_with_blood_for_solver 的 N+1
        blood_by_team: Dict[int, int] = {}
        blood_by_user: Dict[int, int] = {}
        if not getattr(challenge, "disable_blood_bonus", False):
            for b in CtfSolves.query.filter_by(challenge_id=challenge_id).all():
                if b.blood_level is None:
                    continue
                level = int(b.blood_level)
                if b.team_id is not None:
                    blood_by_team[int(b.team_id)] = level
                elif b.user_id is not None:
                    blood_by_user[int(b.user_id)] = level

        initial = int(getattr(challenge, "original_points", None) or base or 0)
        affected: List[Tuple[int, int, Optional[int]]] = []
        seen_keys = set()
        for sub in submissions:
            pts = int(base)
            if not getattr(challenge, "disable_blood_bonus", False):
                level = None
                if sub.team_id is not None:
                    level = blood_by_team.get(int(sub.team_id))
                elif sub.user_id is not None:
                    level = blood_by_user.get(int(sub.user_id))
                if level is not None:
                    extra, _ = ScoringService.calculate_blood_extra(initial, blood_level=level)
                    pts = int(base) + int(extra)
            sub.points_earned = pts
            key = (challenge.game_id, sub.team_id or 0, sub.user_id or 0)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            affected.append((challenge.game_id, sub.user_id, sub.team_id))

        db.session.flush()

        refreshed = set()
        for game_id, user_id, team_id in affected:
            rk = (game_id, team_id if team_id else user_id)
            if rk in refreshed:
                continue
            refreshed.add(rk)
            ScoringService.update_scoreboard(game_id, user_id, team_id)

        return base

    @staticmethod
    def update_scoreboard(
        game_id: int,
        user_id: int,
        team_id: Optional[int] = None
    ) -> None:
        """
        更新排分表：按队（或用户）已解题目汇总当前 points_earned（含衰减与血）。
        使用 Redis 队锁 + DB FOR UPDATE，防止同队并发解两题时丢分覆盖。
        缓存失效交给 after_commit hooks（按 game_id），勿在事务内提前 invalidate。
        """
        from backend.services.submit_lock import redis_scoreboard_lock

        game = CtfGame.query.get(game_id)
        if not game:
            return

        from sqlalchemy.exc import IntegrityError

        owner = f"t{team_id}" if team_id else f"u{user_id}"
        with redis_scoreboard_lock(game_id, owner):
            q = (
                CtfChallengeSubmission.query.filter_by(is_correct=True)
                .join(CtfChallenge)
                .filter(CtfChallenge.game_id == game_id)
            )
            if team_id:
                q = q.filter(CtfChallengeSubmission.team_id == team_id)
            else:
                q = q.filter(CtfChallengeSubmission.user_id == user_id)

            submissions = q.order_by(CtfChallengeSubmission.submitted_at.asc()).all()

            # 同题只计一次（取该队/用户该题最新正确提交的 points_earned）
            by_challenge: Dict[int, int] = {}
            for sub in submissions:
                by_challenge[sub.challenge_id] = int(sub.points_earned or 0)

            total_points = sum(by_challenge.values())
            solved_count = len(by_challenge)

            def _load_sb():
                if team_id:
                    return (
                        CtfScoreboard.query.filter_by(game_id=game_id, team_id=team_id)
                        .with_for_update()
                        .first()
                    )
                return (
                    CtfScoreboard.query.filter_by(game_id=game_id, user_id=user_id)
                    .with_for_update()
                    .first()
                )

            def _apply(sb):
                sb.total_points = total_points
                sb.solved_challenges = solved_count
                sb.user_id = user_id or sb.user_id
                sb.team_id = team_id if team_id is not None else sb.team_id
                sb.updated_at = datetime.utcnow()
                last_time = ScoringService.resolve_last_submission_time(game_id, team_id, user_id)
                if last_time:
                    sb.last_submission_time = last_time

            scoreboard = _load_sb()
            try:
                # SAVEPOINT：唯一约束冲突时不毁掉外层提交事务
                with db.session.begin_nested():
                    if scoreboard:
                        _apply(scoreboard)
                    else:
                        scoreboard = CtfScoreboard(
                            game_id=game_id,
                            user_id=user_id,
                            team_id=team_id,
                            total_points=total_points,
                            solved_challenges=solved_count,
                        )
                        db.session.add(scoreboard)
                        _apply(scoreboard)
                    db.session.flush()
            except IntegrityError:
                scoreboard = _load_sb()
                if not scoreboard:
                    raise
                _apply(scoreboard)
                db.session.flush()

    @staticmethod
    def generate_gzctf_style_timeline(game_id: int, top_n: int = 10) -> Dict:
        """
        全场快照重演（aa26239 满意版）+ 固定血奖 extra。

        每个正确提交事件 T：
          1) 统计截至 T 每题唯一解题队数 N
          2) 余弦动态分 Score_dyn(c,T)
          3) 若该队该题有血：+ fixed_blood_extra(initial, blood_level)
          4) TotalScore_team,T = Σ (Score_dyn + extra)（允许相对 T-1 下挫）

        与昨天 18:08 版相同：每事件对全场已上场队伍重算绝对总分并写点。
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

        # 题×队 → blood_level（0/1/2）；血奖基于 initial，不随衰减缩小
        blood_by_pair: Dict[Tuple[int, int], int] = {}
        for b in CtfSolves.query.filter_by(game_id=game_id).all():
            if b.team_id is None or b.blood_level is None:
                continue
            if int(b.blood_level) > 2:
                continue
            blood_by_pair[(int(b.challenge_id), int(b.team_id))] = int(b.blood_level)

        team_ids = {sb.team_id for sb in CtfScoreboard.query.filter_by(game_id=game_id).all() if sb.team_id}
        team_ids.update(r.team_id for r in rows if r.team_id)
        team_names: Dict[int, str] = {}
        if team_ids:
            for t in Team.query.filter(Team.id.in_(team_ids)).all():
                team_names[t.id] = t.name
            for tid in team_ids:
                team_names.setdefault(tid, f"Team #{tid}")

        solve_counts: Dict[int, int] = {cid: 0 for cid in challenges}
        team_solved: Dict[int, set] = defaultdict(set)
        # timeline_data[team_id] = [[iso, score], ...]
        timeline_data: Dict[int, List] = defaultdict(list)
        prev_score: Dict[int, int] = {}
        current_dyn: Dict[int, int] = {}
        event_count = 0
        dip_events = 0

        def challenge_dyn_score(cid: int, count: int) -> int:
            """共享余弦动态分（与 challenge_base_dynamic_score 一致）。"""
            ch = challenges.get(cid)
            if not ch or count <= 0:
                return 0
            return ScoringService.challenge_base_dynamic_score(ch, count)

        def blood_extra_for(team_id: int, solved_cid: int) -> int:
            ch = challenges.get(solved_cid)
            if not ch or getattr(ch, "disable_blood_bonus", False):
                return 0
            level = blood_by_pair.get((solved_cid, team_id))
            if level is None:
                return 0
            initial = int(getattr(ch, "original_points", None) or 0)
            extra, _ = ScoringService.calculate_blood_extra(initial, blood_level=level)
            return int(extra)

        def append_point(team_id: int, timestamp: Optional[str], total_score: int) -> None:
            nonlocal dip_events
            prev = prev_score.get(team_id)
            if prev is not None and total_score < prev:
                dip_events += 1
            hist = timeline_data[team_id]
            if hist and hist[-1][0] == timestamp and hist[-1][1] == total_score:
                prev_score[team_id] = int(total_score)
                return
            hist.append([timestamp, int(total_score)])
            prev_score[team_id] = int(total_score)

        # 预去重：只保留每队每题最早 AC，减少全表扫描后的空转
        deduped_rows = []
        seen_ac = set()
        for sub in rows:
            tid = sub.team_id
            cid = sub.challenge_id
            if not tid or cid not in challenges:
                continue
            key = (int(tid), int(cid))
            if key in seen_ac:
                continue
            seen_ac.add(key)
            deduped_rows.append(sub)

        for sub in deduped_rows:
            tid = int(sub.team_id)
            cid = int(sub.challenge_id)
            team_names.setdefault(tid, f"Team #{tid}")

            # 增量重演：仅更新受本题动态分变化影响的队伍，避免 O(事件×队伍×已解)
            already = {t for t, solved in team_solved.items() if cid in solved}
            old_val = int(current_dyn.get(cid, 0))
            team_solved[tid].add(cid)
            solve_counts[cid] = len(already) + 1
            new_val = int(challenge_dyn_score(cid, solve_counts[cid]))
            current_dyn[cid] = new_val
            delta = new_val - old_val
            event_count += 1
            timestamp = sub.submitted_at.isoformat() if sub.submitted_at else None

            for other_tid in already:
                total_score = int(prev_score.get(other_tid, 0)) + delta
                append_point(other_tid, timestamp, total_score)

            solver_total = (
                int(prev_score.get(tid, 0)) + new_val + blood_extra_for(tid, cid)
            )
            append_point(tid, timestamp, solver_total)

        # TopN：按重演峰值优先（露出早解断崖），终局分次之
        peak_score = {
            tid: max((p[1] for p in pts), default=0)
            for tid, pts in timeline_data.items()
        }
        ranked = sorted(
            prev_score.items(),
            key=lambda x: (-peak_score.get(x[0], 0), -x[1], x[0]),
        )[: max(1, int(top_n))]
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
                "difficulty": float(c.difficulty if c.difficulty is not None else 10.0),
            }
            for c in challenges.values()
        ]
        teams_payload = [
            {"id": tid, "name": team_names.get(tid, f"Team #{tid}")}
            for tid in sorted(team_names.keys())
        ]

        timeline_map = {str(tid): pts for tid, pts in timeline_data.items()}

        game = CtfGame.query.get(game_id)
        return {
            "series": series,
            "timeline_data": timeline_map,
            "teams": teams_payload,
            "team_count": len(team_solved),
            "challenges": challenges_payload,
            "submissions": submissions_payload,
            "game_start": game.start_time.isoformat() if game and game.start_time else None,
            "game_end": game.end_time.isoformat() if game and game.end_time else None,
            "algorithm": "ret2shell_snapshot_replay",
            "events": event_count,
            "dip_events": dip_events,
            "score_formula": "ret2shell_cosine+fixed_blood_extra",
        }

    @staticmethod
    def build_decay_timeline(game_id: int, top_n: int = 10) -> Dict:
        """兼容别名 → Snapshot Replay。"""
        return ScoringService.generate_gzctf_style_timeline(game_id, top_n=top_n)

    @staticmethod
    def get_timeline_cached(game_id: int, top_n: int = 10) -> Dict:
        """ScoreboardCacheHandler：优先读 Redis Timeline 快照。"""
        try:
            from backend.services.redis_service import get_redis, ScoreboardCache
            rs = get_redis()
            if rs and rs.is_available():
                cached = ScoreboardCache.get_cached_timeline(rs, game_id)
                if (
                    cached
                    and isinstance(cached, dict)
                    and cached.get("series") is not None
                    and cached.get("algorithm") == "ret2shell_snapshot_replay"
                    and cached.get("score_formula") == "ret2shell_cosine+fixed_blood_extra"
                ):
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

    @staticmethod
    def resolve_last_submission_time(
        game_id: int,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Optional[datetime]:
        """获取队伍/用户在该赛事最后一次正确提交时间"""
        query = (
            CtfChallengeSubmission.query.filter_by(is_correct=True)
            .join(CtfChallenge)
            .filter(CtfChallenge.game_id == game_id)
        )
        if team_id:
            query = query.filter(CtfChallengeSubmission.team_id == team_id)
        elif user_id:
            query = query.filter(CtfChallengeSubmission.user_id == user_id)
        else:
            return None
        last = query.order_by(CtfChallengeSubmission.submitted_at.desc()).first()
        return last.submitted_at if last else None

    @staticmethod
    def get_team_rank(game_id: int, team_id: int) -> Optional[int]:
        """按当前积分榜计算队伍排名（只读，不写库）"""
        scoreboards = CtfScoreboard.query.filter_by(game_id=game_id).order_by(
            CtfScoreboard.total_points.desc(),
            CtfScoreboard.last_submission_time.asc(),
        ).all()
        for idx, sb in enumerate(scoreboards, 1):
            if sb.team_id == team_id:
                return idx
        return None

    @staticmethod
    def calculate_rankings(game_id: int) -> List[Dict]:
        """
        计算排名（批量查询，避免 N+1）

        排序规则：
        1. 总分（降序）
        2. 最后一次正确提交时间（升序）
        3. 提交次数（升序）
        """
        from sqlalchemy import func

        scoreboards = CtfScoreboard.query.filter_by(game_id=game_id).all()
        if not scoreboards:
            return []

        user_ids = {sb.user_id for sb in scoreboards if sb.user_id}
        team_ids = {sb.team_id for sb in scoreboards if sb.team_id}

        users = {
            u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()
        } if user_ids else {}
        teams = {
            t.id: t for t in Team.query.filter(Team.id.in_(team_ids)).all()
        } if team_ids else {}

        # 正确提交：最后时间 + 总提交次数 批量聚合
        last_correct_by_team = {}
        last_correct_by_user = {}
        count_by_team = {}
        count_by_user = {}

        if team_ids:
            last_rows = (
                db.session.query(
                    CtfChallengeSubmission.team_id,
                    func.max(CtfChallengeSubmission.submitted_at),
                )
                .filter(
                    CtfChallengeSubmission.game_id == game_id,
                    CtfChallengeSubmission.is_correct.is_(True),
                    CtfChallengeSubmission.team_id.in_(team_ids),
                )
                .group_by(CtfChallengeSubmission.team_id)
                .all()
            )
            last_correct_by_team = {tid: ts for tid, ts in last_rows if tid}

            cnt_rows = (
                db.session.query(
                    CtfChallengeSubmission.team_id,
                    func.count(CtfChallengeSubmission.id),
                )
                .filter(
                    CtfChallengeSubmission.game_id == game_id,
                    CtfChallengeSubmission.team_id.in_(team_ids),
                )
                .group_by(CtfChallengeSubmission.team_id)
                .all()
            )
            count_by_team = {tid: int(n or 0) for tid, n in cnt_rows if tid}

        if user_ids:
            last_rows = (
                db.session.query(
                    CtfChallengeSubmission.user_id,
                    func.max(CtfChallengeSubmission.submitted_at),
                )
                .filter(
                    CtfChallengeSubmission.game_id == game_id,
                    CtfChallengeSubmission.is_correct.is_(True),
                    CtfChallengeSubmission.user_id.in_(user_ids),
                )
                .group_by(CtfChallengeSubmission.user_id)
                .all()
            )
            last_correct_by_user = {uid: ts for uid, ts in last_rows if uid}

            cnt_rows = (
                db.session.query(
                    CtfChallengeSubmission.user_id,
                    func.count(CtfChallengeSubmission.id),
                )
                .filter(
                    CtfChallengeSubmission.game_id == game_id,
                    CtfChallengeSubmission.user_id.in_(user_ids),
                )
                .group_by(CtfChallengeSubmission.user_id)
                .all()
            )
            count_by_user = {uid: int(n or 0) for uid, n in cnt_rows if uid}

        rankings = []
        for sb in scoreboards:
            if sb.user_id:
                user = users.get(sb.user_id)
                username = user.username if user else 'Unknown'
                last_submission = last_correct_by_user.get(sb.user_id) or sb.last_submission_time
                submission_count = count_by_user.get(sb.user_id, 0)
            else:
                team = teams.get(sb.team_id) if sb.team_id else None
                username = team.name if team else f'Team #{sb.team_id}'
                last_submission = (
                    last_correct_by_team.get(sb.team_id)
                    or sb.last_submission_time
                )
                submission_count = count_by_team.get(sb.team_id, 0) if sb.team_id else 0

            rankings.append({
                'user_id': sb.user_id,
                'username': username,
                'total_points': sb.total_points,
                'solved_challenges': sb.solved_challenges,
                'last_submission_time': last_submission,
                'submission_count': submission_count,
                'team_id': sb.team_id
            })

        rankings.sort(
            key=lambda x: (
                -(x['total_points'] or 0),
                x['last_submission_time'] or datetime.max,
                x['submission_count'] or 0,
            )
        )
        for idx, row in enumerate(rankings, 1):
            row['rank'] = idx
            if row['last_submission_time'] and hasattr(row['last_submission_time'], 'isoformat'):
                row['last_submission_time'] = row['last_submission_time'].isoformat()
        return rankings


class CheatDetectionService:
    """
    作弊检测服务
    """

    @staticmethod
    def detect_similar_flags(
        submitted_flag: str,
        challenge_id: int,
        current_user_id: int,
        similarity_threshold: float = 0.9
    ) -> List[Tuple[int, float]]:
        """
        检测相似Flag（作弊检测）
        
        Returns:
            [(user_id, 相似度), ...]
        """
        # 获取其他用户提交的答案
        other_submissions = CtfChallengeSubmission.query.filter(
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.user_id != current_user_id,
            CtfChallengeSubmission.is_correct == True
        ).all()

        similar_users = []
        for submission in other_submissions:
            similarity = CheatDetectionService._calculate_similarity(
                submitted_flag,
                submission.answer
            )
            if similarity >= similarity_threshold:
                similar_users.append((submission.user_id, similarity))

        return similar_users

    @staticmethod
    def _calculate_similarity(s1: str, s2: str) -> float:
        """计算字符串相似度（简单实现）"""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # Levenshtein 距离
        len1, len2 = len(s1), len(s2)
        if len1 < len2:
            return CheatDetectionService._calculate_similarity(s2, s1)

        if len2 == 0:
            return 0.0

        prev_row = list(range(len2 + 1))
        for i in range(1, len1 + 1):
            curr_row = [i] + [0] * len2
            for j in range(1, len2 + 1):
                insertions = prev_row[j] + 1
                deletions = curr_row[j - 1] + 1
                substitutions = prev_row[j - 1] + (s1[i - 1] != s2[j - 1])
                curr_row[j] = min(insertions, deletions, substitutions)
            prev_row = curr_row

        # 相似度 = 1 - (距离 / 最大长度)
        return 1.0 - (prev_row[-1] / len1)


class FlagTemplateService:
    """
    动态Flag生成服务
    """

    @staticmethod
    def generate_flag(
        template: str,
        challenge_id: int,
        user_id: int,
        game_id: int,
        custom_token: Optional[str] = None
    ) -> str:
        """
        从模板生成动态Flag
        
        模板变量：
        {token} - 参赛凭证/团队令牌
        {challenge} - 题目ID
        {user} - 用户ID
        {game} - 比赛ID
        
        Example:
            template = "flag{token_challenge_user}"
            → "flag{abc123_42_18}"
        """
        from hashlib import md5

        if not template:
            return ""

        # 生成或使用提供的token
        if not custom_token:
            token_source = f"{challenge_id}_{user_id}_{game_id}"
            custom_token = md5(token_source.encode()).hexdigest()[:16]

        substitutions = {
            '{token}': custom_token,
            '{challenge}': str(challenge_id),
            '{user}': str(user_id),
            '{game}': str(game_id)
        }

        flag = template
        for placeholder, value in substitutions.items():
            flag = flag.replace(placeholder, value)

        return flag


class PermissionService:
    """
    CTF 权限管理服务
    """

    @staticmethod
    def check_game_permission(user_id: int, game_id: int, permission: int) -> bool:
        """检查用户对游戏的权限"""
        from backend.server.db_models import CtfParticipatingUser

        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            uid = user_id

        user = User.query.get(uid)
        if user and user.is_admin:
            return True

        from backend.server.db_models import CtfGame

        game = CtfGame.query.get(game_id)
        if game and (
            game.game_type in ("training", "practice") or game.status == "archived"
        ):
            user_participation = CtfParticipatingUser.query.filter_by(
                user_id=uid,
                game_id=game_id
            ).first()
            return user_participation is not None

        user_participation = CtfParticipatingUser.query.filter_by(
            user_id=uid,
            game_id=game_id
        ).first()

        if not user_participation:
            return False

        role_permissions = {
            'admin': 0xFFFFFFFF,
            'manager': GamePermission.VIEW_CHALLENGE | GamePermission.SUBMIT_FLAG,
            'player': GamePermission.VIEW_CHALLENGE | GamePermission.SUBMIT_FLAG | GamePermission.GET_SCORE
        }

        user_permissions = role_permissions.get('player', 0)
        return (user_permissions & permission) != 0

    @staticmethod
    def has_submission_permission(user_id: int, game_id: int, challenge_id: int) -> bool:
        """检查是否可以提交"""
        if not PermissionService.check_game_permission(user_id, game_id, GamePermission.SUBMIT_FLAG):
            return False
            
        from backend.server.db_models import CtfChallenge
        
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge or not challenge.is_enabled:
            return False

        from backend.server.db_models import CtfGame
        from backend.server.time_utils import game_has_started, sync_game_status_if_due
        from backend.server.extensions import db

        game = CtfGame.query.get(game_id)
        if game and sync_game_status_if_due(game):
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        is_training = game and (
            game.game_type in ("training", "practice") or game.status == "archived"
        )

        if not is_training and game and not game_has_started(game):
            return False

        # 训练场无截止时间限制
        if not is_training and challenge.deadline and datetime.utcnow() > challenge.deadline:
            return False
            
        return True

    @staticmethod
    def has_container_permission(user_id: int, game_id: int, challenge_id: int) -> bool:
        """检查是否可以启动容器"""
        return PermissionService.has_submission_permission(user_id, game_id, challenge_id)


class FlagValidationService:
    """
    Flag 验证服务 - 支持多种验证方式
    """

    @staticmethod
    def validate_flag(
        submitted_flag: str,
        challenge_id: int,
        user_id: int,
        game_id: int
    ) -> Tuple[bool, int]:
        """
        验证 Flag
        
        Returns:
            (是否正确, 状态码)
            状态码：0=正确, 1=错误, 2=重复, 3=作弊
        """
        from backend.server.db_models import CtfChallenge, CtfChallengeSubmission, CtfGameInstance, User
        
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return False, 1

        user = User.query.get(user_id)

        # 检查是否重复提交（团队模式下按队伍去重）
        duplicate_query = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id,
            is_correct=True,
        )
        if user and user.team_id:
            existing = duplicate_query.filter_by(team_id=user.team_id).first()
        else:
            existing = duplicate_query.filter_by(user_id=user_id).first()
        
        if existing:
            return False, 2  # DUPLICATE
        
        # 验证答案
        instance_query = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            is_running=True
        )
        if user and user.team_id:
            instance = instance_query.filter_by(team_id=user.team_id).first()
        else:
            instance = instance_query.filter_by(user_id=user_id).first()

        from backend.services.flag_generator import resolve_challenge_expected_flag

        expected = resolve_challenge_expected_flag(
            challenge, user, user_id, running_instance=instance,
        )
        correct = bool(expected) and submitted_flag.strip() == expected.strip()

        if not correct:
            return False, 1  # WRONG_ANSWER
        
        # 检测作弊
        similar_users = CheatDetectionService.detect_similar_flags(
            submitted_flag,
            challenge_id,
            user_id,
            0.85  # 相似度阈值
        )
        
        if similar_users:
            return True, 3  # CHEAT_DETECTED（但仍然正确）
        
        return True, 0  # ACCEPTED

    @staticmethod
    def _check_flag(submitted: str, challenge) -> bool:
        """检查提交的flag是否正确"""
        if not challenge.flag:
            return False
            
        # 精确匹配
        if submitted.strip() == challenge.flag.strip():
            return True
        
        # 如果有flag模板，尝试动态验证
        if challenge.flag_template:
            # 简单检查：如果submission包含challenge flag作为子串
            return False
        
        return False



