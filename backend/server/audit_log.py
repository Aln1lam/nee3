"""
审计日志工具模块
记录用户的所有重要操作
"""
import json
from datetime import datetime
from flask import request, g, has_request_context
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.server.extensions import db
from backend.server.db_models import ActivityLog, User


def get_client_ip():
    """获取客户端真实IP"""
    if not has_request_context():
        return None
    # 支持代理情况
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def get_current_user():
    """获取当前登录用户"""
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid:
            return User.query.get(int(uid))
    except:
        pass
    return None


def log_activity(action, target_type=None, target_id=None, target_name=None, 
                 meta=None, status='success', actor=None):
    """
    记录操作日志
    
    Args:
        action: 操作类型 (login, logout, create, update, delete, view, export, etc.)
        target_type: 操作对象类型 (user, article, team, game, resource, etc.)
        target_id: 操作对象ID
        target_name: 操作对象名称/描述
        meta: 额外信息（字典或字符串）
        status: 操作状态 (success, failed)
        actor: 操作人User对象，不传则自动获取当前用户
    """
    try:
        # 获取操作人
        if actor is None:
            actor = get_current_user()
        
        actor_id = actor.id if actor else None
        actor_name = actor.nickname if actor else '系统'
        
        # 处理 meta
        if isinstance(meta, dict):
            meta_str = json.dumps(meta, ensure_ascii=False)
        else:
            meta_str = str(meta) if meta else None
        
        # 获取客户端信息
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')[:500] if has_request_context() else None
        
        # 对象类型中文映射
        target_labels = {
            'session': '会话',
            'user': '用户',
            'profile': '个人资料',
            'article': '文章',
            'team': '团队',
            'game': '竞赛',
            'resource': '资源',
            'announcement': '公告',
            'carousel': '轮播图',
            'todo': '代办',
            'scoreboard': '排行榜',
            'submission': '提交',
            'ctf': 'CTF',
            'system_config': '系统配置'
        }

        # 生成对非技术用户友好的描述（当调用方未提供可读的 target_name 时使用）
        human_msg = None
        try:
            parsed_meta = json.loads(meta_str) if meta_str else None
        except Exception:
            parsed_meta = None

        if action and 'todo' in action:
            # 特殊处理代办分发
            count = None
            recipients = None
            try:
                if parsed_meta and isinstance(parsed_meta, dict):
                    count = parsed_meta.get('count')
                    recipients = parsed_meta.get('recipients')
            except Exception:
                pass
            if recipients and isinstance(recipients, list) and len(recipients) > 0:
                names = [r.get('nickname') or r.get('email') or str(r.get('id')) for r in recipients]
                # 将 target_name 中的英文对象名替换为中文（如果存在）
                tn = target_name or ''
                try:
                    if isinstance(tn, str) and ':' in tn:
                        left, right = tn.split(':', 1)
                        left = left.strip()
                        right = right.strip()
                        if left in target_labels:
                            tn = f"{target_labels[left]}：{right}"
                except Exception:
                    pass
                human_msg = f"分发代办: \"{tn[:60]}\"，共 {len(names)} 人：{', '.join(names[:10])}"
            elif count is not None:
                human_msg = f"分发代办: \"{(target_name or '')[:60]}\"，共 {count} 人"

        if not human_msg:
            # 通用友好描述
            # 使用中文对象类型标签（若可用），并尝试把 target_name 中的前缀替换为中文
            display_target = target_labels.get(target_type, target_type or '对象')
            tn_display = target_name or target_id or ''
            try:
                if isinstance(tn_display, str) and ':' in tn_display:
                    left, right = tn_display.split(':', 1)
                    left = left.strip()
                    right = right.strip()
                    if left in target_labels:
                        tn_display = f"{target_labels[left]}：{right}"
            except Exception:
                pass

            if action == 'create':
                human_msg = f"创建 {display_target}：{tn_display}"
            elif action == 'update':
                human_msg = f"更新 {display_target}：{tn_display}"
            elif action == 'delete':
                human_msg = f"删除 {display_target}：{tn_display}"
            elif action == 'view':
                human_msg = f"查看 {display_target}：{tn_display}"
            elif action == 'login':
                human_msg = f"用户登录：{target_name or actor_name}"
            elif action == 'logout':
                human_msg = f"用户登出：{target_name or actor_name}"
            else:
                # 如果调用方已经传入 target_name，优先使用；否则组合 action 和 target_type
                if target_name:
                    human_msg = str(target_name)
                else:
                    human_msg = f"{action} {target_type or ''} {target_id or ''}".strip()

        # 创建日志记录
        log = ActivityLog(
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=human_msg,
            ip_address=ip_address,
            user_agent=user_agent,
            meta=meta_str,
            status=status,
            created_at=datetime.utcnow()
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    except Exception as e:
        # 日志记录失败不应影响正常业务
        print(f"[AuditLog] Failed to log activity: {e}")
        db.session.rollback()
        return None


# 便捷方法
def log_login(user, success=True, reason=None):
    """记录登录"""
    return log_activity(
        action='login',
        target_type='session',
        target_name=user.nickname if user else '未知用户',
        meta={'reason': reason} if reason else None,
        status='success' if success else 'failed',
        actor=user
    )


def log_logout(user):
    """记录登出"""
    return log_activity(
        action='logout',
        target_type='session',
        actor=user
    )


def log_register(user):
    """记录注册"""
    return log_activity(
        action='register',
        target_type='user',
        target_id=user.id,
        target_name=user.nickname,
        actor=user
    )


def log_create(target_type, target_id, target_name=None, meta=None):
    """记录创建操作"""
    return log_activity(
        action='create',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        meta=meta
    )


def log_update(target_type, target_id, target_name=None, meta=None):
    """记录更新操作"""
    return log_activity(
        action='update',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        meta=meta
    )


def log_delete(target_type, target_id, target_name=None, meta=None):
    """记录删除操作"""
    return log_activity(
        action='delete',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        meta=meta
    )


def log_view(target_type, target_id, target_name=None):
    """记录查看操作"""
    return log_activity(
        action='view',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name
    )


def log_export(target_type, meta=None):
    """记录导出操作"""
    return log_activity(
        action='export',
        target_type=target_type,
        meta=meta
    )


def log_admin_action(action, target_type, target_id=None, target_name=None, meta=None):
    """记录管理员操作"""
    return log_activity(
        action=f'admin_{action}',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        meta=meta
    )
