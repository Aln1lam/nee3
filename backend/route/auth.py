from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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


bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    """注册 - 先发送验证邮件，验证通过后才创建用户"""
    data = request.get_json() or {}
    email, password, nickname = data.get("email"), data.get("password"), data.get("nickname")
    username = data.get("username")  # 可选

    if not all([email, password, nickname]):
        return {"msg": "邮箱、密码和昵称为必填项"}, 400
    
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
def login():
    data = request.get_json() or {}
    account = data.get("account") or data.get("email")  # 兼容旧字段名
    password = data.get("password")
    
    if not account or not password:
        return {"msg": "请输入账号和密码"}, 400
    
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
    payload = {
        "access_token": token,
        "user": user.to_dict(),  # 返回完整的用户信息，包含 avatar
    }
    # 返回 JSON 的同时设置 HttpOnly cookie，便于 SSE 与其他需要凭据的接口（开发/生产差异处理）
    resp = make_response(jsonify(payload))
    # cookie 策略：开发时允许非 Secure, 生产时建议 Secure + SameSite=None
    is_debug = current_app.config.get('DEBUG', False)
    if is_debug:
        resp.set_cookie('neepu_token', token, httponly=True, samesite='Lax', path='/', max_age=7*24*3600)
    else:
        resp.set_cookie('neepu_token', token, httponly=True, secure=True, samesite='None', path='/', max_age=7*24*3600)
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
