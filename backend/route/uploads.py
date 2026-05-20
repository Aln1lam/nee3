from flask import Blueprint, request, jsonify, current_app
import os
import mimetypes
from werkzeug.utils import secure_filename
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

ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'svg', 'txt', 'md', 'pdf', 'html'])
IMAGE_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'])


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
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    md_files = {}
    image_mappings = {}  # 原始路径 -> 上传后的 URL
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 先扫描并上传所有图片文件
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                
                filename = file_info.filename
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                # 处理图片
                if ext in IMAGE_EXT:
                    file_content = zip_ref.read(filename)
                    file_md5 = get_file_md5(file_content)
                    saved_filename = f"{file_md5}.{ext}"
                    saved_path = os.path.join(upload_dir, saved_filename)
                    
                    # 避免重复写入
                    if not os.path.exists(saved_path):
                        with open(saved_path, 'wb') as fh:
                            fh.write(file_content)
                    
                    saved_url = f"/static/uploads/{saved_filename}"
                    image_mappings[filename] = saved_url
                
                # 处理 MD 文件
                elif ext == 'md':
                    file_content = zip_ref.read(filename).decode('utf-8', errors='ignore')
                    md_files[filename] = file_content
            
            # 更新 MD 文件中的图片路径
            for md_file, content in md_files.items():
                updated_content = content
                
                # 替换所有图片引用
                for orig_path, new_url in image_mappings.items():
                    # 处理不同的路径分隔符
                    orig_path_normalized = orig_path.replace('\\', '/')
                    
                    # 替换 ![alt](path) 格式
                    updated_content = re.sub(
                        rf'(!\[[^\]]*\]\()({re.escape(orig_path_normalized)}|{re.escape(orig_path)})',
                        rf'\1{new_url}',
                        updated_content
                    )
                    
                    # 替换 <img src="path"> 格式
                    updated_content = re.sub(
                        rf'(src=")({re.escape(orig_path_normalized)}|{re.escape(orig_path)})(")',
                        rf'\1{new_url}\3',
                        updated_content
                    )
                
                md_files[md_file] = updated_content
        
        return md_files, image_mappings
    except zipfile.BadZipFile:
        return None, None


@bp.post('/')
def upload_file():
    if 'file' not in request.files:
        return jsonify({'msg': 'no file'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'msg': 'empty filename'}), 400
    if not allowed(f.filename):
        return jsonify({'msg': 'file type not allowed'}), 400

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
            return jsonify({'msg': 'Invalid or corrupted ZIP file'}), 400
        
        if not md_files:
            return jsonify({'msg': 'No Markdown files found in ZIP'}), 400
        
        # 返回第一个 MD 文件的内容和图片映射
        first_md_file = list(md_files.keys())[0]
        md_content = md_files[first_md_file]
        
        # 保存处理后的 MD 文件
        md_filename = first_md_file.split('/')[-1] if '/' in first_md_file else first_md_file
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
            size=file_size
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
    dest = os.path.join(upload_dir, filename)
    base, file_ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(dest):
        filename = f"{base}_{i}{file_ext}"
        dest = os.path.join(upload_dir, filename)
        i += 1
    
    f.save(dest)
    url = f"/static/uploads/{filename}"

    # 尝试存储到数据库
    data = None
    size = None
    try:
        size = os.path.getsize(dest)
    except Exception:
        size = None

    mime_type, _ = mimetypes.guess_type(dest)
    fr = FileResource(filename=filename, path=dest, url=url, mime_type=mime_type, size=size)
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
@token_required
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
    
    # 用文件内容的 MD5 作为文件名（去重）
    file_content = f.read()
    file_md5 = get_file_md5(file_content)
    filename = f"{file_md5}.{ext}"
    
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, filename)
    
    # 如果同内容的文件已存在，直接返回
    if not os.path.exists(dest):
        with open(dest, 'wb') as fh:
            fh.write(file_content)
    
    url = f"/static/uploads/{filename}"
    
    # 为图片创建 FileResource 记录（如果还不存在）
    resource_id = None
    existing_resource = FileResource.query.filter_by(url=url).first()
    if not existing_resource:
        fr = FileResource(
            filename=filename,
            url=url,
            path=os.path.join(upload_dir, filename),
            mime_type=f'image/{ext}',
            size=len(file_content),
            purpose='image',  # 标记为通用图片
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
        'url': full_url,
        'filename': filename,
        'resource_id': resource_id
    })
