"""
作弊检测服务
包含：IP 检测、提交行为分析、重复答案检测、异常模式识别
"""

import logging
import hashlib
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from backend.server.extensions import db
from backend.server.db_models import (
    CtfChallengeSubmission, CtfCheatInfo, User, Team, CtfChallenge, CtfGame
)
from collections import defaultdict

logger = logging.getLogger(__name__)


class CheatDetectionService:
    """作弊检测服务"""
    
    # 可配置的检测阈值
    IP_SUSPICION_THRESHOLD = 0.7  # IP 相似度阈值
    SUBMISSION_TIME_THRESHOLD = 60  # 秒，提交时间间隔
    SIMILARITY_THRESHOLD = 0.9  # 答案相似度阈值
    RAPID_SUBMISSION_COUNT = 5  # 快速提交次数
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度（Levenshtein 距离）
        
        Args:
            str1: 字符串1
            str2: 字符串2
        
        Returns:
            相似度 (0-1)
        """
        
        if not str1 or not str2:
            return 0.0
        
        # 如果长度差异过大，相似度很低
        len_diff = abs(len(str1) - len(str2))
        max_len = max(len(str1), len(str2))
        if len_diff / max_len > 0.5:
            return 0.0
        
        # 使用编辑距离计算相似度
        distance = CheatDetectionService._levenshtein_distance(str1, str2)
        similarity = 1 - (distance / max_len)
        
        return max(0.0, min(1.0, similarity))
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return CheatDetectionService._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def detect_duplicate_submission(
        user_id: int,
        challenge_id: int,
        game_id: int,
        answer: str
    ) -> Tuple[bool, Optional[str]]:
        """
        检测是否为重复提交
        
        Args:
            user_id: 用户 ID
            challenge_id: 题目 ID
            game_id: 比赛 ID
            answer: 提交的答案
        
        Returns:
            (是否为重复提交, 原始提交时间)
        """
        
        # 查询用户在该题目的已提交记录
        existing = CtfChallengeSubmission.query.filter(
            CtfChallengeSubmission.user_id == user_id,
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.game_id == game_id,
            CtfChallengeSubmission.is_correct == True
        ).first()
        
        if existing:
            return True, existing.submitted_at.isoformat() if existing.submitted_at else None
        
        return False, None
    
    @staticmethod
    def detect_similar_submission(
        user_id: int,
        challenge_id: int,
        game_id: int,
        answer: str,
        time_window_minutes: int = 30
    ) -> List[Dict]:
        """
        检测相似答案（可能的作弊）
        
        Args:
            user_id: 用户 ID
            challenge_id: 题目 ID
            game_id: 比赛 ID
            answer: 提交的答案
            time_window_minutes: 时间窗口（分钟）
        
        Returns:
            相似提交列表
        """
        
        # 查询时间窗口内的所有提交
        time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        similar_submissions = CtfChallengeSubmission.query.join(
            CtfChallenge
        ).filter(
            CtfChallenge.id == challenge_id,
            CtfChallenge.game_id == game_id,
            CtfChallengeSubmission.submitted_at >= time_threshold,
            CtfChallengeSubmission.is_correct == True,
            CtfChallengeSubmission.user_id != user_id
        ).all()
        
        suspicions = []
        for submission in similar_submissions:
            similarity = CheatDetectionService.calculate_similarity(
                answer,
                submission.answer
            )
            
            if similarity > CheatDetectionService.SIMILARITY_THRESHOLD:
                suspicions.append({
                    'submission_id': submission.id,
                    'user_id': submission.user_id,
                    'team_id': submission.team_id,
                    'answer': submission.answer[:50] + '...' if len(submission.answer) > 50 else submission.answer,
                    'similarity': round(similarity, 3),
                    'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                    'time_diff_seconds': int((datetime.utcnow() - submission.submitted_at).total_seconds())
                })
        
        # 按相似度排序
        suspicions.sort(key=lambda x: x['similarity'], reverse=True)
        
        return suspicions
    
    @staticmethod
    def detect_rapid_submission(
        user_id: int,
        challenge_id: int,
        game_id: int,
        time_window_seconds: int = 30
    ) -> Tuple[bool, Dict]:
        """
        检测快速提交（可能的脚本自动化）
        
        Args:
            user_id: 用户 ID
            challenge_id: 题目 ID
            game_id: 比赛 ID
            time_window_seconds: 时间窗口（秒）
        
        Returns:
            (是否为快速提交, 统计信息)
        """
        
        time_threshold = datetime.utcnow() - timedelta(seconds=time_window_seconds)
        
        submissions = CtfChallengeSubmission.query.filter(
            CtfChallengeSubmission.user_id == user_id,
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.game_id == game_id,
            CtfChallengeSubmission.submitted_at >= time_threshold
        ).order_by(CtfChallengeSubmission.submitted_at).all()
        
        if len(submissions) < CheatDetectionService.RAPID_SUBMISSION_COUNT:
            return False, {'count': len(submissions), 'threshold': CheatDetectionService.RAPID_SUBMISSION_COUNT}
        
        # 计算提交间隔
        intervals = []
        for i in range(1, len(submissions)):
            delta = (submissions[i].submitted_at - submissions[i-1].submitted_at).total_seconds()
            intervals.append(delta)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        is_rapid = avg_interval < CheatDetectionService.SUBMISSION_TIME_THRESHOLD
        
        return is_rapid, {
            'count': len(submissions),
            'avg_interval': round(avg_interval, 2),
            'min_interval': round(min(intervals), 2) if intervals else 0,
            'threshold': CheatDetectionService.SUBMISSION_TIME_THRESHOLD
        }
    
    @staticmethod
    def detect_ip_pattern(
        user_id: int,
        current_ip: str,
        game_id: int,
        time_window_hours: int = 24
    ) -> Tuple[bool, Dict]:
        """
        检测 IP 异常（同一用户从多个 IP 快速登录或提交）
        
        Args:
            user_id: 用户 ID
            current_ip: 当前 IP
            game_id: 比赛 ID
            time_window_hours: 时间窗口（小时）
        
        Returns:
            (是否为异常 IP, 统计信息)
        """
        
        # 注意：实际应用中需要在提交时记录 IP 地址
        # 这里仅展示检测逻辑框架
        
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # 从审计日志或提交记录中获取 IP 信息
        # 这里使用伪代码表示
        ips_in_window = set()
        
        # 示例实现
        activity_logs = []  # 应该从数据库获取
        
        for log in activity_logs:
            if hasattr(log, 'ip_address') and log.ip_address:
                ips_in_window.add(log.ip_address)
        
        if len(ips_in_window) > 1:
            return True, {
                'ip_count': len(ips_in_window),
                'current_ip': current_ip,
                'previous_ips': list(ips_in_window)
            }
        
        return False, {'ip_count': len(ips_in_window), 'current_ip': current_ip}
    
    @staticmethod
    def create_cheat_record(
        game_id: int,
        submission_id: int,
        source_user_id: int,
        target_user_id: int,
        similarity: float
    ) -> CtfCheatInfo:
        """
        创建作弊记录
        
        Args:
            game_id: 比赛 ID
            submission_id: 提交 ID
            source_user_id: 源用户 ID（被怀疑的)
            target_user_id: 目标用户 ID（参考用户）
            similarity: 相似度
        
        Returns:
            CtfCheatInfo 对象
        """
        
        cheat_info = CtfCheatInfo(
            game_id=game_id,
            submission_id=submission_id,
            source_user_id=source_user_id,
            target_user_id=target_user_id,
            similarity=similarity,
            detection_time=datetime.utcnow()
        )
        
        db.session.add(cheat_info)
        db.session.commit()
        
        logger.warning(
            f"Cheat detected: user {source_user_id} vs {target_user_id}, "
            f"similarity: {similarity:.2%}, submission_id: {submission_id}"
        )
        
        return cheat_info
    
    @staticmethod
    def get_cheat_report(game_id: int) -> Dict:
        """
        生成作弊检测报告
        
        Args:
            game_id: 比赛 ID
        
        Returns:
            作弊报告
        """
        
        cheats = CtfCheatInfo.query.filter_by(game_id=game_id).all()
        
        user_cheat_count = defaultdict(int)
        total_similarity = defaultdict(float)
        
        for cheat in cheats:
            user_cheat_count[cheat.source_user_id] += 1
            total_similarity[cheat.source_user_id] += cheat.similarity
        
        # 计算平均相似度
        avg_similarity = {}
        for user_id in user_cheat_count:
            avg_similarity[user_id] = total_similarity[user_id] / user_cheat_count[user_id]
        
        # 风险等级评估
        risk_users = []
        for user_id, count in user_cheat_count.items():
            avg_sim = avg_similarity[user_id]
            if count >= 3 or avg_sim > 0.95:
                risk_level = 'HIGH'
            elif count >= 2 or avg_sim > 0.85:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            risk_users.append({
                'user_id': user_id,
                'cheat_count': count,
                'avg_similarity': round(avg_sim, 3),
                'risk_level': risk_level
            })
        
        # 按风险等级排序
        risk_users.sort(
            key=lambda x: (x['risk_level'] == 'HIGH', x['avg_similarity']),
            reverse=True
        )
        
        return {
            'game_id': game_id,
            'total_cheats': len(cheats),
            'suspicious_users': len(user_cheat_count),
            'risk_users': risk_users,
            'generated_at': datetime.utcnow().isoformat()
        }


# 全局服务实例
cheat_detection_service = CheatDetectionService()
