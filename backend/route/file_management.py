"""
文件资源管理 API
统一管理所有上传的文件，包括头像、文章、轮播图等
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc
from datetime import datetime
from backend.server import extensions
from backend.server.extensions import db
from backend.server.db_models import FileResource, User, Article, CarouselSlide
import os

bp = Blueprint("file_management", __name__, url_prefix="/api/admin/platform/files")


def admin_required(fn):
    """管理员权限验证"""
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


# ======================== 获取文件列表 ========================

@bp.get("")
@admin_required
def list_files():
    """获取所有文件资源"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    purpose = request.args.get('purpose', '', type=str)
    entity_type = request.args.get('entity_type', '', type=str)
    
    query = FileResource.query
    
    if purpose:
        query = query.filter_by(purpose=purpose)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    total = query.count()
    files = query.order_by(desc(FileResource.created_at)).paginate(
        page=page, per_page=per_page
    ).items
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'items': [f.to_dict() for f in files]
    }), 200


# ======================== 获取文件统计 ========================

@bp.get("/stats")
@admin_required
def get_file_stats():
    """获取文件资源统计信息"""
    # 按用途统计
    by_purpose = db.session.query(
        FileResource.purpose,
        func.count(FileResource.id).label('count'),
        func.sum(FileResource.size).label('total_size')
    ).group_by(FileResource.purpose).all()
    
    # 按实体类型统计
    by_entity_type = db.session.query(
        FileResource.entity_type,
        func.count(FileResource.id).label('count'),
        func.sum(FileResource.size).label('total_size')
    ).group_by(FileResource.entity_type).all()
    
    # 总统计
    total_files = FileResource.query.count()
    total_size = db.session.query(func.sum(FileResource.size)).scalar() or 0
    
    return jsonify({
        'total': {
            'files': total_files,
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2)
        },
        'by_purpose': [{
            'purpose': p or 'unknown',
            'count': c,
            'size_bytes': s or 0,
            'size_mb': round((s or 0) / (1024 * 1024), 2)
        } for p, c, s in by_purpose],
        'by_entity_type': [{
            'entity_type': et or 'unknown',
            'count': c,
            'size_bytes': s or 0,
            'size_mb': round((s or 0) / (1024 * 1024), 2)
        } for et, c, s in by_entity_type]
    }), 200


# ======================== 查找未使用的文件 ========================

@bp.get("/unused")
@admin_required
def find_unused_files():
    """查找未被任何实体引用的文件"""
    # 获取所有文件
    all_files = FileResource.query.all()
    
    unused_files = []
    
    for f in all_files:
        is_used = False
        
        # 检查是否被用户头像引用
        if f.purpose == 'avatar':
            user = User.query.filter_by(avatar_resource_id=f.id).first()
            if user:
                is_used = True
        
        # 检查是否被文章引用
        if f.purpose == 'article' or f.entity_type == 'article':
            article = Article.query.filter_by(resource_id=f.id).first()
            if article:
                is_used = True
        
        # 检查是否被轮播图引用
        if f.purpose == 'carousel' or f.entity_type == 'carousel_slide':
            carousel = CarouselSlide.query.filter_by(resource_id=f.id).first()
            if carousel:
                is_used = True
        
        # 如果有entity_id，说明被标记为已使用
        if f.entity_id:
            is_used = True
        
        if not is_used:
            unused_files.append(f.to_dict())
    
    return jsonify({
        'total_unused': len(unused_files),
        'items': unused_files
    }), 200


# ======================== 删除文件 ========================

@bp.delete("/<int:file_id>")
@admin_required
def delete_file(file_id):
    """删除文件及其关联"""
    fr = FileResource.query.get(file_id)
    if not fr:
        return jsonify({'error': '文件不存在'}), 404
    
    # 检查文件是否被使用
    is_used = False
    using_entity = None
    
    # 检查用户头像
    if fr.purpose == 'avatar':
        user = User.query.filter_by(avatar_resource_id=fr.id).first()
        if user:
            is_used = True
            using_entity = f"用户 {user.nickname} 的头像"
    
    # 检查文章
    if fr.purpose == 'article' or fr.entity_type == 'article':
        article = Article.query.filter_by(resource_id=fr.id).first()
        if article:
            is_used = True
            using_entity = f"文章 '{article.title}' 的配图"
    
    # 检查轮播图
    if fr.purpose == 'carousel' or fr.entity_type == 'carousel_slide':
        carousel = CarouselSlide.query.filter_by(resource_id=fr.id).first()
        if carousel:
            is_used = True
            using_entity = f"轮播图 {carousel.id}"
    
    if is_used:
        return jsonify({
            'error': '文件仍在使用中',
            'detail': using_entity
        }), 400
    
    # 删除物理文件
    try:
        if fr.path and os.path.exists(fr.path):
            os.remove(fr.path)
        elif fr.url:
            file_path = os.path.join(current_app.root_path, 'static', fr.url.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        current_app.logger.warning(f'删除文件失败: {e}')
    
    # 删除数据库记录
    try:
        db.session.delete(fr)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除数据库记录失败', 'detail': str(e)}), 500
    
    return jsonify({'success': True, 'message': '文件已删除'}), 200


# ======================== 清理未使用文件 ========================

@bp.post("/cleanup-unused")
@admin_required
def cleanup_unused_files():
    """批量删除所有未使用的文件"""
    # 获取所有文件
    all_files = FileResource.query.all()
    
    deleted_count = 0
    failed_count = 0
    errors = []
    
    for f in all_files:
        is_used = False
        
        # 检查各种引用
        if f.purpose == 'avatar':
            user = User.query.filter_by(avatar_resource_id=f.id).first()
            is_used = bool(user)
        
        if f.purpose == 'article' or f.entity_type == 'article':
            article = Article.query.filter_by(resource_id=f.id).first()
            is_used = bool(article)
        
        if f.purpose == 'carousel' or f.entity_type == 'carousel_slide':
            carousel = CarouselSlide.query.filter_by(resource_id=f.id).first()
            is_used = bool(carousel)
        
        if f.entity_id:
            is_used = True
        
        if not is_used:
            # 尝试删除
            try:
                if f.path and os.path.exists(f.path):
                    os.remove(f.path)
                elif f.url:
                    file_path = os.path.join(current_app.root_path, 'static', f.url.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                db.session.delete(f)
                deleted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"文件 {f.filename}: {str(e)}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': '提交事务失败',
            'detail': str(e)
        }), 500
    
    return jsonify({
        'success': True,
        'deleted': deleted_count,
        'failed': failed_count,
        'errors': errors if errors else None
    }), 200


# ======================== 获取文件详情 ========================

@bp.get("/<int:file_id>")
@admin_required
def get_file_detail(file_id):
    """获取单个文件的详细信息"""
    fr = FileResource.query.get(file_id)
    if not fr:
        return jsonify({'error': '文件不存在'}), 404
    
    # 获取使用情况
    usage = {
        'using': False,
        'used_by': None
    }
    
    if fr.purpose == 'avatar':
        user = User.query.filter_by(avatar_resource_id=fr.id).first()
        if user:
            usage['using'] = True
            usage['used_by'] = f"用户 {user.nickname} 的头像"
    
    if fr.purpose == 'article' or fr.entity_type == 'article':
        article = Article.query.filter_by(resource_id=fr.id).first()
        if article:
            usage['using'] = True
            usage['used_by'] = f"文章 '{article.title}'"
    
    if fr.purpose == 'carousel' or fr.entity_type == 'carousel_slide':
        carousel = CarouselSlide.query.filter_by(resource_id=fr.id).first()
        if carousel:
            usage['using'] = True
            usage['used_by'] = f"轮播图"
    
    return jsonify({
        'file': fr.to_dict(),
        'usage': usage
    }), 200
