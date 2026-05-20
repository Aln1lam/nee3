"""
权限控制系统服务
细粒度权限模型、角色定义、权限检查装饰器
"""

from typing import Dict, List, Optional, Callable
from functools import wraps
from enum import IntFlag, IntEnum
import logging
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from backend.server.extensions import db
from backend.server.db_models import User, CtfGame, CtfParticipatingUser, ActivityLog

logger = logging.getLogger(__name__)


# ======================== 权限定义 ========================

class GamePermission(IntFlag):
    """游戏权限标志"""
    # 基础权限
    JOIN_GAME = 1 << 0                    # 加入比赛
    VIEW_CHALLENGE = 1 << 1               # 查看题目
    SUBMIT_FLAG = 1 << 2                  # 提交 Flag
    GET_SCORE = 1 << 3                    # 获得积分
    GET_BLOOD = 1 << 4                    # 获得血液奖励
    
    # 管理权限
    MANAGE_GAME = 1 << 8                  # 管理比赛
    MANAGE_CHALLENGE = 1 << 9             # 管理题目
    MANAGE_SCOREBOARD = 1 << 10           # 管理排行榜
    MANAGE_CONTAINERS = 1 << 11           # 管理容器
    
    # 审核权限
    REVIEW_SUBMISSION = 1 << 16           # 审核提交
    DETECT_CHEAT = 1 << 17                # 检测作弊
    
    # 全权限
    FULL_PERMISSION = 0xFFFFFFFF


class GameRole(IntEnum):
    """游戏角色"""
    NONE = 0
    PLAYER = 1                            # 普通参赛者
    MANAGER = 2                           # 比赛管理员
    ADMIN = 3                             # 系统管理员


class PlatformRole(IntEnum):
    """平台角色"""
    USER = 0
    MODERATOR = 1
    ADMIN = 2
    SUPER_ADMIN = 3


# 角色权限映射
ROLE_PERMISSIONS = {
    GameRole.PLAYER: (
        GamePermission.VIEW_CHALLENGE |
        GamePermission.SUBMIT_FLAG |
        GamePermission.GET_SCORE |
        GamePermission.GET_BLOOD
    ),
    GameRole.MANAGER: (
        GamePermission.VIEW_CHALLENGE |
        GamePermission.SUBMIT_FLAG |
        GamePermission.GET_SCORE |
        GamePermission.MANAGE_GAME |
        GamePermission.MANAGE_CHALLENGE |
        GamePermission.MANAGE_SCOREBOARD |
        GamePermission.REVIEW_SUBMISSION
    ),
    GameRole.ADMIN: (
        GamePermission.FULL_PERMISSION
    )
}

PLATFORM_ROLE_PERMISSIONS = {
    PlatformRole.USER: set(),
    PlatformRole.MODERATOR: {'view_logs', 'moderate_content'},
    PlatformRole.ADMIN: {'all_admin_features'},
    PlatformRole.SUPER_ADMIN: {'full_platform_control'}
}


# ======================== 权限检查服务 ========================

class PermissionService:
    """权限管理服务"""
    
    @staticmethod
    def get_user_game_role(user_id: int, game_id: int) -> GameRole:
        """
        获取用户在特定游戏中的角色
        
        Args:
            user_id: 用户 ID
            game_id: 游戏 ID
        
        Returns:
            GameRole 枚举值
        """
        
        user = User.query.get(user_id)
        if not user:
            return GameRole.NONE
        
        # 系统管理员拥有所有权限
        if user.is_admin:
            return GameRole.ADMIN
        
        # 查询用户参赛记录
        user_participation = CtfParticipatingUser.query.filter_by(
            user_id=user_id,
            game_id=game_id
        ).first()
        
        if not user_participation:
            return GameRole.NONE
        
        # 目前按默认玩家角色处理
        role_str = 'player'
        
        role_map = {
            'admin': GameRole.ADMIN,
            'manager': GameRole.MANAGER,
            'player': GameRole.PLAYER
        }
        
        return role_map.get(role_str, GameRole.PLAYER)
    
    @staticmethod
    def has_game_permission(
        user_id: int,
        game_id: int,
        required_permission: GamePermission
    ) -> bool:
        """
        检查用户是否有特定的游戏权限
        
        Args:
            user_id: 用户 ID
            game_id: 游戏 ID
            required_permission: 所需权限
        
        Returns:
            是否有权限
        """
        
        role = PermissionService.get_user_game_role(user_id, game_id)
        user_permissions = ROLE_PERMISSIONS.get(role, 0)
        
        return (user_permissions & required_permission) != 0
    
    @staticmethod
    def has_platform_permission(
        user_id: int,
        required_permission: str
    ) -> bool:
        """
        检查用户是否有特定的平台权限
        
        Args:
            user_id: 用户 ID
            required_permission: 所需权限字符串
        
        Returns:
            是否有权限
        """
        
        user = User.query.get(user_id)
        if not user:
            return False
        
        if user.is_admin:
            return True
        
        # 可以扩展为使用更复杂的权限系统
        # user_permissions = PLATFORM_ROLE_PERMISSIONS.get(user.platform_role, set())
        # return required_permission in user_permissions
        
        return False
    
    @staticmethod
    def check_challenge_permission(
        user_id: int,
        challenge_id: int,
        required_permission: GamePermission = GamePermission.VIEW_CHALLENGE
    ) -> bool:
        """
        检查用户是否有访问题目的权限
        
        Args:
            user_id: 用户 ID
            challenge_id: 题目 ID
            required_permission: 所需权限
        
        Returns:
            是否有权限
        """
        
        from backend.server.db_models import CtfChallenge
        
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge or not challenge.is_enabled:
            return False
        
        return PermissionService.has_game_permission(
            user_id,
            challenge.game_id,
            required_permission
        )
    
    @staticmethod
    def log_action(
        user_id: Optional[int],
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        status: str = 'success',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        meta: Optional[Dict] = None
    ) -> ActivityLog:
        """
        记录用户操作
        
        Args:
            user_id: 用户 ID
            action: 操作类型（如 'login', 'submit_flag', 'create_game' 等）
            target_type: 目标类型（如 'challenge', 'game', 'user' 等）
            target_id: 目标 ID
            target_name: 目标名称
            status: 操作状态（'success', 'failure' 等）
            ip_address: IP 地址
            user_agent: User Agent
            meta: 其他元数据
        
        Returns:
            ActivityLog 对象
        """
        
        user = User.query.get(user_id) if user_id else None
        
        log = ActivityLog(
            actor_id=user_id,
            actor_name=user.nickname if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            meta=meta
        )
        
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Action logged: {action} by user {user_id} on {target_type}:{target_id} - {status}")
        
        return log


# ======================== 权限检查装饰器 ========================

def require_permission(permission: GamePermission):
    """
    要求特定权限的装饰器（用于游戏权限）
    
    用法：
        @require_permission(GamePermission.MANAGE_CHALLENGE)
        def update_challenge(challenge_id):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            
            # 从路由参数中获取 game_id（需要在路由中定义）
            game_id = request.view_args.get('game_id') if request.view_args else None
            
            if not game_id:
                return jsonify({'error': 'CtfGame ID not found'}), 400
            
            if not PermissionService.has_game_permission(user_id, game_id, permission):
                return jsonify({'error': 'Permission denied'}), 403
            
            # 记录操作
            PermissionService.log_action(
                user_id,
                fn.__name__,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_platform_permission(permission: str):
    """
    要求特定平台权限的装饰器
    
    用法：
        @require_platform_permission('manage_users')
        def manage_users():
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not PermissionService.has_platform_permission(user_id, permission):
                return jsonify({'error': 'Permission denied'}), 403
            
            PermissionService.log_action(
                user_id,
                fn.__name__,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_challenge_permission(permission: GamePermission = GamePermission.VIEW_CHALLENGE):
    """
    要求特定题目权限的装饰器
    
    用法：
        @require_challenge_permission(GamePermission.SUBMIT_FLAG)
        def submit_flag(challenge_id):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            
            challenge_id = request.view_args.get('challenge_id') if request.view_args else None
            
            if not challenge_id:
                return jsonify({'error': 'Challenge ID not found'}), 400
            
            if not PermissionService.check_challenge_permission(user_id, challenge_id, permission):
                return jsonify({'error': 'Permission denied'}), 403
            
            PermissionService.log_action(
                user_id,
                fn.__name__,
                target_type='challenge',
                target_id=challenge_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def admin_only(fn: Callable) -> Callable:
    """
    仅限管理员的装饰器
    
    用法：
        @admin_only
        def delete_game(game_id):
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        PermissionService.log_action(
            user_id,
            f"{fn.__name__}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return fn(*args, **kwargs)
    
    return wrapper


# ======================== 权限矩阵生成 ========================

class PermissionMatrix:
    """权限矩阵 - 用于生成权限文档和验证"""
    
    @staticmethod
    def generate_role_matrix() -> Dict:
        """生成角色权限矩阵"""
        return {
            'player': {
                'view_challenge': True,
                'submit_flag': True,
                'get_score': True,
                'get_blood': True,
                'manage_game': False,
                'manage_challenge': False,
                'manage_scoreboard': False,
                'review_submission': False,
                'detect_cheat': False,
            },
            'manager': {
                'view_challenge': True,
                'submit_flag': True,
                'get_score': True,
                'get_blood': True,
                'manage_game': True,
                'manage_challenge': True,
                'manage_scoreboard': True,
                'review_submission': True,
                'detect_cheat': False,
            },
            'admin': {
                'view_challenge': True,
                'submit_flag': True,
                'get_score': True,
                'get_blood': True,
                'manage_game': True,
                'manage_challenge': True,
                'manage_scoreboard': True,
                'review_submission': True,
                'detect_cheat': True,
            }
        }
    
    @staticmethod
    def export_matrix_csv() -> str:
        """导出为 CSV 格式"""
        matrix = PermissionMatrix.generate_role_matrix()
        
        permissions = set()
        for role_perms in matrix.values():
            permissions.update(role_perms.keys())
        
        permissions = sorted(list(permissions))
        
        lines = ['Role,' + ','.join(permissions)]
        
        for role, perms in matrix.items():
            row = [role]
            for perm in permissions:
                row.append('Yes' if perms.get(perm, False) else 'No')
            lines.append(','.join(row))
        
        return '\n'.join(lines)


# 全局服务实例
permission_service = PermissionService()
