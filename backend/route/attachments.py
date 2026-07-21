"""
文章和轮播图附件管理
"""
from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server.extensions import db
from backend.server.db_models import (
    FileResource, Article, CarouselSlide, 
    ArticleAttachment, CarouselAttachment, User
)
import hashlib

bp = Blueprint('attachments', __name__, url_prefix='/api/attachments')

ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'svg', 'txt', 'md', 'pdf', 'html', 'zip'])
IMAGE_EXT = set(['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'])


def get_file_md5(content):
    """计算内容的 MD5 hash"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.md5(content).hexdigest()


# ==================== 文章附件 ====================

@bp.post('/article/<int:article_id>')
@jwt_required()
def upload_article_attachment(article_id):
    """为文章上传附件"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    
    # 检查文章是否存在
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'error': '文章不存在'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    if '.' not in f.filename:
        return jsonify({'error': '文件没有扩展名'}), 400
    
    ext = f.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'error': f'不支持的文件类型: {ext}'}), 400
    
    # 读取文件内容并计算MD5
    file_content = f.read()
    if ext == 'zip':
        from backend.services.zip_safety import ZipSafetyError, validate_zip_bytes
        try:
            validate_zip_bytes(file_content)
        except ZipSafetyError as e:
            return jsonify({'error': f'ZIP 不安全: {e}'}), 400
    file_md5 = get_file_md5(file_content)
    filename = f"{file_md5}.{ext}"
    
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'articles')
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, filename)
    
    # 保存文件
    if not os.path.exists(dest):
        with open(dest, 'wb') as fh:
            fh.write(file_content)
    
    url = f"/static/uploads/articles/{filename}"
    
    # 创建FileResource记录 - 确定mime_type
    mime_type = 'application/octet-stream'
    if ext in IMAGE_EXT:
        mime_type = f'image/{ext}'
    elif ext == 'pdf':
        mime_type = 'application/pdf'
    elif ext == 'zip':
        mime_type = 'application/zip'
    
    try:
        # 检查是否已存在相同的文件资源
        existing_resource = FileResource.query.filter_by(url=url).first()
        if not existing_resource:
            fr = FileResource(
                filename=filename,
                url=url,
                path=dest,
                mime_type=mime_type,
                size=len(file_content),
                purpose='article',
                entity_type='article',
                entity_id=article_id
            )
            db.session.add(fr)
            db.session.flush()
        else:
            fr = existing_resource
        
        # 创建ArticleAttachment记录
        attachment_type = 'image' if ext in IMAGE_EXT else 'document'
        sort_order = request.form.get('sort_order', 0, type=int)
        description = request.form.get('description', '')
        
        aa = ArticleAttachment(
            article_id=article_id,
            file_id=fr.id,
            attachment_type=attachment_type,
            sort_order=sort_order,
            description=description
        )
        db.session.add(aa)
        db.session.commit()
        
        full_url = request.host_url.rstrip('/') + url
        return jsonify({
            'id': aa.id,
            'url': full_url,
            'filename': filename,
            'file_id': fr.id,
            'attachment_type': attachment_type
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to upload article attachment: {e}')
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@bp.get('/article/<int:article_id>')
@jwt_required()
def get_article_attachments(article_id):
    """获取文章的所有附件"""
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'error': '文章不存在'}), 404
    
    attachments = ArticleAttachment.query.filter_by(article_id=article_id).order_by(
        ArticleAttachment.sort_order
    ).all()
    
    return jsonify([a.to_dict() for a in attachments])


@bp.delete('/article/<int:article_id>/<int:attachment_id>')
@jwt_required()
def delete_article_attachment(article_id, attachment_id):
    """删除文章的附件"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    
    attachment = ArticleAttachment.query.filter_by(
        id=attachment_id,
        article_id=article_id
    ).first()
    
    if not attachment:
        return jsonify({'error': '附件不存在'}), 404
    
    try:
        db.session.delete(attachment)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 轮播图附件 ====================

@bp.post('/carousel/<int:carousel_id>')
@jwt_required()
def upload_carousel_attachment(carousel_id):
    """为轮播图上传附件"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    
    # 检查轮播图是否存在
    carousel = CarouselSlide.query.get(carousel_id)
    if not carousel:
        return jsonify({'error': '轮播图不存在'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    if '.' not in f.filename:
        return jsonify({'error': '文件没有扩展名'}), 400
    
    ext = f.filename.rsplit('.', 1)[1].lower()
    if ext not in IMAGE_EXT:
        return jsonify({'error': f'仅支持图片文件'}), 400
    
    # 读取文件内容并计算MD5
    file_content = f.read()
    file_md5 = get_file_md5(file_content)
    filename = f"{file_md5}.{ext}"
    
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'carousel')
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, filename)
    
    # 保存文件
    if not os.path.exists(dest):
        with open(dest, 'wb') as fh:
            fh.write(file_content)
    
    url = f"/static/uploads/carousel/{filename}"
    
    try:
        # 检查是否已存在相同的文件资源
        existing_resource = FileResource.query.filter_by(url=url).first()
        if not existing_resource:
            fr = FileResource(
                filename=filename,
                url=url,
                path=dest,
                mime_type=f'image/{ext}',
                size=len(file_content),
                purpose='carousel',
                entity_type='carousel_slide',
                entity_id=carousel_id
            )
            db.session.add(fr)
            db.session.flush()
        else:
            fr = existing_resource
        
        # 创建CarouselAttachment记录
        is_thumbnail = request.form.get('is_thumbnail', False, type=bool)
        sort_order = request.form.get('sort_order', 0, type=int)
        
        ca = CarouselAttachment(
            carousel_id=carousel_id,
            file_id=fr.id,
            sort_order=sort_order,
            is_thumbnail=is_thumbnail
        )
        db.session.add(ca)

        if is_thumbnail or not carousel.image_url:
            carousel.image_url = url
            carousel.resource_id = fr.id

        db.session.commit()
        
        full_url = request.host_url.rstrip('/') + url
        return jsonify({
            'id': ca.id,
            'url': full_url,
            'filename': filename,
            'file_id': fr.id,
            'is_thumbnail': is_thumbnail
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to upload carousel attachment: {e}')
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@bp.get('/carousel/<int:carousel_id>')
@jwt_required()
def get_carousel_attachments(carousel_id):
    """获取轮播图的所有附件"""
    carousel = CarouselSlide.query.get(carousel_id)
    if not carousel:
        return jsonify({'error': '轮播图不存在'}), 404
    
    attachments = CarouselAttachment.query.filter_by(carousel_id=carousel_id).order_by(
        CarouselAttachment.sort_order
    ).all()
    
    return jsonify([a.to_dict() for a in attachments])


@bp.delete('/carousel/<int:carousel_id>/<int:attachment_id>')
@jwt_required()
def delete_carousel_attachment(carousel_id, attachment_id):
    """删除轮播图的附件"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    
    attachment = CarouselAttachment.query.filter_by(
        id=attachment_id,
        carousel_id=carousel_id
    ).first()
    
    if not attachment:
        return jsonify({'error': '附件不存在'}), 404
    
    try:
        db.session.delete(attachment)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
