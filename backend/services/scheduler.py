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
        self._register_container_cleanup()
        self._register_pcap_cleanup()
        self._register_hide_ephemeral_games()
        self._register_pcap_reconcile()
        self._register_container_start_queue()
        
        # 启动调度器
        if not self.scheduler.running:
            self.scheduler.start()
            app.logger.info("任务调度器已启动")
    
    def _register_container_cleanup(self):
        """周期清理过期容器实例（对齐 Ret2Shell 约 30s 节奏）"""
        self.scheduler.add_job(
            func=self._cleanup_expired_containers,
            trigger='interval',
            seconds=30,
            id='container_cleanup',
            name='清理过期容器',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _cleanup_expired_containers(self):
        if not self.app:
            return
        with self.app.app_context():
            try:
                from backend.services.container_service import container_service
                ghosts = container_service.reconcile_ghost_instances()
                if ghosts:
                    self.app.logger.info("清理幽灵运行实例: %s 个", ghosts)
                orphans = container_service.reconcile_orphan_docker_containers()
                if orphans:
                    self.app.logger.info("清理 Docker 孤儿容器: %s 个", orphans)
                cleaned_count, cleaned_ids = container_service.cleanup_expired_containers()
                if cleaned_count:
                    self.app.logger.info(
                        "定时清理过期容器: %s 个 %s",
                        cleaned_count,
                        [str(i)[:12] if i else i for i in cleaned_ids[:10]],
                    )
            except Exception as e:
                self.app.logger.warning("定时清理过期容器失败: %s", e)

    def _register_pcap_cleanup(self):
        """每天凌晨 3 点清理过期 PCAP 文件（默认保留 30 天）"""
        self.scheduler.add_job(
            func=self._cleanup_old_pcaps,
            trigger=CronTrigger(hour=3, minute=15),
            id='pcap_cleanup',
            name='清理过期 PCAP',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _cleanup_old_pcaps(self):
        if not self.app:
            return
        with self.app.app_context():
            try:
                from backend.server.traffic_capture import get_traffic_manager
                from backend.server.config import settings
                days = int(
                    self.app.config.get('PCAP_RETENTION_DAYS')
                    or getattr(settings, 'PCAP_RETENTION_DAYS', 30)
                    or 30
                )
                stats = get_traffic_manager().cleanup_old_captures(days=days)
                if stats.get('deleted'):
                    self.app.logger.info(
                        "PCAP 清理: deleted=%s freed_mb=%.1f",
                        stats.get('deleted'),
                        (stats.get('freed_bytes') or 0) / 1024 / 1024,
                    )
                quota = get_traffic_manager().enforce_disk_quota()
                if quota.get('deleted'):
                    self.app.logger.info("PCAP 配额回收: %s", quota)
            except Exception as e:
                self.app.logger.warning("定时清理 PCAP 失败: %s", e)

    def _register_container_start_queue(self):
        """每 2 秒消费启容器队列"""
        self.scheduler.add_job(
            func=self._process_container_start_queue,
            trigger='interval',
            seconds=2,
            id='container_start_queue',
            name='启容器队列消费',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _process_container_start_queue(self):
        if not self.app:
            return
        with self.app.app_context():
            try:
                from backend.services.container_start_queue import process_container_start_queue
                from backend.server.config import settings
                n = process_container_start_queue(
                    max_jobs=int(getattr(settings, 'CONTAINER_START_MAX_CONCURRENT', 2) or 2),
                )
                if n:
                    self.app.logger.debug("启容器队列处理 %s 个任务", n)
            except Exception as e:
                self.app.logger.warning("启容器队列消费失败: %s", e)

    def _register_pcap_reconcile(self):
        """每天凌晨 3:45 对账 PCAP DB 与磁盘"""
        self.scheduler.add_job(
            func=self._reconcile_pcap_storage,
            trigger=CronTrigger(hour=3, minute=45),
            id='pcap_reconcile',
            name='PCAP 磁盘/DB 对账',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _reconcile_pcap_storage(self):
        if not self.app:
            return
        with self.app.app_context():
            try:
                from backend.services.traffic_capture_service import TrafficCaptureService
                prune = bool(self.app.config.get('PCAP_PRUNE_ORPHAN_FILES', False))
                stats = TrafficCaptureService.reconcile_consistency(
                    delete_missing_records=True,
                    prune_orphan_files=prune,
                )
                if any(stats.get(k) for k in (
                    'missing_records_deleted', 'orphans_imported', 'orphan_files_deleted',
                )):
                    self.app.logger.info("PCAP 对账: %s", stats)
            except Exception as e:
                self.app.logger.warning("PCAP 对账失败: %s", e)

    def _register_hide_ephemeral_games(self):
        """每小时隐藏仍公开的 E2E/探针赛事"""
        self.scheduler.add_job(
            func=self._hide_ephemeral_games,
            trigger='interval',
            hours=1,
            id='hide_ephemeral_games',
            name='隐藏 E2E/探针赛事',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    def _hide_ephemeral_games(self):
        if not self.app:
            return
        with self.app.app_context():
            try:
                from backend.server.db_models import CtfGame
                from backend.server.extensions import db
                from backend.server.game_filters import is_ephemeral_test_game

                games = CtfGame.query.filter_by(is_public=True).all()
                targets = [g for g in games if is_ephemeral_test_game(g)]
                if not targets:
                    return
                for g in targets:
                    g.is_public = False
                db.session.commit()
                self.app.logger.info(
                    "已隐藏 %s 场公开 E2E/探针赛: %s",
                    len(targets),
                    [g.id for g in targets[:20]],
                )
            except Exception as e:
                self.app.logger.warning("隐藏 E2E 赛事失败: %s", e)

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
