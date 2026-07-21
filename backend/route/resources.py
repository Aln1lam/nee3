from flask import Blueprint, jsonify, Response, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.server import extensions
from backend.server.db_models import FileResource, User, CtfChallenge
from backend.server.security_helpers import can_access_resource
from backend.services.scoring_service import ChallengeCType
from backend.services.flag_generator import (
    resolve_challenge_expected_flag,
    personalize_signup_attachment,
)
import os

bp = Blueprint('resources', __name__)


def _get_optional_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid is not None:
            return User.query.get(int(uid))
    except Exception:
        pass
    return None


def _check_resource_access(resource):
    user = _get_optional_user()
    if not can_access_resource(user, resource):
        return jsonify({'msg': 'forbidden'}), 403
    return None


@bp.get('/<int:rid>')
def get_resource_meta(rid):
    r = FileResource.query.get_or_404(rid)
    denied = _check_resource_access(r)
    if denied:
        return denied
    return jsonify({
        'id': r.id,
        'filename': r.filename,
        'url': r.url,
        'mime_type': r.mime_type,
        'size': r.size,
        'created_at': r.created_at.isoformat() if r.created_at else None,
    })


@bp.get('/<int:rid>/content')
def get_resource_content(rid):
    r = FileResource.query.get_or_404(rid)
    denied = _check_resource_access(r)
    if denied:
        return denied

    try:
        data = None
        upload_root = os.path.abspath(os.path.join(current_app.root_path, 'static', 'uploads'))
        app_root = os.path.abspath(current_app.root_path)

        if r.path:
            file_path = os.path.abspath(r.path)
            # 仅允许落在 uploads 根或应用根下的受控路径
            under_upload = file_path.startswith(upload_root + os.sep)
            under_app = file_path.startswith(app_root + os.sep)
            if (under_upload or under_app) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
        elif r.url:
            url_path = r.url.replace('\\', '/').lstrip('/')
            if '..' in url_path.split('/'):
                return jsonify({'msg': 'forbidden'}), 403
            # 优先按 uploads 相对路径解析
            if url_path.startswith('static/uploads/'):
                rel = url_path[len('static/uploads/'):]
                file_path = os.path.abspath(os.path.join(upload_root, rel))
            elif url_path.startswith('uploads/'):
                rel = url_path[len('uploads/'):]
                file_path = os.path.abspath(os.path.join(upload_root, rel))
            else:
                file_path = os.path.abspath(os.path.join(app_root, url_path))
            if not (
                file_path.startswith(upload_root + os.sep)
                or file_path.startswith(app_root + os.sep)
            ):
                return jsonify({'msg': 'forbidden'}), 403
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()

        if data is not None:
            challenge = CtfChallenge.query.filter_by(attachment_id=rid).first()
            if (
                challenge
                and int(challenge.challenge_type or 0) == ChallengeCType.DYNAMIC_ATTACHMENT
                and challenge.flag_template
            ):
                user = _get_optional_user()
                if not user:
                    return jsonify({'msg': '动态附件需登录后下载'}), 401
                dynamic_flag = resolve_challenge_expected_flag(challenge, user, user.id)
                data = personalize_signup_attachment(data, dynamic_flag)

            resp = Response(data, mimetype=r.mime_type or 'application/octet-stream')
            resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
            resp.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
            return resp

        return jsonify({'msg': 'file not found'}), 404
    except Exception as e:
        current_app.logger.error(f'Error reading file: {e}')
        return jsonify({'msg': 'Error reading file'}), 500
