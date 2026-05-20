"""
定时任务调度器
用于定期更新赛季统计、清理过期容器等
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from backend.services.season_stats_service import SeasonStatsService
from backend.server.db_models import CtfSeason, CtfGame


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化调度器"""
        self.app = app
        
        # 注册定时任务
        self._register_season_stats_update()
        
        # 启动调度器
        if not self.scheduler.running:
            self.scheduler.start()
            app.logger.info("任务调度器已启动")
    
    def _register_season_stats_update(self):
        """
        注册赛季统计更新任务
        每小时运行一次，更新当前活跃赛季的统计数据
        """
        self.scheduler.add_job(
            func=self._update_active_seasons_stats,
            trigger=CronTrigger(minute=0),  # 每小时整点运行
            id='season_stats_update',
            name='更新赛季统计',
            replace_existing=True
        )
        
        # 也可以选择每天凌晨2点更新所有赛季
        self.scheduler.add_job(
            func=self._update_all_seasons_stats,
            trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点运行
            id='season_stats_daily_update',
            name='每日赛季统计更新',
            replace_existing=True
        )
    
    def _update_active_seasons_stats(self):
        """
        更新当前活跃赛季的统计数据
        活跃赛季：包含进行中或最近结束的比赛
        """
        if not self.app:
            return
        
        with self.app.app_context():
            try:
                # 查询所有活跃赛季（假设当前年份 ±1）
                current_year = datetime.now().year
                active_seasons = CtfSeason.query.filter(
                    CtfSeason.year.between(current_year - 1, current_year + 1)
                ).all()
                
                for season in active_seasons:
                    # 检查赛季是否有进行中或最近结束的比赛
                    recent_games = CtfGame.query.filter_by(season_id=season.id).filter(
                        CtfGame.end_time >= datetime.utcnow()
                    ).count()
                    
                    if recent_games > 0:
                        print(f"正在更新赛季 {season.year}-{season.season} 的统计...")
                        result = SeasonStatsService.update_entire_season_stats(season.id)
                        print(f"赛季 {season.year}-{season.season} 更新完成: "
                              f"用户 {result['users_updated']} 个, "
                              f"团队 {result['teams_updated']} 个")
                
            except Exception as e:
                print(f"更新活跃赛季统计失败: {e}")
    
    def _update_all_seasons_stats(self):
        """
        更新所有赛季的统计数据
        用于每日完整统计计算
        """
        if not self.app:
            return
        
        with self.app.app_context():
            try:
                all_seasons = CtfSeason.query.all()
                
                for season in all_seasons:
                    print(f"正在更新赛季 {season.year}-{season.season} 的统计...")
                    result = SeasonStatsService.update_entire_season_stats(season.id)
                    print(f"赛季 {season.year}-{season.season} 更新完成: "
                          f"用户 {result['users_updated']} 个, "
                          f"团队 {result['teams_updated']} 个")
                
            except Exception as e:
                print(f"更新所有赛季统计失败: {e}")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            if self.app:
                self.app.logger.info("任务调度器已关闭")


# 创建全局调度器实例
scheduler = TaskScheduler()
