"""
平台级管理接口 - 用于管理整个 NEEPU 平台
包括用户管理、内容管理、系统配置、日志审计等
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from backend.server import extensions
from backend.server.extensions import db
from backend.server.db_models import User, Article, ActivityLog, Todo, FileResource, Team, MainAnnouncement, CarouselSlide, CtfParticipation, CtfParticipatingUser, CtfChallengeSubmission
from dotenv import set_key, find_dotenv
import os

bp = Blueprint("platform_admin", __name__, url_prefix="/api/admin/platform")


def platform_admin_required(fn):
    """平台管理员权限验证"""
    from functools import wraps
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user or not user.is_admin:
            return jsonify({'error': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ==================== 仪表盘统计 ====================

@bp.get("/dashboard")
@platform_admin_required
def get_dashboard():
    """获取平台仪表盘数据"""
    now = datetime.utcnow()
    
    # 用户统计
    total_users = User.query.count()
    new_users_7d = User.query.filter(
        User.created_at >= now - timedelta(days=7)
    ).count()
    new_users_30d = User.query.filter(
        User.created_at >= now - timedelta(days=30)
    ).count()
    admin_count = User.query.filter_by(is_admin=True).count()
    
    # 活跃用户（24小时内有活动的用户）
    active_users = db.session.query(func.count(func.distinct(ActivityLog.actor_id))).filter(
        ActivityLog.created_at >= now - timedelta(hours=24)
    ).scalar() or 0
    
    # 文章统计
    total_articles = Article.query.count()
    published_articles = Article.query.filter_by(status='published').count()
    draft_articles = Article.query.filter_by(status='draft').count()
    
    # 资源统计
    total_resources = FileResource.query.count()
    storage_bytes = db.session.query(func.sum(FileResource.size)).scalar() or 0
    storage_mb = storage_bytes / (1024 * 1024) if storage_bytes else 0
    
    # 团队统计
    total_teams = Team.query.count()
    
    # 7天用户增长趋势
    daily_new_users = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = User.query.filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        
        daily_new_users.append({
            'date': day_start.strftime('%m-%d'),
            'count': count
        })
    
    return jsonify({
        'users': {
            'total': total_users,
            'new_7d': new_users_7d,
            'new_30d': new_users_30d,
            'admins': admin_count,
            'active': active_users
        },
        'articles': {
            'total': total_articles,
            'published': published_articles,
            'draft': draft_articles
        },
        'resources': {
            'total': total_resources,
            'storage_bytes': storage_bytes,
            'storage_mb': round(storage_mb, 2)
        },
        'teams': {
            'total': total_teams
        },
        'trends': {
            'daily_new_users': daily_new_users
        }
    })


# ==================== 用户管理 ====================

@bp.get("/users")
@platform_admin_required
def list_users():
    """获取用户列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.nickname.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )
    
    total = query.count()
    users = query.paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'items': [{
            'id': u.id,
            'email': u.email,
            'nickname': u.nickname,
            'full_name': u.full_name,
            'is_admin': u.is_admin,
            'is_moderator': bool(getattr(u, 'is_moderator', False)),
            'team_id': u.team_id,
            'created_at': u.created_at.isoformat()
        } for u in users]
    })


@bp.patch("/users/<int:user_id>")
@platform_admin_required
def update_user(user_id):
    """编辑用户信息"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json() or {}
    
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    if 'is_moderator' in data:
        user.is_moderator = bool(data['is_moderator'])
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'email' in data:
        email = (data.get('email') or '').strip().lower()
        if not email or '@' not in email:
            return jsonify({'error': '邮箱格式无效'}), 400
        conflict = User.query.filter(User.email == email, User.id != user_id).first()
        if conflict:
            return jsonify({'error': '该邮箱已被其他账号使用'}), 409
        user.email = email
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'team_id' in data:
        user.team_id = data['team_id'] if data['team_id'] else None
    
    db.session.commit()
    return jsonify({'success': True})


@bp.delete("/users/<int:user_id>")
@platform_admin_required
def delete_user(user_id):
    """删除用户及其关联数据（文章、资源、代办等）"""
    import os
    from flask import current_app
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 1. 先删除用户的所有文章及其关联资源
        user_articles = Article.query.filter_by(author_id=user_id).all()
        for article in user_articles:
            # 清理文章关联的资源
            if article.resource_id:
                # 检查是否有其他文章引用该资源
                other_articles = Article.query.filter(
                    Article.resource_id == article.resource_id,
                    Article.id != article.id
                ).count()
                
                if other_articles == 0:
                    fr = FileResource.query.get(article.resource_id)
                    if fr:
                        try:
                            file_path = os.path.join(current_app.root_path, 'static', fr.url.lstrip('/'))
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            current_app.logger.warning(f'删除文件失败: {e}')
                        
                        try:
                            extensions.db.session.delete(fr)
                        except Exception as e:
                            current_app.logger.warning(f'删除资源记录失败: {e}')
            
            extensions.db.session.delete(article)
        
        # 3. 删除用户的所有代办任务
        Todo.query.filter_by(user_id=user_id).delete()
        
        # 4. 删除用户的参赛记录（user participation）
        CtfParticipatingUser.query.filter_by(user_id=user_id).delete()
        
        # 5. 删除用户的所有提交记录
        CtfChallengeSubmission.query.filter_by(user_id=user_id).delete()
        
        # 6. 删除用户的活动日志
        ActivityLog.query.filter_by(actor_id=user_id).delete()
        
        # 7. 如果用户是某个文件的上传者，清理文件资源
        FileResource.query.filter_by(uploader_id=user_id).delete()
        
        # 8. 删除用户本身
        extensions.db.session.delete(user)
        extensions.db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        extensions.db.session.rollback()
        current_app.logger.error(f'删除用户 {user_id} 失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': '删除失败'}), 500


# ==================== 环境变量管理 (仅限平台管理员) ====================


@bp.get('/env')
@platform_admin_required
def get_env_vars():
    """返回允许编辑的环境变量及其当前值"""
    # 白名单：仅允许通过前端编辑的键
    allowed = [
        'FRONTEND_URL', 'API_URL', 'NEEPU_SITE_NAME', 'NEEPU_SITE_DESCRIPTION',
        'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_SSL', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER', 'MAIL_SENDER_NAME',
        'NEEPU_ALLOW_REGISTRATION', 'NEEPU_ALLOW_TEAMS', 'NEEPU_ALLOW_GAMES', 'NEEPU_REQUIRE_EMAIL_VERIFICATION'
    ]
    res = {}
    for k in allowed:
        val = os.environ.get(k, '')
        if k == 'MAIL_PASSWORD' and val:
            res[k] = '******'
        else:
            res[k] = val
    return jsonify({'vars': res})


@bp.post('/env')
@platform_admin_required
def set_env_vars():
    """接收 JSON { updates: { KEY: VALUE } }，写入项目根目录的 .env 文件（覆盖或新增）"""
    data = request.get_json() or {}
    updates = data.get('updates') or {}
    if not isinstance(updates, dict) or not updates:
        return jsonify({'error': '无更新内容'}), 400

    dotenv_path = find_dotenv()
    if not dotenv_path:
        # fallback to project root .env
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env')

    written = {}
    try:
        # 使用 python-dotenv 的 set_key 来写入或更新
        for k, v in updates.items():
            # 仅允许更新白名单中的键
            if k not in ['FRONTEND_URL', 'API_URL', 'NEEPU_SITE_NAME', 'NEEPU_SITE_DESCRIPTION', 'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_SSL', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER', 'MAIL_SENDER_NAME', 'NEEPU_ALLOW_REGISTRATION', 'NEEPU_ALLOW_TEAMS', 'NEEPU_ALLOW_GAMES', 'NEEPU_REQUIRE_EMAIL_VERIFICATION']:
                continue
            if k == 'MAIL_PASSWORD' and str(v) == '******':
                continue
            # set_key 会在文件中更新或添加
            set_key(dotenv_path, k, str(v))
            written[k] = str(v)
            # 同时 update os.environ so subsequent reads reflect changes in this process
            os.environ[k] = str(v)
        return jsonify({'updated': written})
    except Exception as e:
        return jsonify({'error': '写入 .env 失败', 'details': str(e)}), 500
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500


# ==================== 内容管理 ====================

@bp.get("/articles")
@platform_admin_required
def list_articles():
    """获取文章列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '', type=str)
    
    query = Article.query
    if status:
        query = query.filter_by(status=status)
    
    total = query.count()
    articles = query.order_by(desc(Article.created_at)).paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'items': [{
            'id': a.id,
            'title': a.title,
            'slug': getattr(a, 'slug', None),
            'status': a.status,
            'author_id': a.author_id,
            'author_name': User.query.get(a.author_id).nickname if a.author_id and User.query.get(a.author_id) else '未知作者',
            'category': getattr(a, 'category', None),
            'created_at': a.created_at.isoformat(),
            'published_at': a.published_at.isoformat() if a.published_at else None
        } for a in articles]
    })


@bp.patch("/articles/<int:article_id>")
@platform_admin_required
def update_article(article_id):
    """编辑文章"""
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'error': '文章不存在'}), 404
    
    data = request.get_json() or {}
    
    if 'status' in data:
        article.status = data['status']
        if data['status'] == 'published' and not article.published_at:
            article.published_at = datetime.utcnow()
    
    if 'title' in data:
        article.title = data['title']
    
    db.session.commit()
    return jsonify({'success': True})


@bp.delete("/articles/<int:article_id>")
@platform_admin_required
def delete_article(article_id):
    """删除文章及其关联资源"""
    import os
    from flask import current_app
    
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'error': '文章不存在'}), 404
    
    # 删除关联的图片（如果没有其他文章引用）
    if article.resource_id:
        # 检查是否有其他文章引用该图片
        other_articles = Article.query.filter(
            Article.resource_id == article.resource_id,
            Article.id != article_id
        ).count()
        
        if other_articles == 0:
            # 没有其他文章引用，删除图片文件和数据库记录
            fr = FileResource.query.get(article.resource_id)
            if fr:
                # 删除物理文件
                try:
                    file_path = os.path.join(current_app.root_path, 'static', fr.url.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    current_app.logger.warning(f'删除文件失败: {e}')
                
                # 删除数据库记录
                try:
                    extensions.db.session.delete(fr)
                except Exception as e:
                    current_app.logger.warning(f'删除资源记录失败: {e}')
    
    extensions.db.session.delete(article)
    extensions.db.session.commit()
    
    return jsonify({'success': True})


# ==================== 系统日志 ====================

@bp.get("/logs")
@platform_admin_required
def get_logs():
    """获取系统活动日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action_type = request.args.get('action', '', type=str)
    target_type = request.args.get('target', '', type=str)
    search = request.args.get('search', '', type=str)
    
    query = ActivityLog.query
    if action_type:
        query = query.filter(ActivityLog.action.like(f'%{action_type}%'))
    if target_type:
        query = query.filter_by(target_type=target_type)
    if search:
        query = query.filter(
            (ActivityLog.actor_name.like(f'%{search}%')) |
            (ActivityLog.target_name.like(f'%{search}%')) |
            (ActivityLog.ip_address.like(f'%{search}%'))
        )
    
    total = query.count()
    logs = query.order_by(desc(ActivityLog.created_at)).paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'items': [log.to_dict() for log in logs]
    })


@bp.delete('/logs/<int:log_id>')
@platform_admin_required
def delete_log(log_id):
    """删除单条日志记录"""
    log = ActivityLog.query.get(log_id)
    if not log:
        return jsonify({'error': '日志不存在'}), 404
    try:
        db.session.delete(log)
        db.session.commit()
        return jsonify({'success': True, 'deleted_id': log_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@bp.post('/logs/delete-by-months')
@platform_admin_required
def delete_logs_by_months():
    """按月份区间删除日志。

    接收 JSON: { "start_month": "YYYY-MM", "end_month": "YYYY-MM", "dry_run": false }
    将删除开始月份的第一天 00:00 到结束月份的最后一日 23:59:59 之间的所有日志。
    返回删除数量或匹配数量（dry_run=true 时）。
    """
    data = request.get_json() or {}
    start_month = data.get('start_month')
    end_month = data.get('end_month')
    dry_run = bool(data.get('dry_run', False))

    if not start_month or not end_month:
        return jsonify({'error': '需要 start_month 和 end_month，格式 YYYY-MM'}), 400

    try:
        start_dt = datetime.fromisoformat(start_month + '-01')
        # compute first day of the month after end_month
        y, m = map(int, end_month.split('-'))
        if m == 12:
            next_month = datetime(y + 1, 1, 1)
        else:
            next_month = datetime(y, m + 1, 1)
    except Exception:
        return jsonify({'error': '日期格式错误，须为 YYYY-MM'}), 400

    q = ActivityLog.query.filter(ActivityLog.created_at >= start_dt, ActivityLog.created_at < next_month)
    total = q.count()
    if dry_run:
        # 返回匹配数量和示例
        sample = q.order_by(ActivityLog.created_at.desc()).limit(5).all()
        return jsonify({'matched': total, 'sample': [s.to_dict() for s in sample]})

    try:
        # 批量删除以防一次性大事务，删除按 id 分页
        batch = 500
        deleted = 0
        while True:
            ids = [r.id for r in q.with_entities(ActivityLog.id).limit(batch).all()]
            if not ids:
                break
            db.session.query(ActivityLog).filter(ActivityLog.id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()
            deleted += len(ids)
        return jsonify({'deleted': deleted})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@bp.get("/logs/stats")
@platform_admin_required
def get_logs_stats():
    """获取日志统计信息"""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    today_count = ActivityLog.query.filter(ActivityLog.created_at >= today_start).count()
    week_count = ActivityLog.query.filter(ActivityLog.created_at >= week_start).count()
    month_count = ActivityLog.query.filter(ActivityLog.created_at >= month_start).count()
    
    # 按操作类型统计
    from sqlalchemy import func
    action_stats = db.session.query(
        ActivityLog.action, func.count(ActivityLog.id)
    ).group_by(ActivityLog.action).all()
    
    return jsonify({
        'today_count': today_count,
        'week_count': week_count,
        'month_count': month_count,
        'action_stats': {action: count for action, count in action_stats}
    })


@bp.get('/logs/months')
@platform_admin_required
def get_logs_months():
    """返回可选的月份列表（从最早日志所在月到当前月），用于前端下拉选择。

    返回 JSON: { 'months': ['YYYY-MM', ...], 'earliest': 'YYYY-MM', 'latest': 'YYYY-MM' }
    """
    from sqlalchemy import func
    min_dt, max_dt = db.session.query(func.min(ActivityLog.created_at), func.max(ActivityLog.created_at)).first()
    if not min_dt:
        return jsonify({'months': [], 'earliest': None, 'latest': None})

    def month_iter(start, end):
        cur = start.replace(day=1)
        while cur <= end:
            yield cur.strftime('%Y-%m')
            # move to next month
            y = cur.year + (cur.month // 12)
            m = (cur.month % 12) + 1
            cur = cur.replace(year=y, month=m, day=1)

    start_month = min_dt.replace(day=1)
    end_month = max_dt.replace(day=1)
    months = list(month_iter(start_month, end_month))
    return jsonify({'months': months, 'earliest': months[0] if months else None, 'latest': months[-1] if months else None})


# ==================== 系统配置 ====================

@bp.get("/config")
@platform_admin_required
def get_config():
    """获取系统配置"""
    from backend.server.db_models import SystemConfig
    return jsonify(SystemConfig.get_all())


@bp.patch("/config")
@platform_admin_required
def update_config():
    """更新系统配置"""
    import json
    from backend.server.db_models import SystemConfig
    from backend.server.audit_log import log_activity
    
    data = request.get_json() or {}
    
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            value = 'true' if value else 'false'
        elif value is not None and not isinstance(value, str):
            value = str(value)
        SystemConfig.set(key, value)
    
    log_activity('update', 'system_config', meta={'keys': list(data.keys())})
    
    return jsonify({'success': True, 'config': SystemConfig.get_all()})


@bp.get("/config/ui")
@platform_admin_required
def get_ui_config():
    """获取平台 UI 配置（结构化 JSON）"""
    from backend.services.platform_config_service import load_platform_ui_config, get_default_platform_config
    return jsonify({
        'current': load_platform_ui_config(),
        'defaults': get_default_platform_config(),
    })


@bp.patch("/config/ui")
@platform_admin_required
def update_ui_config():
    """更新平台 UI 配置（结构化 JSON）"""
    import json
    from backend.server.db_models import SystemConfig
    from backend.server.audit_log import log_activity
    from backend.services.platform_config_service import JSON_CONFIG_KEYS, TEXT_CONFIG_KEYS

    data = request.get_json() or {}
    allowed = set(JSON_CONFIG_KEYS.keys()) | set(TEXT_CONFIG_KEYS.keys())
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return jsonify({'error': '无有效配置项'}), 400

    for key, value in payload.items():
        if key in JSON_CONFIG_KEYS:
            stored = json.dumps(value, ensure_ascii=False)
        else:
            stored = '' if value is None else str(value)
        SystemConfig.set(key, stored)

    log_activity('update', 'platform_ui_config', meta={'keys': list(payload.keys())})
    try:
        from backend.server.cache_invalidation import invalidate_platform_info_cache
        invalidate_platform_info_cache()
    except Exception:
        pass
    from backend.services.platform_config_service import load_platform_ui_config
    return jsonify({'success': True, 'config': load_platform_ui_config()})


@bp.post("/config/init")
@platform_admin_required
def init_config():
    """初始化默认配置"""
    from backend.server.db_models import SystemConfig
    SystemConfig.init_defaults()
    return jsonify({'success': True, 'message': '配置初始化完成'})


@bp.post("/test-email")
@platform_admin_required
def test_email():
    """发送测试邮件"""
    from backend.server.email_service import email_service
    
    data = request.get_json() or {}
    email = data.get('email')
    
    if not email:
        return jsonify({'msg': '请提供邮箱地址'}), 400
    
    try:
        email_service.send_email(
            to_email=email,
            subject='NEEPU CTF 测试邮件',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #00c48c;">✅ 邮件配置测试成功</h2>
                <p>这是一封来自 NEEPU CTF 平台的测试邮件。</p>
                <p>如果你收到这封邮件，说明邮件服务配置正确！</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #888; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
            </div>
            '''
        )
        return jsonify({'success': True, 'message': '测试邮件已发送'})
    except Exception as e:
        return jsonify({'msg': f'发送失败: {str(e)}'}), 500


# ==================== 统计数据 ====================

@bp.get("/stats/users-trend")
@platform_admin_required
def users_trend():
    """用户增长趋势（30天）"""
    now = datetime.utcnow()
    data = []
    
    for i in range(29, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = User.query.filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        
        data.append({
            'date': day_start.strftime('%m-%d'),
            'count': count
        })
    
    return jsonify({'data': data})


@bp.get("/stats/articles-distribution")
@platform_admin_required
def articles_distribution():
    """文章状态分布"""
    published = Article.query.filter_by(status='published').count()
    draft = Article.query.filter_by(status='draft').count()
    
    return jsonify({
        'published': published,
        'draft': draft
    })


@bp.get("/stats/top-active-users")
@platform_admin_required
def top_active_users():
    """活跃用户排行（根据 Flag 提交次数）"""
    top_users = db.session.query(
        User.id, User.nickname,
        func.count(CtfChallengeSubmission.id).label('submission_count')
    ).join(CtfChallengeSubmission, User.id == CtfChallengeSubmission.user_id).group_by(
        User.id, User.nickname
    ).order_by(desc(func.count(CtfChallengeSubmission.id))).limit(10).all()
    
    return jsonify({
        'items': [{
            'user_id': u[0],
            'nickname': u[1],
            'submission_count': u[2]
        } for u in top_users]
    })


# ==================== 公告管理 ====================

@bp.get("/announcements")
@platform_admin_required
def get_announcements():
    """获取所有公告"""
    announcements = MainAnnouncement.query.order_by(desc(MainAnnouncement.created_at)).all()
    return jsonify([a.to_dict() for a in announcements])


@bp.post("/announcements")
@platform_admin_required
def create_announcement():
    """创建新公告"""
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    user_id = int(get_jwt_identity())
    announcement = MainAnnouncement(
        title=title,
        content=content,
        creator_id=user_id,
        is_active=True
    )
    db.session.add(announcement)
    db.session.commit()
    
    return jsonify(announcement.to_dict()), 201


@bp.patch("/announcements/<int:announcement_id>")
@platform_admin_required
def update_announcement(announcement_id):
    """更新公告"""
    announcement = MainAnnouncement.query.get(announcement_id)
    if not announcement:
        return jsonify({'error': '公告不存在'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        announcement.title = data['title'].strip()
    if 'content' in data:
        announcement.content = data['content'].strip()
    if 'is_active' in data:
        announcement.is_active = bool(data['is_active'])
    
    announcement.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(announcement.to_dict())


@bp.delete("/announcements/<int:announcement_id>")
@platform_admin_required
def delete_announcement(announcement_id):
    """删除公告"""
    announcement = MainAnnouncement.query.get(announcement_id)
    if not announcement:
        return jsonify({'error': '公告不存在'}), 404
    
    db.session.delete(announcement)
    db.session.commit()
    
    return jsonify({'message': '公告已删除'})


# ==================== 轮播图管理 ====================

@bp.get("/carousel")
@platform_admin_required
def get_carousel_slides():
    """获取所有轮播图（管理员）"""
    from backend.services.carousel_service import carousel_slide_to_dict, bind_slide_resource
    slides = CarouselSlide.query.order_by(CarouselSlide.sort_order, CarouselSlide.id).all()
    changed = False
    for slide in slides:
        if slide.image_url and not slide.resource_id:
            bind_slide_resource(slide, slide.image_url)
            changed = True
    if changed:
        db.session.commit()
    return jsonify([carousel_slide_to_dict(s, admin=True) for s in slides])


@bp.post("/carousel")
@platform_admin_required
def create_carousel_slide():
    """创建轮播图"""
    from backend.services.carousel_service import (
        bind_slide_resource,
        carousel_slide_to_dict,
        image_file_exists,
        normalize_carousel_image_url,
    )

    data = request.get_json() or {}
    image_url = (data.get('image_url') or '').strip()

    if not image_url:
        return jsonify({'error': '图片地址不能为空'}), 400

    normalized = normalize_carousel_image_url(image_url)
    if not image_file_exists(normalized):
        return jsonify({'error': '图片文件不存在，请先在媒体库上传'}), 400

    max_order = db.session.query(func.max(CarouselSlide.sort_order)).scalar() or 0

    slide = CarouselSlide(
        title=(data.get('title') or '').strip() or None,
        description=(data.get('description') or '').strip() or None,
        image_url=normalized,
        link_url=(data.get('link_url') or '').strip() or None,
        sort_order=data.get('sort_order', max_order + 1),
        is_active=data.get('is_active', True),
    )
    bind_slide_resource(slide, normalized, data.get('resource_id'))
    db.session.add(slide)
    db.session.commit()

    return jsonify(carousel_slide_to_dict(slide, admin=True)), 201


@bp.patch("/carousel/<int:slide_id>")
@platform_admin_required
def update_carousel_slide(slide_id):
    """更新轮播图"""
    from backend.services.carousel_service import (
        bind_slide_resource,
        carousel_slide_to_dict,
        image_file_exists,
        normalize_carousel_image_url,
    )

    slide = CarouselSlide.query.get(slide_id)
    if not slide:
        return jsonify({'error': '轮播图不存在'}), 404

    data = request.get_json() or {}

    if 'title' in data:
        slide.title = data['title'].strip() if data['title'] else None
    if 'description' in data:
        slide.description = data['description'].strip() if data['description'] else None
    if 'link_url' in data:
        slide.link_url = data['link_url'].strip() if data['link_url'] else None
    if 'sort_order' in data:
        slide.sort_order = data['sort_order']
    if 'is_active' in data:
        slide.is_active = data['is_active']
    if 'image_url' in data:
        normalized = normalize_carousel_image_url(data['image_url'])
        if not image_file_exists(normalized):
            return jsonify({'error': '图片文件不存在，请重新上传'}), 400
        bind_slide_resource(slide, normalized, data.get('resource_id'))
    elif 'resource_id' in data and data['resource_id']:
        bind_slide_resource(slide, slide.image_url, data['resource_id'])

    db.session.commit()
    return jsonify(carousel_slide_to_dict(slide, admin=True))


@bp.delete("/carousel/<int:slide_id>")
@platform_admin_required
def delete_carousel_slide(slide_id):
    """删除轮播图"""
    slide = CarouselSlide.query.get(slide_id)
    if not slide:
        return jsonify({'error': '轮播图不存在'}), 404

    db.session.delete(slide)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@bp.post("/distribute-todos")
@platform_admin_required
def distribute_todos():
    """批量向用户分发待办事项"""
    import json
    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "待办内容不能为空"}), 400
    if not isinstance(user_ids, list) or not user_ids:
        return jsonify({"error": "请选择至少一个用户"}), 400

    created = 0
    recipients = []
    for raw_id in user_ids:
        try:
            uid = int(raw_id)
        except (TypeError, ValueError):
            continue
        user = User.query.get(uid)
        if not user:
            continue
        db.session.add(Todo(text=text, user_id=uid, done=False))
        created += 1
        recipients.append(user.nickname or user.username or str(uid))

    if created == 0:
        return jsonify({"error": "没有有效用户"}), 400

    actor_id = None
    try:
        actor_id = int(get_jwt_identity())
    except Exception:
        pass
    actor = User.query.get(actor_id) if actor_id else None
    db.session.add(ActivityLog(
        actor_id=actor_id,
        actor_name=(actor.nickname or actor.username) if actor else "admin",
        action="distribute_todos",
        target_type="todo",
        target_name=text[:200],
        meta=json.dumps({"count": created, "text": text, "recipients": recipients[:50]}, ensure_ascii=False),
        status="success",
    ))
    db.session.commit()
    return jsonify({"message": f"已向 {created} 名用户分发待办", "created": created})

