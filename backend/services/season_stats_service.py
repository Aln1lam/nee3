"""
赛季统计更新服务
提供赛季级别的用户和团队统计数据计算和更新
"""

from datetime import datetime
from sqlalchemy import func, and_
from backend.server.extensions import db
from backend.server.db_models import (
    CtfSeason, CtfGame, CtfParticipation, CtfParticipatingUser,
    CtfChallengeSubmission, CtfScoreboard,
    UserSeasonStats, TeamSeasonStats,
    User, Team
)


class SeasonStatsService:
    """赛季统计服务"""
    
    @staticmethod
    def update_user_season_stats(user_id, season_id):
        """
        更新单个用户的赛季统计数据
        
        Args:
            user_id: 用户ID
            season_id: 赛季ID
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取该赛季所有比赛
            season_games = CtfGame.query.filter_by(season_id=season_id).all()
            game_ids = [game.id for game in season_games]
            
            if not game_ids:
                return False
            
            # 1. 查询用户参与的比赛数量（通过 CtfParticipatingUser）
            user_participations = db.session.query(func.count(func.distinct(CtfParticipatingUser.game_id))).filter(
                CtfParticipatingUser.user_id == user_id,
                CtfParticipatingUser.game_id.in_(game_ids)
            ).scalar() or 0
            
            # 2. 查询用户的总分数（所有正确提交的分数总和）
            total_points = db.session.query(func.sum(CtfChallengeSubmission.points_awarded)).filter(
                CtfChallengeSubmission.user_id == user_id,
                CtfChallengeSubmission.game_id.in_(game_ids),
                CtfChallengeSubmission.is_correct == True
            ).scalar() or 0
            
            # 3. 查询用户解决的题目数量（去重）
            total_challenges_solved = db.session.query(func.count(func.distinct(CtfChallengeSubmission.challenge_id))).filter(
                CtfChallengeSubmission.user_id == user_id,
                CtfChallengeSubmission.game_id.in_(game_ids),
                CtfChallengeSubmission.is_correct == True
            ).scalar() or 0
            
            # 4. 查询或创建赛季统计记录
            stats = UserSeasonStats.query.filter_by(
                user_id=user_id,
                season_id=season_id
            ).first()
            
            if not stats:
                stats = UserSeasonStats(
                    user_id=user_id,
                    season_id=season_id,
                    total_games_participated=user_participations,
                    total_points=total_points,
                    total_challenges_solved=total_challenges_solved,
                    season_rank=None  # 排名稍后计算
                )
                db.session.add(stats)
            else:
                stats.total_games_participated = user_participations
                stats.total_points = total_points
                stats.total_challenges_solved = total_challenges_solved
                stats.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"更新用户赛季统计失败: {e}")
            return False
    
    @staticmethod
    def update_team_season_stats(team_id, season_id):
        """
        更新单个团队的赛季统计数据
        
        Args:
            team_id: 团队ID
            season_id: 赛季ID
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取该赛季所有比赛
            season_games = CtfGame.query.filter_by(season_id=season_id).all()
            game_ids = [game.id for game in season_games]
            
            if not game_ids:
                return False
            
            # 1. 查询团队参与的比赛数量
            team_participations = db.session.query(func.count(CtfParticipation.id)).filter(
                CtfParticipation.team_id == team_id,
                CtfParticipation.game_id.in_(game_ids)
            ).scalar() or 0
            
            # 2. 查询团队的总分数（从 CtfScoreboard）
            total_points = db.session.query(func.sum(CtfScoreboard.total_points)).filter(
                CtfScoreboard.team_id == team_id,
                CtfScoreboard.game_id.in_(game_ids)
            ).scalar() or 0
            
            # 3. 查询团队解决的题目数量（从 CtfScoreboard）
            total_challenges_solved = db.session.query(func.sum(CtfScoreboard.solved_challenges)).filter(
                CtfScoreboard.team_id == team_id,
                CtfScoreboard.game_id.in_(game_ids)
            ).scalar() or 0
            
            # 4. 查询或创建赛季统计记录
            stats = TeamSeasonStats.query.filter_by(
                team_id=team_id,
                season_id=season_id
            ).first()
            
            if not stats:
                stats = TeamSeasonStats(
                    team_id=team_id,
                    season_id=season_id,
                    total_games_participated=team_participations,
                    total_points=total_points,
                    total_challenges_solved=total_challenges_solved,
                    season_rank=None  # 排名稍后计算
                )
                db.session.add(stats)
            else:
                stats.total_games_participated = team_participations
                stats.total_points = total_points
                stats.total_challenges_solved = total_challenges_solved
                stats.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"更新团队赛季统计失败: {e}")
            return False
    
    @staticmethod
    def recalculate_all_user_season_ranks(season_id):
        """
        重新计算赛季内所有用户的排名
        按总分降序、题目数降序排序
        
        Args:
            season_id: 赛季ID
        
        Returns:
            bool: 计算是否成功
        """
        try:
            # 查询该赛季的所有用户统计记录，按分数和题目数排序
            user_stats = UserSeasonStats.query.filter_by(season_id=season_id).order_by(
                UserSeasonStats.total_points.desc(),
                UserSeasonStats.total_challenges_solved.desc()
            ).all()
            
            # 分配排名
            for rank, stats in enumerate(user_stats, start=1):
                stats.season_rank = rank
                stats.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"计算用户赛季排名失败: {e}")
            return False
    
    @staticmethod
    def recalculate_all_team_season_ranks(season_id):
        """
        重新计算赛季内所有团队的排名
        按总分降序、题目数降序排序
        
        Args:
            season_id: 赛季ID
        
        Returns:
            bool: 计算是否成功
        """
        try:
            # 查询该赛季的所有团队统计记录，按分数和题目数排序
            team_stats = TeamSeasonStats.query.filter_by(season_id=season_id).order_by(
                TeamSeasonStats.total_points.desc(),
                TeamSeasonStats.total_challenges_solved.desc()
            ).all()
            
            # 分配排名
            for rank, stats in enumerate(team_stats, start=1):
                stats.season_rank = rank
                stats.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"计算团队赛季排名失败: {e}")
            return False
    
    @staticmethod
    def update_entire_season_stats(season_id):
        """
        更新整个赛季的所有统计数据（用户 + 团队）
        适用于：赛季结束后批量计算、定时任务
        
        Args:
            season_id: 赛季ID
        
        Returns:
            dict: 更新结果统计
        """
        try:
            result = {
                'users_updated': 0,
                'teams_updated': 0,
                'success': True,
                'errors': []
            }
            
            # 1. 获取该赛季所有参与的用户
            season_games = CtfGame.query.filter_by(season_id=season_id).all()
            game_ids = [game.id for game in season_games]
            
            if not game_ids:
                result['success'] = False
                result['errors'].append('该赛季没有比赛')
                return result
            
            # 查询所有参与用户
            user_ids = db.session.query(func.distinct(CtfParticipatingUser.user_id)).filter(
                CtfParticipatingUser.game_id.in_(game_ids)
            ).all()
            user_ids = [uid[0] for uid in user_ids]
            
            # 2. 查询所有参与团队
            team_ids = db.session.query(func.distinct(CtfParticipation.team_id)).filter(
                CtfParticipation.game_id.in_(game_ids)
            ).all()
            team_ids = [tid[0] for tid in team_ids]
            
            # 3. 更新所有用户统计
            for user_id in user_ids:
                if SeasonStatsService.update_user_season_stats(user_id, season_id):
                    result['users_updated'] += 1
                else:
                    result['errors'].append(f'用户 {user_id} 更新失败')
            
            # 4. 更新所有团队统计
            for team_id in team_ids:
                if SeasonStatsService.update_team_season_stats(team_id, season_id):
                    result['teams_updated'] += 1
                else:
                    result['errors'].append(f'团队 {team_id} 更新失败')
            
            # 5. 重新计算排名
            SeasonStatsService.recalculate_all_user_season_ranks(season_id)
            SeasonStatsService.recalculate_all_team_season_ranks(season_id)
            
            return result
            
        except Exception as e:
            print(f"批量更新赛季统计失败: {e}")
            return {
                'success': False,
                'users_updated': 0,
                'teams_updated': 0,
                'errors': [str(e)]
            }
    
    @staticmethod
    def trigger_on_challenge_solved(user_id, team_id, game_id):
        """
        触发器：当题目被解决时调用
        用于实时更新赛季统计
        
        Args:
            user_id: 用户ID
            team_id: 团队ID
            game_id: 比赛ID
        """
        try:
            # 查询该比赛所属的赛季
            game = CtfGame.query.get(game_id)
            if not game or not game.season_id:
                return False
            
            season_id = game.season_id
            
            # 更新用户统计
            SeasonStatsService.update_user_season_stats(user_id, season_id)
            
            # 更新团队统计
            if team_id:
                SeasonStatsService.update_team_season_stats(team_id, season_id)
            
            # 重新计算排名（可选，避免频繁计算可改为定时任务）
            # SeasonStatsService.recalculate_all_user_season_ranks(season_id)
            # SeasonStatsService.recalculate_all_team_season_ranks(season_id)
            
            return True
            
        except Exception as e:
            print(f"赛季统计触发器失败: {e}")
            return False
    
    @staticmethod
    def get_user_season_leaderboard(season_id, limit=100):
        """
        获取赛季用户排行榜
        
        Args:
            season_id: 赛季ID
            limit: 返回前N名
        
        Returns:
            list: 排行榜数据
        """
        try:
            stats = UserSeasonStats.query.filter_by(season_id=season_id).order_by(
                UserSeasonStats.season_rank.asc()
            ).limit(limit).all()
            
            result = []
            for s in stats:
                user = User.query.get(s.user_id)
                result.append({
                    'rank': s.season_rank,
                    'user_id': s.user_id,
                    'username': user.username if user else 'Unknown',
                    'total_points': s.total_points,
                    'total_challenges_solved': s.total_challenges_solved,
                    'total_games_participated': s.total_games_participated
                })
            
            return result
            
        except Exception as e:
            print(f"获取赛季排行榜失败: {e}")
            return []
    
    @staticmethod
    def get_team_season_leaderboard(season_id, limit=100):
        """
        获取赛季团队排行榜
        
        Args:
            season_id: 赛季ID
            limit: 返回前N名
        
        Returns:
            list: 排行榜数据
        """
        try:
            stats = TeamSeasonStats.query.filter_by(season_id=season_id).order_by(
                TeamSeasonStats.season_rank.asc()
            ).limit(limit).all()
            
            result = []
            for s in stats:
                team = Team.query.get(s.team_id)
                result.append({
                    'rank': s.season_rank,
                    'team_id': s.team_id,
                    'team_name': team.name if team else 'Unknown',
                    'total_points': s.total_points,
                    'total_challenges_solved': s.total_challenges_solved,
                    'total_games_participated': s.total_games_participated
                })
            
            return result
            
        except Exception as e:
            print(f"获取团队赛季排行榜失败: {e}")
            return []
