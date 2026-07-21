from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from backend.server import extensions
from backend.server.db_models import User, CtfGame, Team, Todo, Article, FileResource, ActivityLog
from functools import wraps

bp = Blueprint("admin", __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        try:
            uid = get_jwt_identity()
            if not uid:
                return jsonify({'msg': 'forbidden'}), 403
            try:
                uid_int = int(uid)
            except Exception:
                return jsonify({'msg': 'forbidden'}), 403
            u = User.query.get(uid_int)
            if not u or not getattr(u, 'is_admin', False):
                return jsonify({'msg': 'forbidden'}), 403
        except Exception:
            return jsonify({'msg': 'forbidden'}), 403
        return fn(*args, **kwargs)
    return wrapper

# ==================== 调试接口：设置/检查管理员 ====================
# 前端入口：@/services/admin/setup.js（AdminSetup 页面）

@bp.get("/check-current-user")
@jwt_required()
def check_current_user():
    """检查当前用户是否是管理员"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'nickname': user.nickname,
        'email': user.email,
        'is_admin': user.is_admin
    })


@bp.post("/set-admin-first-user")
@jwt_required()
def set_admin_first_user():
    """首次安装：将当前登录用户设为管理员（需 NEPU_SETUP_SECRET）"""
    from backend.server.security_helpers import allow_bootstrap_admin

    allowed, msg = allow_bootstrap_admin()
    if not allowed:
        return jsonify({'error': msg}), 403

    try:
        uid = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid identity'}), 401

    user = User.query.get(uid)
    if not user:
        return jsonify({'error': '没有用户'}), 404

    user.is_admin = True
    extensions.db.session.commit()

    return jsonify({
        'success': True,
        'message': f'用户 {user.nickname} (ID: {user.id}) 已设置为管理员',
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'email': user.email,
            'is_admin': user.is_admin
        }
    })


@bp.get("/search-user/<nickname>")
@admin_required
def search_user(nickname):
    """搜索用户（根据昵称）"""
    user = User.query.filter_by(nickname=nickname).first()
    if not user:
        return jsonify({'error': f'找不到昵称为 {nickname} 的用户'}), 404
    
    return jsonify({
        'id': user.id,
        'nickname': user.nickname,
        'email': user.email,
        'is_admin': user.is_admin
    })



def require_admin():
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return False
    user = User.query.get(uid_int)
    if not user or not getattr(user, 'is_admin', False):
        return False
    return True



def _games_gone():
    """/api/admin/games* CRUD 已迁至 /api/competitions/admin/*（stats/export 仍由 ctf_admin 提供）。"""
    body = {
        'code': 410,
        'msg': 'Gone: use /api/competitions/admin/* for game CRUD; stats/export remain at /api/admin/games/<id>/stats|export-scoreboard',
        'successor': '/api/competitions/admin/*',
    }
    resp = jsonify(body)
    resp.status_code = 410
    resp.headers['Deprecation'] = 'true'
    resp.headers['Link'] = '</api/competitions/admin/>; rel="successor-version"'
    return resp


@bp.get('/games')
@jwt_required()
def admin_list_games():
    return _games_gone()


@bp.put('/games/<int:gid>')
@jwt_required()
def admin_update_game(gid):
    return _games_gone()


@bp.put('/users/<int:uid>')
@admin_required
def admin_update_user(uid):
    """兼容旧客户端 PUT；字段语义与 PATCH /users/<id> 对齐。"""
    data = request.json or {}
    u = User.query.get_or_404(uid)
    if 'is_admin' in data:
        u.is_admin = bool(data['is_admin'])
    if 'team_id' in data:
        u.team_id = int(data['team_id']) if data['team_id'] else None
    if 'nickname' in data:
        u.nickname = data['nickname']
    if 'full_name' in data:
        u.full_name = data['full_name']
    extensions.db.session.add(u)
    extensions.db.session.commit()
    return jsonify(u.to_dict())

@bp.get('/teams')
@admin_required
def admin_list_teams():
    items = []
    for t in Team.query.order_by(Team.id.desc()).all():
        members = []
        for u in getattr(t, 'users', []):
            members.append({'id': u.id, 'email': u.email, 'nickname': u.nickname})
        items.append({'id': t.id, 'name': t.name, 'members': members})
    return jsonify({'items': items})

@bp.put('/teams/<int:tid>')
@admin_required
def admin_update_team(tid):
    data = request.json or {}
    t = Team.query.get_or_404(tid)
    if 'name' in data:
        t.name = data['name']
    extensions.db.session.add(t)
    extensions.db.session.commit()
    return jsonify({'id': t.id, 'name': t.name})

# 开发用 seed：仅在 DEBUG 模式允许
@bp.post('/seed')
def admin_seed():
    if not current_app.config.get('DEBUG', False):
        return jsonify({'msg': 'not allowed'}), 403
    game = CtfGame.query.filter_by(title='Seed CtfGame').first()
    if not game:
        game = CtfGame(title='Seed CtfGame', start_time=None, end_time=None, is_public=True)
        extensions.db.session.add(game)
        extensions.db.session.commit()
    if not Team.query.filter_by(name='SeedTeamA').first():
        t1 = Team(name='SeedTeamA')
        t2 = Team(name='SeedTeamB')
        extensions.db.session.add_all([t1, t2])
        extensions.db.session.commit()
        u1 = User(email='seed1@example.com', nickname='seed1', is_admin=False, team_id=t1.id)
        u1.set_password('password')
        u2 = User(email='seed2@example.com', nickname='seed2', is_admin=False, team_id=t2.id)
        u2.set_password('password')
        extensions.db.session.add_all([u1, u2])
    extensions.db.session.commit()
    return jsonify({'msg': 'seeded'})

# ==================== 用户管理（合并原重复 GET /users） ====================

@bp.get("/users")
@admin_required
def list_users():
    """获取用户列表（支持分页与 email/nickname/team_id 过滤）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    # 未传 page 且需要全量时：per_page 上限放宽（兼容旧 Admin 过滤面板）
    if request.args.get('page') is None and request.args.get('per_page') is None:
        if request.args.get('email') or request.args.get('nickname') or request.args.get('team_id'):
            per_page = min(request.args.get('per_page', 1000, type=int) or 1000, 1000)

    query = User.query
    email = request.args.get('email')
    nickname = request.args.get('nickname')
    team_id = request.args.get('team_id')
    if email:
        query = query.filter(User.email.contains(email))
    if nickname:
        query = query.filter(User.nickname.contains(nickname))
    if team_id:
        try:
            query = query.filter_by(team_id=int(team_id))
        except (TypeError, ValueError):
            pass

    total = query.count()
    users = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page).items

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
            'team_id': u.team_id,
            'created_at': u.created_at.isoformat() if u.created_at else None,
        } for u in users]
    })


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id):
    """更新用户信息或权限"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json() or {}
    
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    if 'nickname' in data:
        user.nickname = data['nickname']
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'team_id' in data:
        user.team_id = data['team_id'] if data['team_id'] else None
    
    extensions.db.session.commit()
    return jsonify({'success': True})


@bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    """删除用户及其关联数据（文章、资源、代办、提交、比赛等）"""
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
        
        # 删除用户的所有代办任务
        Todo.query.filter_by(user_id=user_id).delete()        
        # 5. 删除用户的参赛记录（user participation）
        from backend.server.db_models import CtfParticipatingUser
        CtfParticipatingUser.query.filter_by(user_id=user_id).delete()
        # 5. 删除与用户相关的活动日志
        ActivityLog.query.filter_by(actor_id=user_id).delete()
        
        # 6. 如果用户是某个文件的上传者，清理文件资源
        FileResource.query.filter_by(uploader_id=user_id).delete()
        
        # 7. 最后删除用户本身
        extensions.db.session.delete(user)
        extensions.db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        extensions.db.session.rollback()
        current_app.logger.error(f'删除用户 {user_id} 失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500


# ==================== 比赛管理（CRUD 已下线，避免与 ctf_admin / competitions 阴影） ====================

@bp.post("/games")
@admin_required
def create_game_admin():
    return _games_gone()


@bp.delete("/games/<int:game_id>")
@admin_required
def delete_game_admin(game_id):
    return _games_gone()


# ==================== 数据统计 ====================

@bp.get("/stats/dashboard")
@admin_required
def dashboard_stats():
    """获取仪表板统计数据"""
    user_count = User.query.count()
    game_count = CtfGame.query.count()
    article_count = Article.query.count()
    
    return jsonify({
        'users': user_count,
        'games': game_count,
        'articles': article_count
    })


@bp.get("/stats/users")
@admin_required
def user_stats():
    """用户活跃度统计"""
    user_count = User.query.count()
    return jsonify({
        'top_users': [],
        'total_users': user_count
    })


@bp.get("/stats/games")
@admin_required  
def game_stats():
    """比赛统计"""
    games = CtfGame.query.all()
    stats = []
    
    for game in games:
        stats.append({
            'game_id': game.id,
            'title': game.title
        })
    
    return jsonify({'items': stats})