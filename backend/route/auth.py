from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
import backend.server.extensions as extensions
from backend.server.db_models import User, Email, RegistratingUser
from werkzeug.utils import secure_filename
import os
from hashlib import md5
from PIL import Image
import io
from datetime import datetime, timedelta
from backend.server.email_service import email_service, generate_token
from backend.server.audit_log import log_login, log_logout, log_register, log_update, log_activity
from backend.middleware_refactored import login_rate_limit, rate_limit

bp = Blueprint("auth", __name__)


@bp.post("/register")
@rate_limit(max_requests=10, window_seconds=300, error_message="注册请求过于频繁，请稍后再试")
def register():
    """注册 - 先发送验证邮件，验证通过后才创建用户"""
    from backend.server.db_models import SystemConfig
    allow = SystemConfig.query.filter_by(key='allow_registration').first()
    if allow and str(allow.value).lower() in ('false', '0', 'no'):
        return {"msg": "平台当前已关闭注册"}, 403

    data = request.get_json() or {}
    email, password, nickname = data.get("email"), data.get("password"), data.get("nickname")
    username = data.get("username")  # 可选

    if not all([email, password, nickname]):
        return {"msg": "邮箱、密码和昵称为必填项"}, 400

    if len(password) < 8:
        return {"msg": "密码至少 8 位"}, 400

    from backend.server.security_helpers import verify_captcha_required
    ok, msg = verify_captcha_required(data)
    if not ok:
        return {"msg": msg}, 400
    
    # 检查邮箱是否已被正式注册
    if User.query.filter_by(email=email).first():
        return {"msg": "该邮箱已被注册"}, 409
    if username and User.query.filter_by(username=username).first():
        return {"msg": "该用户名已被使用"}, 409
    
    
    # 删除该邮箱之前的待验证记录（允许重新注册）
    RegistratingUser.query.filter_by(email=email).delete()
    
    # 创建待验证的注册记录（不是真正的用户）
    token = generate_token()
    pending = RegistratingUser(
        email=email,
        nickname=nickname,
        username=username if username else None,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    pending.set_password(password)
    extensions.db.session.add(pending)
    extensions.db.session.commit()
    
    # 发送验证邮件
    try:
        email_service.send_verification_email(email, token, nickname)
    except Exception as e:
        current_app.logger.warning(f"发送验证邮件失败: {e}")
        return {"msg": "发送验证邮件失败，请稍后重试"}, 500
    
    return {"msg": "验证邮件已发送，请查收邮箱完成注册", "need_verify": True}, 200


@bp.post("/verify-email")
def verify_email():
    """验证邮箱 - 验证通过后创建真正的用户"""
    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return {"msg": "missing token"}, 400
    
    # 先检查是否是待注册验证
    pending = RegistratingUser.query.filter_by(token=token).first()
    if pending:
        if not pending.is_valid():
            extensions.db.session.delete(pending)
            extensions.db.session.commit()
            return {"msg": "验证链接已过期，请重新注册"}, 400
        
        # 再次检查邮箱是否已被注册（防止并发）
        if User.query.filter_by(email=pending.email).first():
            extensions.db.session.delete(pending)
            extensions.db.session.commit()
            return {"msg": "该邮箱已被注册"}, 409
        
        # 创建真正的用户
        user = User(
            email=pending.email,
            nickname=pending.nickname,
            username=pending.username,
            password_hash=pending.password_hash,  # 直接使用已加密的密码
            email_verified=True  # 已验证
        )
        extensions.db.session.add(user)
        extensions.db.session.delete(pending)
        extensions.db.session.commit()
        
        # 记录注册日志
        log_register(user)
        
        return {"msg": "注册成功！", "email": user.email}
    
    # 如果不是待注册验证，检查是否是已有用户的邮箱验证
    email_token = Email.query.filter_by(token=token, token_type='verify_email').first()
    if not email_token:
        return {"msg": "无效的验证链接"}, 400
    
    if not email_token.is_valid():
        return {"msg": "验证链接已过期"}, 400
    
    user = User.query.get(email_token.user_id)
    if not user:
        return {"msg": "用户不存在"}, 404
    
    user.email_verified = True
    email_token.used = True
    extensions.db.session.commit()
    
    return {"msg": "邮箱验证成功！", "email": user.email}


@bp.post("/resend-verification")
def resend_verification():
    """重新发送验证邮件"""
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return {"msg": "missing email"}, 400
    
    # 先检查是否有待验证的注册
    pending = RegistratingUser.query.filter_by(email=email).first()
    if pending:
        # 检查是否频繁请求（1分钟内）
        if (datetime.utcnow() - pending.created_at).seconds < 60:
            return {"msg": "请稍后再试"}, 429
        
        # 生成新token
        new_token = generate_token()
        pending.token = new_token
        pending.expires_at = datetime.utcnow() + timedelta(hours=24)
        pending.created_at = datetime.utcnow()
        extensions.db.session.commit()
        
        email_service.send_verification_email(email, new_token, pending.nickname)
        return {"msg": "验证邮件已重新发送"}
    
    # 检查是否是已注册但未验证的用户
    user = User.query.filter_by(email=email).first()
    if not user:
        return {"msg": "未找到该邮箱的注册信息"}, 404
    
    if user.email_verified:
        return {"msg": "该邮箱已验证"}, 400
    
    # 检查是否频繁请求（1分钟内）
    recent_token = Email.query.filter_by(
        user_id=user.id, 
        token_type='verify_email',
        used=False
    ).order_by(Email.created_at.desc()).first()
    
    if recent_token and (datetime.utcnow() - recent_token.created_at).seconds < 60:
        return {"msg": "请稍后再试"}, 429
    
    # 生成新token并发送
    token = generate_token()
    email_token = Email(
        user_id=user.id,
        token=token,
        token_type='verify_email',
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    extensions.db.session.add(email_token)
    extensions.db.session.commit()
    email_service.send_verification_email(email, token, user.nickname)
    
    return {"msg": "验证邮件已重新发送"}


@bp.post("/forgot-password")
@rate_limit(max_requests=5, window_seconds=300, error_message="请求过于频繁，请稍后再试")
def forgot_password():
    """忘记密码 - 发送重置链接"""
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return {"msg": "missing email"}, 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        # 为了安全，不透露用户是否存在
        return {"msg": "ok"}
    
    # 检查是否频繁请求（1分钟内）
    recent_token = Email.query.filter_by(
        user_id=user.id, 
        token_type='reset_password',
        used=False
    ).order_by(Email.created_at.desc()).first()
    
    if recent_token and (datetime.utcnow() - recent_token.created_at).seconds < 60:
        return {"msg": "ok"}  # 不透露是否频繁
    
    # 生成重置token
    token = generate_token()
    email_token = Email(
        user_id=user.id,
        token=token,
        token_type='reset_password',
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    extensions.db.session.add(email_token)
    extensions.db.session.commit()
    email_service.send_password_reset_email(email, token, user.nickname)
    
    return {"msg": "ok"}


@bp.post("/reset-password")
def reset_password():
    """重置密码"""
    data = request.get_json() or {}
    token = data.get("token")
    new_password = data.get("password")
    
    if not token or not new_password:
        return {"msg": "missing fields"}, 400
    
    if len(new_password) < 6:
        return {"msg": "password too short"}, 400
    
    email_token = Email.query.filter_by(token=token, token_type='reset_password').first()
    if not email_token:
        return {"msg": "invalid token"}, 400
    
    if not email_token.is_valid():
        return {"msg": "token expired"}, 400
    
    user = User.query.get(email_token.user_id)
    if not user:
        return {"msg": "user not found"}, 404
    
    user.set_password(new_password)
    email_token.used = True
    extensions.db.session.commit()
    
    return {"msg": "ok"}


@bp.post("/login")
@login_rate_limit()
def login():
    data = request.get_json() or {}
    account = data.get("account") or data.get("email")  # 兼容旧字段名
    password = data.get("password")
    
    if not account or not password:
        return {"msg": "请输入账号和密码"}, 400

    from backend.server.security_helpers import verify_captcha_required
    ok, msg = verify_captcha_required(data)
    if not ok:
        return {"msg": msg}, 400

    # 支持用户名、邮箱、昵称三种方式登录
    user = None
    # 尝试邮箱匹配
    if '@' in account:
        user = User.query.filter_by(email=account).first()
    # 尝试用户名匹配
    if not user:
        user = User.query.filter_by(username=account).first()
    # 尝试昵称匹配
    if not user:
        user = User.query.filter_by(nickname=account).first()
    # 如果还没找到，再尝试邮箱与用户名和昵称（已尝试过邮箱/用户名），最后再尝试昵称匹配
    if not user:
        user = User.query.filter_by(nickname=account).first()
    
    if not user or not user.verify_password(password):
        # 记录失败登录
        log_activity('login', 'session', target_name=account, status='failed', meta={'reason': '账号或密码错误'})
        return {"msg": "账号或密码错误"}, 401
    
    # 记录成功登录
    log_login(user, success=True)
    
    # 使用字符串 identity，避免底层 JWT 库对 sub 类型的限制
    token = create_access_token(identity=str(user.id))
    resp = make_response(jsonify({"user": user.to_dict()}))
    set_access_cookies(resp, token)
    return resp


@bp.post("/logout")
@jwt_required(optional=True)
def logout():
    """注销并清除 HttpOnly 会话 Cookie"""
    uid = get_jwt_identity()
    if uid:
        try:
            u = User.query.get(int(uid))
            if u:
                log_logout(u)
        except Exception:
            pass
    resp = make_response(jsonify({"msg": "ok"}))
    unset_jwt_cookies(resp)
    return resp


@bp.get('/me')
@jwt_required(optional=True)
def me():
    uid = get_jwt_identity()
    if not uid:
        return jsonify({'msg':'anonymous'}), 401
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({'msg':'invalid token identity'}), 400
    u = User.query.get(uid_int)
    if not u:
        return jsonify({'msg':'not found'}), 404
    return jsonify(u.to_dict())


@bp.put('/profile')
@jwt_required()
def update_profile():
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({'msg':'invalid identity'}), 400
    u = User.query.get_or_404(uid_int)
    
    # Handle form fields (both JSON and form data)
    if request.is_json:
        data = request.get_json() or {}
    else:
        # For multipart/form-data, read from form
        data = request.form.to_dict() if request.form else {}
    
    # Update text fields
    for k in ('nickname','full_name','class_name','direction','bio','signature'):
        if k in data and data[k]:
            setattr(u, k, data.get(k))
    
    # 更新用户名（需要检查唯一性）
    if 'username' in data:
        new_username = data.get('username')
        if new_username:
            existing = User.query.filter(User.username == new_username, User.id != uid_int).first()
            if existing:
                return jsonify({'msg': '该用户名已被使用'}), 409
            u.username = new_username
        else:
            u.username = None  # 允许清空
    
    if 'avatar' in request.files:
        try:
            from backend.server.db_models import FileResource
            
            file = request.files['avatar']
            if file and file.filename:
                # Validate file type
                allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                ext = file.filename.lower().split('.')[-1]
                if ext not in allowed_ext:
                    return {'msg': 'invalid file type'}, 400
                
                # Process image
                img = Image.open(file.stream)
                # Resize to max 500x500
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                
                # Create filename
                import time
                filename = f"avatar_{uid_int}_{md5(str(time.time()).encode()).hexdigest()[:8]}.png"
                # 使用正确的绝对路径
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                img.save(filepath, 'PNG')
                
                # Save relative path to db
                avatar_url = f'/static/uploads/{filename}'
                u.avatar = avatar_url
                
                # 删除旧头像的FileResource记录（如果存在）
                if u.avatar_resource_id:
                    try:
                        old_resource = FileResource.query.get(u.avatar_resource_id)
                        if old_resource:
                            # 先清除外键引用，再删除资源记录
                            u.avatar_resource_id = None
                            extensions.db.session.delete(old_resource)
                    except Exception as e:
                        current_app.logger.warning(f"删除旧头像资源记录失败: {e}")
                        # 如果删除失败，回滚事务以清除 pending 状态
                        extensions.db.session.rollback()
                        u.avatar_resource_id = None
                
                # 创建新的FileResource记录
                try:
                    file_size = os.path.getsize(filepath)
                    fr = FileResource(
                        filename=filename,
                        path=filepath,
                        url=avatar_url,
                        mime_type='image/png',
                        size=file_size,
                        uploader_id=uid_int,
                        purpose='avatar',
                        entity_type='user',
                        entity_id=uid_int
                    )
                    extensions.db.session.add(fr)
                    extensions.db.session.flush()  # 获取ID
                    u.avatar_resource_id = fr.id
                    print(f"Avatar saved: {filepath} -> {u.avatar}, resource_id={fr.id}")
                except Exception as e:
                    print(f"FileResource creation error: {e}")
                    current_app.logger.warning(f"创建头像FileResource记录失败: {e}")
        except Exception as e:
            print(f"Avatar upload error: {e}")
            import traceback
            traceback.print_exc()
            return {'msg': 'avatar upload failed'}, 400
    
    extensions.db.session.add(u)
    extensions.db.session.commit()
    
    # 记录资料更新日志
    log_update('profile', u.id, u.nickname)
    
    return jsonify({'msg':'ok','user': u.to_dict()})


def _public_user_dict(u):
    """公开用户信息（不含敏感字段）"""
    return {
        'id': u.id,
        'username': u.username,
        'nickname': u.nickname,
        'avatar': u.avatar,
        'school': u.school,
        'email_verified': bool(u.email_verified),
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }


@bp.post('/change-password')
@jwt_required()
def change_password():
    """已登录用户修改密码"""
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({'msg': 'invalid identity'}), 400

    data = request.get_json() or {}
    old_password = data.get('old_password') or data.get('current_password')
    new_password = data.get('new_password') or data.get('password')

    if not old_password or not new_password:
        return jsonify({'msg': '请填写当前密码和新密码'}), 400
    if len(new_password) < 8 or len(new_password) > 40:
        return jsonify({'msg': '新密码长度需 8-40 位'}), 400
    if not any(c.islower() for c in new_password) or not any(c.isupper() for c in new_password) or not any(c.isdigit() for c in new_password):
        return jsonify({'msg': '新密码需包含大小写字母和数字'}), 400

    u = User.query.get_or_404(uid_int)
    if not u.verify_password(old_password):
        return jsonify({'msg': '当前密码不正确'}), 403

    u.set_password(new_password)
    extensions.db.session.commit()
    log_update('password', u.id, u.nickname)
    return jsonify({'msg': '密码已更新'})


@bp.get('/users')
def list_users():
    """公开用户列表/搜索"""
    from backend.server.db_models import CtfParticipatingUser, CtfChallengeSubmission, Team
    q = (request.args.get('q') or '').strip()
    query = User.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            (User.nickname.like(like)) | (User.username.like(like))
        )
    users = query.order_by(User.created_at.desc()).limit(50).all()
    return jsonify({'users': [_public_user_dict(u) for u in users]})


@bp.get('/users/<int:user_id>')
def public_user_profile(user_id):
    """用户公开主页"""
    from backend.server.db_models import (
        CtfParticipatingUser, CtfChallengeSubmission, CtfGame, CtfChallenge, Team,
    )
    u = User.query.get(user_id)
    if not u:
        return jsonify({'msg': '用户不存在'}), 404

    participations_raw = (
        CtfParticipatingUser.query.filter_by(user_id=user_id)
        .order_by(CtfParticipatingUser.joined_at.desc())
        .limit(20)
        .all()
    )
    participations = []
    for p in participations_raw:
        game = CtfGame.query.get(p.game_id)
        team = Team.query.get(p.team_id) if p.team_id else None
        participations.append({
            'id': p.id,
            'game_id': p.game_id,
            'game_title': game.title if game else '未知赛事',
            'team_name': team.name if team else None,
            'joined_at': p.joined_at.isoformat() if p.joined_at else None,
        })

    correct_subs = CtfChallengeSubmission.query.filter_by(
        user_id=user_id, is_correct=True
    ).all()
    solves = len(correct_subs)

    teams = 1 if u.team_id else 0

    category_map = {}
    for sub in correct_subs:
        ch = CtfChallenge.query.get(sub.challenge_id)
        cat = (ch.category if ch else None) or '其他'
        category_map[cat] = category_map.get(cat, 0) + 1
    category_stats = [
        {'category': k, 'count': v}
        for k, v in sorted(category_map.items(), key=lambda x: -x[1])
    ]

    recent_solves = []
    for sub in sorted(correct_subs, key=lambda s: s.submitted_at or datetime.min, reverse=True)[:15]:
        ch = CtfChallenge.query.get(sub.challenge_id)
        game = CtfGame.query.get(sub.game_id) if sub.game_id else None
        recent_solves.append({
            'challenge_title': ch.title if ch else '未知题目',
            'game_title': game.title if game else None,
            'points': sub.points_earned or (ch.points if ch else 0),
            'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
        })

    return jsonify({
        'user': _public_user_dict(u),
        'stats': {
            'participations': len(participations_raw),
            'solves': solves,
            'teams': teams,
            'category_stats': category_stats,
        },
        'participations': participations,
        'recent_solves': recent_solves,
    })


@bp.post("/delete-account")
@jwt_required()
def delete_own_account():
    """用户自助注销：需确认密码 + 确认文案"""
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({"code": 400, "msg": "invalid identity"}), 400
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    confirm = (data.get("confirm") or "").strip()
    if confirm not in ("DELETE", "删除", "注销"):
        return jsonify({"code": 400, "msg": "请在 confirm 中输入 DELETE 或「删除」确认"}), 400
    u = User.query.get(uid_int)
    if not u:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404
    if u.is_admin:
        return jsonify({"code": 403, "msg": "管理员请先取消管理员身份或由其他管理员删除"}), 403
    if not password or not u.verify_password(password):
        return jsonify({"code": 403, "msg": "密码不正确"}), 403
    # 软删策略：改邮箱/用户名，清空密码，保留外键完整性
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    u.email = f"deleted_{u.id}_{stamp}@invalid.local"
    if u.username:
        u.username = f"deleted_{u.id}_{stamp}"[:64]
    u.nickname = f"已注销用户#{u.id}"
    u.set_password(os.urandom(16).hex())
    u.email_verified = False
    u.is_moderator = False
    extensions.db.session.commit()
    return jsonify({"code": 200, "msg": "账号已注销"}), 200


@bp.get("/oauth/providers")
def list_oauth_providers():
    """公开：可用 OAuth 提供方（来自平台配置）"""
    from backend.services.platform_config_service import load_public_platform_info
    info = load_public_platform_info()
    providers = info.get("oauth_providers") or []
    return jsonify({"code": 200, "data": {"providers": providers}}), 200


@bp.get("/oauth/<provider_id>")
def oauth_start(provider_id):
    """OAuth 启动占位：未配置 provider 时返回明确错误，避免前端死链"""
    from backend.services.platform_config_service import load_public_platform_info
    info = load_public_platform_info()
    providers = {p.get("id"): p for p in (info.get("oauth_providers") or []) if isinstance(p, dict)}
    p = providers.get(provider_id)
    if not p:
        return jsonify({
            "code": 404,
            "msg": f"未配置 OAuth 提供方「{provider_id}」。请在平台配置 oauth_providers 后重试。",
        }), 404
    # 真实授权 URL 若已配置则 302
    auth_url = p.get("auth_url") or p.get("url")
    if auth_url and str(auth_url).startswith("http"):
        from flask import redirect
        return redirect(auth_url)
    return jsonify({
        "code": 501,
        "msg": f"提供方「{provider_id}」已登记但未配置 auth_url，暂无法跳转。",
        "data": {"provider": p},
    }), 501
