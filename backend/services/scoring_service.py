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
    def calculate_dynamic_score(
        original_score: int,
        accepted_count: int,
        min_score_rate: float = 0.25,
        difficulty: float = 5.0
    ) -> int:
        """
        计算动态分数
        
        公式：
        若解题数 ≤ 1：分数 = 原始分数
        否则：分数 = ⌊原始分数 × (最小分值率 + (1 - 最小分值率) × e^((1 - 解题数) / 难度))⌋
        
        Args:
            original_score: 原始分值
            accepted_count: 已解题队伍数
            min_score_rate: 最小分值率（默认0.25 = 25%）
            difficulty: 难度系数，越大衰减越慢（默认5）
            
        Returns:
            当前分值
            
        Examples:
            >>> ScoringService.calculate_dynamic_score(1000, 1)
            1000
            >>> ScoringService.calculate_dynamic_score(1000, 5)
            490  # approximately
        """
        if accepted_count <= 1:
            return original_score

        # e^((1 - accepted_count) / difficulty)
        exponent = (1 - accepted_count) / difficulty
        decay = min_score_rate + (1 - min_score_rate) * math.exp(exponent)
        
        return int(original_score * decay)

    @staticmethod
    def calculate_blood_bonus(
        base_score: int,
        blood_bonus_config: int = (50 << 20) | (30 << 10) | 10,
        blood_level: int = 0
    ) -> Tuple[int, float]:
        """
        计算血液奖励
        
        血液奖励格式（64bit）：(一血 << 20) | (二血 << 10) | 三血
        每个值范围：0-1023（千分比）
        默认值：一血5%、二血3%、三血1%
        
        Args:
            base_score: 基础分数
            blood_bonus_config: 血液奖励配置
            blood_level: 血液等级 (0=一血, 1=二血, 2=三血)
            
        Returns:
            (加成后分数, 血液倍数)
            
        Examples:
            >>> ScoringService.calculate_blood_bonus(1000, (50 << 20) | (30 << 10) | 10, 0)
            (1050, 1.05)  # 一血 +5%
        """
        if blood_level > 2:
            return base_score, 1.0

        # 解析血液奖励配置
        first_blood = (blood_bonus_config >> 20) & 0x3FF
        second_blood = (blood_bonus_config >> 10) & 0x3FF
        third_blood = blood_bonus_config & 0x3FF

        blood_values = [first_blood, second_blood, third_blood]
        bonus_rate = blood_values[blood_level] / 1000.0
        multiplier = 1.0 + bonus_rate

        return int(base_score * multiplier), multiplier

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
    def update_scoreboard(
        game_id: int,
        user_id: int,
        team_id: Optional[int] = None
    ) -> None:
        """
        更新排分表
        
        Args:
            game_id: 比赛ID
            user_id: 用户ID
            team_id: 队伍ID
        """
        # 计算该用户在该比赛的总分
        game = CtfGame.query.get(game_id)
        if not game:
            return

        submissions = CtfChallengeSubmission.query.filter_by(
            user_id=user_id,
            is_correct=True
        ).join(CtfChallenge).filter_by(game_id=game_id).all()

        total_points = 0
        solved_count = 0

        for submission in submissions:
            challenge = submission.challenge
            # 获取该题目当前的动态分数
            accepted_count = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge.id,
                is_correct=True
            ).count()

            dynamic_score = ScoringService.calculate_dynamic_score(
                challenge.points,
                accepted_count,
                0.25,  # min_score_rate
                5.0    # difficulty
            )

            total_points += dynamic_score
            solved_count += 1

        # 更新或创建排分记录
        scoreboard = CtfScoreboard.query.filter_by(
            game_id=game_id,
            user_id=user_id,
            team_id=team_id
        ).first()

        if scoreboard:
            scoreboard.total_points = total_points
            scoreboard.solved_challenges = solved_count
            scoreboard.updated_at = datetime.utcnow()
        else:
            scoreboard = CtfScoreboard(
                game_id=game_id,
                user_id=user_id,
                team_id=team_id,
                total_points=total_points,
                solved_challenges=solved_count
            )
            db.session.add(scoreboard)

        last_time = ScoringService.resolve_last_submission_time(game_id, team_id, user_id)
        if last_time:
            scoreboard.last_submission_time = last_time

        db.session.flush()

        try:
            from backend.services.redis_service import get_redis, ScoreboardCache
            rs = get_redis()
            if rs and rs.is_available():
                ScoreboardCache.invalidate_scoreboard(rs, game_id)
        except Exception:
            pass

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
        计算排名
        
        排序规则：
        1. 总分（降序）
        2. 最后一次正确提交时间（升序）
        3. 提交次数（升序）
        """
        scoreboards = CtfScoreboard.query.filter_by(game_id=game_id).all()

        rankings = []
        for sb in scoreboards:
            if sb.user_id:
                user = User.query.get(sb.user_id)
                username = user.username if user else 'Unknown'
                last_submission = CtfChallengeSubmission.query.filter_by(
                    user_id=sb.user_id,
                    is_correct=True,
                ).order_by(CtfChallengeSubmission.submitted_at.desc()).first()
                submission_count = CtfChallengeSubmission.query.filter_by(
                    user_id=sb.user_id,
                ).count()
            else:
                team = Team.query.get(sb.team_id) if sb.team_id else None
                username = team.name if team else f'Team #{sb.team_id}'
                last_submission = CtfChallengeSubmission.query.filter_by(
                    team_id=sb.team_id,
                    is_correct=True,
                ).join(CtfChallenge).filter_by(game_id=game_id).order_by(
                    CtfChallengeSubmission.submitted_at.desc()
                ).first()
                submission_count = CtfChallengeSubmission.query.filter_by(
                    team_id=sb.team_id,
                ).join(CtfChallenge).filter_by(game_id=game_id).count()

            rankings.append({
                'user_id': sb.user_id,
                'username': username,
                'total_points': sb.total_points,
                'solved_challenges': sb.solved_challenges,
                'last_submission_time': last_submission.submitted_at if last_submission else None,
                'submission_count': submission_count,
                'team_id': sb.team_id
            })

        # 按排序规则排序
        rankings.sort(
            key=lambda x: (
                -x['total_points'],  # 降序
                x['last_submission_time'] or datetime.max,  # 升序
                x['submission_count']  # 升序
            )
        )

        # 添加排名
        for rank, item in enumerate(rankings, 1):
            item['rank'] = rank

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
        game = CtfGame.query.get(game_id)
        is_training = game and (
            game.game_type in ("training", "practice") or game.status == "archived"
        )

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



