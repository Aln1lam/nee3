"""共享安全校验工具"""
import os

from flask import current_app, request

from backend.server.db_models import Article, CtfChallenge, User


def _captcha_enabled():
    """环境变量优先；否则读 SystemConfig.captcha_required。"""
    env = os.environ.get("NEPU_CAPTCHA_REQUIRED", "").lower()
    if env in ("1", "true", "yes"):
        return True
    if env in ("0", "false", "no"):
        return False
    try:
        from backend.server.db_models import SystemConfig
        row = SystemConfig.query.filter_by(key="captcha_required").first()
        if row and str(row.value).lower() in ("1", "true", "yes"):
            return True
    except Exception:
        pass
    return False


def verify_captcha_required(data):
    """注册/登录验证码。默认关闭；NEPU_CAPTCHA_REQUIRED 或 SystemConfig.captcha_required 启用。"""
    if not _captcha_enabled():
        return True, None
    if current_app.config.get("TESTING"):
        return True, None

    from backend.route.captcha import verify_captcha

    captcha_id = data.get("captcha_id")
    captcha_answer = data.get("captcha_answer")
    if not captcha_id or not captcha_answer:
        return False, "请完成验证码"
    if not verify_captcha(captcha_id, captcha_answer):
        return False, "验证码错误或已过期"
    return True, None


def allow_bootstrap_admin():
    """仅允许携带有效 NEPU_SETUP_SECRET 的首次提权（DEBUG 亦不可免密钥）。"""
    if User.query.filter_by(is_admin=True).first():
        return False, "管理员已存在"
    setup_secret = os.environ.get("NEPU_SETUP_SECRET", "")
    provided = request.headers.get("X-Setup-Secret", "")
    if setup_secret and provided and provided == setup_secret:
        return True, None
    return False, "forbidden: require X-Setup-Secret"


def can_access_resource(user, resource):
    """判断用户是否有权访问文件资源。"""
    if not resource:
        return False

    # poster/image：赛事海报、编辑器插图需可匿名展示
    if resource.purpose in ("carousel", "public", "avatar", "poster", "image"):
        return True

    if not user:
        return False
    if getattr(user, "is_admin", False):
        return True
    if resource.uploader_id and resource.uploader_id == user.id:
        return True

    article = Article.query.filter_by(resource_id=resource.id).first()
    if article:
        if article.status == "published":
            return True
        if article.author_id == user.id:
            return True

    challenge = CtfChallenge.query.filter_by(attachment_id=resource.id).first()
    if challenge:
        from backend.services.permission_service import GamePermission, PermissionService

        return PermissionService.check_challenge_permission(
            user.id, challenge.id, GamePermission.VIEW_CHALLENGE
        )

    return False


def user_can_manage_instance(user, user_id, instance):
    """容器实例：创建者或同队成员可管理。"""
    if not instance:
        return False
    if getattr(user, "is_admin", False):
        return True
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        uid = user_id
    if instance.user_id == uid:
        return True
    return bool(user and user.team_id and instance.team_id == user.team_id)
