"""
Docker 容器管理服务
支持：动态容器编排、资源限制、网络隔离、容器状态追踪
"""

import docker
import logging
import uuid
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from backend.server.extensions import db
from backend.server.db_models import CtfGameInstance, CtfChallenge, User, Team, CtfGame
import os
from backend.services.flag_generator import ContainerFlagService, ensure_team_hash_salt
from backend.server.container_access import build_connection_url, normalize_connection_url
from backend.server.container_ports import allocate_host_port, release_host_port
from backend.services.container_traffic import maybe_start_traffic_capture

logger = logging.getLogger(__name__)


class ContainerService:
    """容器管理服务"""
    
    def __init__(self):
        """初始化 Docker 客户端（失败不永久缓存：后续 is_available 会重连）"""
        self.client = None
        self._connect()

    def _connect(self) -> bool:
        """连接 / 重连 Docker Engine（覆盖 Desktop 晚于 Flask 启动的场景）"""
        try:
            client = docker.from_env()
            client.ping()
            self.client = client
            logger.info("Docker client initialized successfully")
            return True
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize Docker client: {e}")
            return False

    def is_available(self) -> bool:
        """检查 Docker 是否可用；不可用时尝试重连一次"""
        if self.client is not None:
            try:
                self.client.ping()
                return True
            except Exception as e:
                logger.warning(f"Docker ping failed, will reconnect: {e}")
                self.client = None
        return self._connect()

    def create_container(
        self,
        challenge: CtfChallenge,
        user: User,
        team: Optional[Team] = None,
        expire_hours: int | None = None
    ) -> Tuple[bool, Optional[CtfGameInstance], str]:
        """
        为用户创建动态容器实例
        
        Args:
            challenge: 题目对象
            user: 用户对象
            team: 所属团队（可选）
            expire_hours: 容器过期时间（小时）
        
        Returns:
            (是否成功, CtfGameInstance 对象或None, 消息)
        """
        
        if not self.is_available():
            return False, None, "Docker service is not available"
        
        if not challenge.docker_image:
            return False, None, "Challenge does not have a Docker image configured"

        from backend.services.container_expire import default_container_expire_hours
        if expire_hours is None:
            expire_hours = default_container_expire_hours()

        from backend.services.instance_quota import check_can_start_new_instance
        ok_quota, quota_msg, existing = check_can_start_new_instance(
            user, team, challenge_id=challenge.id,
        )
        if existing:
            url = normalize_connection_url(existing, challenge=challenge)
            if url and url != (existing.connection_url or ""):
                existing.connection_url = url
                db.session.commit()
            return True, existing, quota_msg or "instance already running"
        if not ok_quota:
            return False, None, quota_msg

        host_port = None
        container = None
        try:
            # 生成唯一的容器名称
            container_name = f"ctf-{challenge.id}-{user.id}-{uuid.uuid4().hex[:8]}"

            is_dynamic_container = int(challenge.challenge_type or 0) == 3
            # 使用模块顶层 CtfGame，勿在函数内再 import（会遮蔽导致 UnboundLocalError）
            game = CtfGame.query.get(challenge.game_id)
            team_hash_salt = None
            if challenge.flag_template or is_dynamic_container:
                team_hash_salt = ensure_team_hash_salt(game)

            dynamic_flag = ContainerFlagService.generate_dynamic_flag(
                flag_template=challenge.flag_template or "flag{[TEAM_HASH]}",
                challenge_id=challenge.id,
                user_id=user.id,
                game_id=challenge.game_id,
                team_id=team.id if team else user.id,
                team_hash_salt=team_hash_salt,
            ) if (challenge.flag_template or is_dynamic_container) else None

            capture_enabled = bool(game and game.enable_traffic_capture and is_dynamic_container)
            host_port = allocate_host_port()
            if not host_port:
                return False, None, "无可用端口（10000-20000 已耗尽）"

            env_vars = [
                f'TEAM_ID={team.id if team else user.id}',
                f'USER_ID={user.id}',
                f'CHALLENGE_ID={challenge.id}'
            ]
            if dynamic_flag:
                env_vars.extend([
                    f'FLAG={dynamic_flag}',
                ])
            elif challenge.flag:
                env_vars.extend([
                    f'FLAG={challenge.flag}',
                ])
            
            # 准备容器配置
            container_config = {
                'image': challenge.docker_image,
                'name': container_name,
                'detach': True,
                'auto_remove': False,
                'cpu_quota': challenge.cpu_count * 100000,  # CPU 限制
                'mem_limit': f"{challenge.memory_limit}m",  # 内存限制
                'memswap_limit': f"{challenge.memory_limit}m",  # 交换内存限制
                'storage_opt': {
                    'size': f"{challenge.storage_limit}m"  # 存储限制
                },
                'environment': env_vars,
                'labels': {
                    'ctf_challenge': str(challenge.id),
                    'ctf_user': str(user.id),
                    'ctf_team': str(team.id) if team else str(user.id),
                    'ctf_created_at': datetime.utcnow().isoformat()
                }
            }
            
            # 根据网络隔离模式配置网络
            if challenge.network_mode == "Isolated":
                # 创建或获取隔离网络
                network_name = f"ctf-isolated-{challenge.id}"
                container_config['network_mode'] = network_name
            else:
                # 使用桥接网络（开放模式）— 端口限定在 10000–20000
                container_config['network_mode'] = 'bridge'
                bind_host = '127.0.0.1' if capture_enabled else '0.0.0.0'
                container_config['ports'] = {
                    f'{challenge.docker_port}/tcp': (bind_host, host_port)
                }
            
            # 创建容器
            container = self.client.containers.run(**container_config)
            
            logger.info(f"Container created: {container.id[:12]}")
            
            # 获取容器信息
            container.reload()
            mapped_port = None
            connection_url = None
            
            if challenge.network_mode != "Isolated":
                mapped_port = host_port
                connection_url = build_connection_url(mapped_port, challenge=challenge)
            else:
                # 隔离网络模式下使用容器内部地址
                connection_url = f"http://{container_name}:{challenge.docker_port}"
            
            # 创建数据库记录
            instance = CtfGameInstance(
                challenge_id=challenge.id,
                team_id=team.id if team else None,
                user_id=user.id,
                container_id=container.id,
                container_image=challenge.docker_image,
                port=mapped_port,
                connection_url=connection_url,
                is_running=True,
                dynamic_flag=dynamic_flag,
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=expire_hours)
            )
            
            db.session.add(instance)
            db.session.flush()

            if capture_enabled:
                maybe_start_traffic_capture(challenge, instance, user, team)
            db.session.commit()
            
            return True, instance, f"Container created successfully at {instance.connection_url}"
        
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
            # Docker 已创建但 DB 失败：立即回收，避免幽灵容器 + 端口泄漏
            if container is not None:
                try:
                    container.remove(force=True)
                    logger.info(
                        "Rolled back orphan docker container %s after create failure",
                        (getattr(container, "id", "") or "")[:12],
                    )
                except Exception as cleanup_err:
                    logger.warning("Failed to remove orphan container after create error: %s", cleanup_err)
            release_host_port(host_port)
            return False, None, f"Failed to create container: {str(e)}"

    @staticmethod
    def _is_missing_container_error(exc: Exception) -> bool:
        """Docker 容器已不存在（404 / NotFound / No such container）"""
        if isinstance(exc, docker.errors.NotFound):
            return True
        # docker SDK 有时会包一层 APIError，文案含 404
        msg = str(exc).lower()
        return "no such container" in msg or "404 client error" in msg or "not found" in msg

    def _mark_instance_stopped(self, instance: CtfGameInstance) -> None:
        instance.is_running = False
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def destroy_container(self, instance: CtfGameInstance) -> Tuple[bool, str]:
        """
        销毁容器实例。

        Docker 侧容器已不存在时视为成功，并清理数据库 is_running，
        避免定时清理每 30s 对幽灵 container_id 反复报错。
        """
        cid = (instance.container_id or "")[:12] or "(none)"

        if not instance.container_id:
            self._mark_instance_stopped(instance)
            return True, "No container ID; instance marked stopped"

        if not self.client:
            self._mark_instance_stopped(instance)
            logger.warning(f"Docker unavailable; marked instance stopped ({cid})")
            return True, "Docker unavailable; instance marked stopped"

        try:
            container = self.client.containers.get(instance.container_id)
            try:
                container.stop(timeout=10)
            except Exception as stop_err:
                if not self._is_missing_container_error(stop_err):
                    logger.warning(f"Stop container {cid} failed, force remove: {stop_err}")
                try:
                    container.kill()
                except Exception:
                    pass
            try:
                container.remove(force=True)
            except Exception as remove_err:
                if not self._is_missing_container_error(remove_err):
                    logger.warning(f"Remove container {cid} failed: {remove_err}")

            port = instance.port
            self._mark_instance_stopped(instance)
            release_host_port(port)
            logger.info(f"Container destroyed: {cid}")
            return True, "Container destroyed successfully"

        except Exception as e:
            # 容器已在 Docker 中消失：清库即可，不要当失败反复刷日志
            if self._is_missing_container_error(e):
                port = instance.port
                self._mark_instance_stopped(instance)
                release_host_port(port)
                logger.info(f"Container already gone, marked stopped: {cid}")
                return True, "Container already removed; instance marked stopped"

            # 其它 Docker 错误：仍标记停止，避免选手卡在「幽灵运行中」
            logger.error(f"Failed to destroy container {cid}: {e}")
            try:
                port = instance.port
                self._mark_instance_stopped(instance)
                release_host_port(port)
            except Exception:
                pass
            return True, f"Instance marked stopped (docker error: {e})"
    
    def get_container_status(self, instance: CtfGameInstance) -> Dict:
        """
        获取容器状态
        
        Args:
            instance: CtfGameInstance 对象
        
        Returns:
            容器状态字典
        """
        
        if not instance.container_id:
            return {'status': 'unknown', 'message': 'No container ID'}
        
        try:
            container = self.client.containers.get(instance.container_id)
            container.reload()
            
            stats = container.stats(stream=False)
            
            return {
                'status': container.status,
                'id': container.id[:12],
                'name': container.name,
                'memory_usage': stats['memory_stats'].get('usage', 0),
                'memory_limit': stats['memory_stats'].get('limit', 0),
                'cpu_usage': stats['cpu_stats'].get('cpu_usage', {}).get('total_usage', 0),
                'is_running': instance.is_running,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None
            }
        
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def cleanup_expired_containers(self) -> Tuple[int, List[str]]:
        """
        清理已过期的容器
        
        Returns:
            (清理数量, 清理的容器ID列表)
        """
        
        if not self.is_available():
            return 0, []
        
        cleaned_count = 0
        cleaned_ids = []
        
        try:
            # 查询已过期的容器实例
            expired_instances = CtfGameInstance.query.filter(
                CtfGameInstance.is_running == True,
                CtfGameInstance.expires_at < datetime.utcnow()
            ).all()
            
            for instance in expired_instances:
                cid = instance.container_id or ""
                success, msg = self.destroy_container(instance)
                if success:
                    cleaned_count += 1
                    if cid:
                        cleaned_ids.append(cid)
                    logger.info(f"Cleaned expired instance #{instance.id}: {msg}")
                else:
                    logger.warning(f"Skip expired instance #{instance.id}: {msg}")
            
            return cleaned_count, cleaned_ids
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired containers: {e}")
            return 0, []

    def reconcile_ghost_instances(self) -> int:
        """将 Docker 侧已不存在、但 DB 仍 is_running 的实例标为停止。"""
        if not self.is_available():
            # 无 Docker 时仍清库，避免前端一直显示运行中
            rows = CtfGameInstance.query.filter_by(is_running=True).all()
            for inst in rows:
                inst.is_running = False
            if rows:
                db.session.commit()
            return len(rows)

        fixed = 0
        rows = CtfGameInstance.query.filter_by(is_running=True).all()
        for inst in rows:
            if not inst.container_id:
                inst.is_running = False
                fixed += 1
                continue
            try:
                c = self.client.containers.get(inst.container_id)
                c.reload()
                # 容器还在但已退出：同样视为幽灵运行态
                if getattr(c, "status", None) != "running":
                    inst.is_running = False
                    fixed += 1
            except Exception as e:
                if self._is_missing_container_error(e):
                    inst.is_running = False
                    fixed += 1
                # 其它错误留给 destroy/手动处理
        if fixed:
            db.session.commit()
            logger.info(f"Reconciled {fixed} ghost running instances")
        return fixed

    def reconcile_orphan_docker_containers(self) -> int:
        """清理 Docker 中仍在、但 DB 无对应记录的 ctf-* 实例容器。

        仅匹配实例命名：``ctf-{challenge_id}-{user_id}-{hex}``。
        不处理 ``ctf-isolated-*`` 网络等其它资源。
        """
        import re

        if not self.is_available():
            return 0

        name_re = re.compile(r'^/?ctf-\d+-\d+-[0-9a-f]{6,}$', re.IGNORECASE)
        known_ids = {
            row.container_id
            for row in CtfGameInstance.query.filter(
                CtfGameInstance.container_id.isnot(None)
            ).all()
            if row.container_id
        }
        # 短 ID / 长 ID 都算已知
        known_prefixes = set()
        for cid in known_ids:
            known_prefixes.add(cid)
            if len(cid) >= 12:
                known_prefixes.add(cid[:12])

        removed = 0
        try:
            containers = self.client.containers.list(all=True)
        except Exception as e:
            logger.warning(f"List docker containers failed: {e}")
            return 0

        for c in containers:
            names = [c.name] + list(getattr(c, 'attrs', {}).get('Names', []) or [])
            match_name = None
            for n in names:
                if n and name_re.match(n):
                    match_name = n
                    break
            if not match_name:
                continue

            cid = c.id or ''
            short = cid[:12]
            if cid in known_prefixes or short in known_prefixes:
                continue
            # DB 可能存短 ID
            if any(k.startswith(short) or short.startswith(k[:12]) for k in known_ids if k):
                continue

            try:
                if c.status == 'running':
                    c.stop(timeout=5)
                c.remove(force=True)
                removed += 1
                logger.info(f"Removed orphan docker container {short} ({match_name})")
            except Exception as e:
                if self._is_missing_container_error(e):
                    continue
                logger.warning(f"Failed to remove orphan {short}: {e}")

        if removed:
            logger.info(f"Reconciled {removed} orphan docker containers")
        return removed
    
    def list_user_containers(self, user_id: int, game_id: Optional[int] = None) -> List[Dict]:
        """
        列出用户的所有容器
        
        Args:
            user_id: 用户 ID
            game_id: 可选的比赛 ID 过滤
        
        Returns:
            容器实例列表
        """
        
        query = CtfGameInstance.query.filter_by(user_id=user_id)
        
        if game_id:
            query = query.join(CtfChallenge).filter(CtfChallenge.game_id == game_id)
        
        instances = query.all()
        
        result = []
        for instance in instances:
            status = self.get_container_status(instance)
            result.append({
                'id': instance.id,
                'challenge_id': instance.challenge_id,
                'connection_url': instance.connection_url,
                'is_running': instance.is_running,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'status': status
            })
        
        return result
    
    def renew_container_lease(self, instance: CtfGameInstance, hours: int = 2) -> Tuple[bool, str]:
        """
        续期容器
        
        Args:
            instance: CtfGameInstance 对象
            hours: 续期小时数
        
        Returns:
            (是否成功, 消息)
        """
        
        try:
            instance.expires_at = datetime.utcnow() + timedelta(hours=hours)
            db.session.commit()
            
            logger.info(f"Container lease renewed: {instance.container_id[:12]}")
            return True, f"Container lease renewed until {instance.expires_at.isoformat()}"
        
        except Exception as e:
            logger.error(f"Failed to renew container lease: {e}")
            return False, f"Failed to renew lease: {str(e)}"
    
    def get_container_logs(self, instance: CtfGameInstance, tail: int = 100) -> str:
        """
        获取容器日志
        
        Args:
            instance: CtfGameInstance 对象
            tail: 最后多少行日志
        
        Returns:
            日志内容
        """
        
        if not instance.container_id:
            return "No container ID found"
        
        try:
            container = self.client.containers.get(instance.container_id)
            logs = container.logs(tail=tail, stdout=True, stderr=True)
            return logs.decode('utf-8', errors='ignore')
        
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            return f"Failed to get logs: {str(e)}"


# 全局容器服务实例
container_service = ContainerService()
