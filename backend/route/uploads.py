from flask import Blueprint, request, jsonify, current_app, send_file
import os
import mimetypes
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server import extensions
from backend.server.db_models import FileResource
from backend.server.audit_log import log_create, log_view
from functools import wraps
import jwt
import hashlib
import re
from pathlib import Path
import zipfile
import tempfile

bp = Blueprint('uploads', __name__)

ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'txt', 'md', 'pdf'])
IMAGE_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'webp'])
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def allowed(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXT or ext == 'zip'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'msg': 'Missing authorization header'}), 401
        try:
            token = token.split(' ')[1]
            jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        except (IndexError, jwt.InvalidTokenError):
            return jsonify({'msg': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


def get_file_md5(content):
    """计算内容的 MD5 hash"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.md5(content).hexdigest()


def extract_zip_and_process(zip_path):
    """
    解析 ZIP 文件，提取 MD 和图片，返回处理后的 MD 内容和图片 URL 映射
    """
    from backend.services.zip_safety import (
        ZipSafetyError, ZipLimits, validate_zip_path, safe_read_member,
    )

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    md_files = {}
    image_mappings = {}  # 原始路径 -> 上传后的 URL

    try:
        validate_zip_path(
            zip_path,
            limits=ZipLimits(max_compressed=MAX_UPLOAD_BYTES),
            allow_ext=IMAGE_EXT | {'md'},
        )
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue

                try:
                    file_content, safe_name = safe_read_member(
                        zip_ref, file_info, MAX_UPLOAD_BYTES,
                    )
                except ZipSafetyError:
                    raise

                ext = safe_name.rsplit('.', 1)[1].lower() if '.' in safe_name else ''
                orig_key = safe_name

                if ext in IMAGE_EXT:
                    file_md5 = get_file_md5(file_content)
                    saved_filename = f"{file_md5}.{ext}"
                    saved_path = os.path.join(upload_dir, saved_filename)

                    if not os.path.exists(saved_path):
                        with open(saved_path, 'wb') as fh:
                            fh.write(file_content)

                    saved_url = f"/static/uploads/{saved_filename}"
                    image_mappings[orig_key] = saved_url
                    # 兼容 ZIP 内原始相对路径引用
                    image_mappings[file_info.filename.replace('\\', '/')] = saved_url

                elif ext == 'md':
                    md_files[orig_key] = file_content.decode('utf-8', errors='ignore')

            for md_file, content in list(md_files.items()):
                updated_content = content
                for orig_path, new_url in image_mappings.items():
                    orig_path_normalized = orig_path.replace('\\', '/')
                    updated_content = re.sub(
                        rf'(!\[[^\]]*\]\()({re.escape(orig_path_normalized)}|{re.escape(orig_path)})',
                        rf'\1{new_url}',
                        updated_content
                    )
                    updated_content = re.sub(
                        rf'(src=")({re.escape(orig_path_normalized)}|{re.escape(orig_path)})(")',
                        rf'\1{new_url}\3',
                        updated_content
                    )
                md_files[md_file] = updated_content

        return md_files, image_mappings
    except ZipSafetyError as e:
        current_app.logger.warning(f'ZIP rejected: {e}')
        return None, None
    except zipfile.BadZipFile:
        return None, None


@bp.post('/')
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'msg': 'no file'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'msg': 'empty filename'}), 400
    if not allowed(f.filename):
        return jsonify({'msg': 'file type not allowed'}), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > MAX_UPLOAD_BYTES:
        return jsonify({'msg': 'file too large'}), 400

    try:
        uploader_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'msg': 'invalid identity'}), 400

    filename = secure_filename(f.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 处理 ZIP 文件
    if ext == 'zip':
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name
        
        md_files, image_mappings = extract_zip_and_process(tmp_path)
        os.unlink(tmp_path)
        
        if md_files is None:
            return jsonify({'msg': 'ZIP 校验失败：无效、损坏，或包含路径穿越/炸弹/不允许的文件类型'}), 400
        
        if not md_files:
            return jsonify({'msg': 'No Markdown files found in ZIP'}), 400
        
        # 保存处理后的 MD 文件（只用 basename + hash，避免 ZIP 内路径名污染）
        first_md_file = list(md_files.keys())[0]
        md_content = md_files[first_md_file]
        base_name = secure_filename(os.path.basename(first_md_file)) or "article.md"
        if not base_name.lower().endswith(".md"):
            base_name = f"{base_name}.md"
        content_hash = get_file_md5(md_content)[:12]
        md_filename = f"{content_hash}_{base_name}"
        md_dest = os.path.join(upload_dir, md_filename)

        base, md_ext = os.path.splitext(md_filename)
        i = 1
        while os.path.exists(md_dest):
            md_filename = f"{base}_{i}{md_ext}"
            md_dest = os.path.join(upload_dir, md_filename)
            i += 1
        
        with open(md_dest, 'w', encoding='utf-8') as fh:
            fh.write(md_content)
        
        url = f"/static/uploads/{md_filename}"
        
        # 为处理后的 MD 文件创建 FileResource 记录
        file_size = len(md_content.encode('utf-8'))
        file_path = os.path.join(upload_dir, md_filename)
        fr = FileResource(
            filename=md_filename,
            path=file_path,
            url=url,
            mime_type='text/markdown',
            size=file_size,
            uploader_id=uploader_id,
        )
        
        resource_id = None
        try:
            extensions.db.session.add(fr)
            extensions.db.session.commit()
            resource_id = fr.id
        except Exception as e:
            try:
                extensions.db.session.rollback()
            except Exception:
                pass
            current_app.logger.warning(f'Failed to save FileResource for ZIP: {e}')
        
        full_url = request.host_url.rstrip('/') + url
        try:
            if resource_id:
                log_create('resource', resource_id, md_filename, meta={'type': 'zip_processed', 'images': len(image_mappings)})
        except Exception:
            pass
        return jsonify({
            'url': full_url,
            'filename': md_filename,
            'resource_id': resource_id,
            'type': 'zip_processed',
            'images_extracted': len(image_mappings)
        })
    
    # 处理普通文件
    from backend.services.storage import get_storage
    storage = get_storage()
    key = filename
    base, file_ext = os.path.splitext(filename)
    i = 1
    while storage.exists(key):
        key = f"{base}_{i}{file_ext}"
        i += 1

    dest, url = storage.save(key, f.stream)
    filename = key

    # 尝试存储到数据库
    data = None
    size = None
    try:
        size = os.path.getsize(dest) if os.path.isfile(dest) else None
    except Exception:
        size = None

    mime_type, _ = mimetypes.guess_type(filename)
    fr = FileResource(
        filename=filename, path=dest, url=url, mime_type=mime_type, size=size,
        uploader_id=uploader_id,
    )
    try:
        extensions.db.session.add(fr)
        extensions.db.session.commit()
    except Exception:
        try:
            extensions.db.session.rollback()
        except Exception:
            pass
        return jsonify({'url': url, 'filename': filename})

    full_url = request.host_url.rstrip('/') + url
    try:
        log_create('resource', fr.id, filename)
    except Exception:
        pass
    return jsonify({'url': full_url, 'filename': filename, 'resource_id': fr.id})


@bp.post('/upload-image/')
@jwt_required()
def upload_image():
    """上传图片到编辑器（仅图片文件）"""
    if 'file' not in request.files:
        return jsonify({'msg': 'no file'}), 400
    
    f = request.files['file']
    if f.filename == '':
        return jsonify({'msg': 'empty filename'}), 400
    
    if '.' not in f.filename:
        return jsonify({'msg': 'file has no extension'}), 400
    
    ext = f.filename.rsplit('.', 1)[1].lower()
    if ext not in IMAGE_EXT:
        return jsonify({'msg': 'only image files allowed'}), 400

    try:
        uploader_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'msg': 'invalid identity'}), 400

    purpose = (request.form.get('purpose') or 'image').strip()
    if purpose not in ('image', 'carousel', 'public', 'avatar', 'article', 'attachment', 'poster'):
        purpose = 'image'

    # 用文件内容的 MD5 作为文件名（去重）
    file_content = f.read()
    if len(file_content) > MAX_UPLOAD_BYTES:
        return jsonify({'msg': 'file too large'}), 400
    file_md5 = get_file_md5(file_content)
    filename = f"{file_md5}.{ext}"

    from backend.services.storage import get_storage
    storage = get_storage()
    dest, url = storage.save(filename, file_content, content_type=f'image/{ext}')
    
    # 为图片创建 FileResource 记录（如果还不存在）
    resource_id = None
    existing_resource = FileResource.query.filter_by(url=url).first()
    if not existing_resource:
        fr = FileResource(
            filename=filename,
            url=url,
            path=dest,
            mime_type=f'image/{ext}',
            size=len(file_content),
            uploader_id=uploader_id,
            purpose=purpose,
            entity_type=request.form.get('entity_type'),  # 从请求中获取实体类型
            entity_id=request.form.get('entity_id')  # 从请求中获取实体ID
        )
        try:
            extensions.db.session.add(fr)
            extensions.db.session.commit()
            resource_id = fr.id
        except Exception as e:
            try:
                extensions.db.session.rollback()
            except Exception:
                pass
            current_app.logger.warning(f'Failed to save FileResource for image: {e}')
    else:
        resource_id = existing_resource.id
    
    full_url = request.host_url.rstrip('/') + url
    try:
        if resource_id:
            log_create('resource', resource_id, filename,)
    except Exception:
        pass
    return jsonify({
        'url': url,
        'full_url': full_url,
        'filename': filename,
        'resource_id': resource_id
    })


def _optional_user():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    from backend.server.db_models import User
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid is not None:
            return User.query.get(int(uid))
    except Exception:
        pass
    return None


@bp.get('/serve/<path:relpath>')
def serve_upload(relpath):
    """受控文件下载：替代直接访问 /static/uploads/"""
    from backend.server.security_helpers import can_access_resource

    if '..' in relpath.replace('\\', '/'):
        return jsonify({'msg': 'forbidden'}), 403

    upload_root = os.path.abspath(os.path.join(current_app.root_path, 'static', 'uploads'))
    safe_rel = relpath.replace('\\', '/').lstrip('/')
    file_path = os.path.abspath(os.path.join(upload_root, safe_rel))
    if not file_path.startswith(upload_root + os.sep):
        return jsonify({'msg': 'forbidden'}), 403
    if not os.path.isfile(file_path):
        return jsonify({'msg': 'not found'}), 404

    url = f'/static/uploads/{safe_rel}'
    fr = FileResource.query.filter(
        (FileResource.url == url) | (FileResource.path == file_path)
    ).first()
    user = _optional_user()

    if fr:
        if not can_access_resource(user, fr):
            return jsonify({'msg': 'forbidden'}), 403
    else:
        ext = safe_rel.rsplit('.', 1)[-1].lower() if '.' in safe_rel else ''
        if ext not in IMAGE_EXT:
            return jsonify({'msg': 'forbidden'}), 403

    mime_type, _ = mimetypes.guess_type(file_path)
    return send_file(file_path, mimetype=mime_type or 'application/octet-stream')
