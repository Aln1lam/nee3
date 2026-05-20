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
from backend.server.db_models import CtfGameInstance, CtfChallenge, User, Team
import os

logger = logging.getLogger(__name__)


class ContainerService:
    """容器管理服务"""
    
    def __init__(self):
        """初始化 Docker 客户端"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查 Docker 是否可用"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker is not available: {e}")
            return False
    
    def create_container(
        self,
        challenge: CtfChallenge,
        user: User,
        team: Optional[Team] = None,
        expire_hours: int = 2
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
        
        try:
            # 生成唯一的容器名称
            container_name = f"ctf-{challenge.id}-{user.id}-{uuid.uuid4().hex[:8]}"
            
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
                'environment': [
                    f'TEAM_ID={team.id if team else user.id}',
                    f'USER_ID={user.id}',
                    f'CHALLENGE_ID={challenge.id}'
                ],
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
                # 使用桥接网络（开放模式）
                container_config['network_mode'] = 'bridge'
                container_config['ports'] = {
                    f'{challenge.docker_port}/tcp': None  # 随机映射端口
                }
            
            # 创建容器
            container = self.client.containers.run(**container_config)
            
            logger.info(f"Container created: {container.id[:12]}")
            
            # 获取容器信息
            container.reload()
            mapped_port = None
            connection_url = None
            
            if challenge.network_mode != "Isolated":
                # 获取映射的端口
                ports = container.ports
                if ports and f'{challenge.docker_port}/tcp' in ports:
                    port_info = ports[f'{challenge.docker_port}/tcp']
                    if port_info:
                        mapped_port = port_info[0]['HostPort']
                        connection_url = f"http://localhost:{mapped_port}"
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
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=expire_hours)
            )
            
            db.session.add(instance)
            db.session.commit()
            
            return True, instance, f"Container created successfully at {connection_url}"
        
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            return False, None, f"Failed to create container: {str(e)}"
    
    def destroy_container(self, instance: CtfGameInstance) -> Tuple[bool, str]:
        """
        销毁容器实例
        
        Args:
            instance: CtfGameInstance 对象
        
        Returns:
            (是否成功, 消息)
        """
        
        if not instance.container_id:
            return False, "No container ID found"
        
        try:
            container = self.client.containers.get(instance.container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            
            instance.is_running = False
            db.session.commit()
            
            logger.info(f"Container destroyed: {instance.container_id[:12]}")
            return True, "Container destroyed successfully"
        
        except Exception as e:
            logger.error(f"Failed to destroy container: {e}")
            return False, f"Failed to destroy container: {str(e)}"
    
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
                success, msg = self.destroy_container(instance)
                if success:
                    cleaned_count += 1
                    cleaned_ids.append(instance.container_id)
                    logger.info(f"Cleaned expired container: {instance.container_id[:12]}")
            
            return cleaned_count, cleaned_ids
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired containers: {e}")
            return 0, []
    
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
