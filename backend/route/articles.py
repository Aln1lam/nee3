from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from backend.server import extensions
from backend.server.db_models import Article, User, MainAnnouncement
from backend.server.db_models import FileResource
from backend.server.audit_log import log_create, log_view, log_update, log_delete
from backend.services.wiki_nav_service import build_wiki_nav_from_db
from backend.services.cache_aside import (
    read_through,
    KEY_WIKI_NAV,
    KEY_CAROUSEL,
    TTL_WIKI_NAV,
    TTL_CAROUSEL,
    TTL_ARTICLES,
    articles_public_cache_key,
)
import json

bp = Blueprint('articles', __name__)


def load_public_articles_page(page: int = 1, per_page: int = 20) -> dict:
    """从 MySQL 加载公开文章列表（Cache-Aside loader）。"""
    q = Article.query.filter(Article.status == 'published')
    items_q = q.order_by(Article.created_at.desc())
    total = items_q.count()
    items = items_q.offset((page - 1) * per_page).limit(per_page).all()
    out = []
    for a in items:
        author = User.query.get(a.author_id) if a.author_id else None
        out.append({
            'id': a.id,
            'title': a.title,
            'summary': a.summary,
            'author_id': a.author_id,
            'author_name': author.nickname if author else '未知作者',
            'resource_id': a.resource_id,
            'status': a.status,
            'tags': a.tags,
            'created_at': a.created_at.isoformat(),
            'published_at': a.published_at.isoformat() if a.published_at else None,
            'content': a.content,
        })
    return {
        "code": 200,
        "msg": "获取成功",
        "data": {"items": out, "total": total, "page": page, "per_page": per_page},
    }


def success_response(data=None, message="Success"):
    """返回成功响应"""
    return jsonify({"data": data, "message": message, "code": 0}), 200


def error_response(message="Error", code=400):
    """返回错误响应"""
    return jsonify({"error": message, "code": code}), code


@bp.get('/wiki-nav')
def wiki_nav():
    """知识库侧栏导航：Cache-Aside，真相源为 Article 表"""
    data, hit = read_through(
        KEY_WIKI_NAV,
        TTL_WIKI_NAV,
        lambda: build_wiki_nav_from_db(wiki_only=True),
    )
    resp = jsonify(data)
    resp.headers['X-Cache'] = 'HIT' if hit else 'MISS'
    return resp


@bp.get('/carousel')
def get_carousel():
    """获取轮播图（公开接口）"""
    def _load():
        from backend.services.carousel_service import load_public_carousel_slides
        slides = load_public_carousel_slides(sanitize=True)
        try:
            log_view('carousel', None, 'carousel_list')
        except Exception:
            pass
        return slides

    data, hit = read_through(KEY_CAROUSEL, TTL_CAROUSEL, _load)
    resp = jsonify(data)
    resp.headers['X-Cache'] = 'HIT' if hit else 'MISS'
    return resp


@bp.get('/announcements')
def get_announcements_for_user():
    """获取公告（公开读取已激活公告；登录用户同样可见）"""
    announcements = MainAnnouncement.query.filter_by(is_active=True).order_by(MainAnnouncement.created_at.desc()).all()
    try:
        verify_jwt_in_request(optional=True)
        log_view('announcement', None, 'announcements_list')
    except Exception:
        pass
    return jsonify([a.to_dict() for a in announcements])


@bp.get('/')
def list_articles():
    q = Article.query
    uid_int = None
    is_admin = False
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid is not None:
            uid_int = int(uid)
            u = User.query.get(uid_int)
            is_admin = bool(u and getattr(u, 'is_admin', False))
    except Exception:
        pass

    if is_admin:
        pass
    elif uid_int:
        q = q.filter((Article.status == 'published') | (Article.author_id == uid_int))
    else:
        q = q.filter(Article.status == 'published')

    search = request.args.get('q')
    tag = request.args.get('tag')
    page = int(request.args.get('page') or 1)
    per_page = int(request.args.get('per_page') or 20)

    # 公开默认列表走 Cache-Aside；带搜索/标签/管理员/个人草稿视图直查 MySQL
    can_cache = (
        not search
        and not tag
        and not is_admin
        and not uid_int
    )
    if can_cache:
        cache_key = articles_public_cache_key(page, per_page)
        payload, hit = read_through(
            cache_key,
            TTL_ARTICLES,
            lambda: load_public_articles_page(page=page, per_page=per_page),
        )
        resp = jsonify(payload)
        resp.headers['X-Cache'] = 'HIT' if hit else 'MISS'
        return resp

    if search:
        q = q.filter(Article.title.contains(search) | Article.content.contains(search))
    if tag:
        q = q.filter(Article.tags.contains(tag))
    items_q = q.order_by(Article.created_at.desc())
    total = items_q.count()
    items = items_q.offset((page-1)*per_page).limit(per_page).all()
    out = []
    for a in items:
        author = User.query.get(a.author_id) if a.author_id else None
        out.append({
            'id': a.id,
            'title': a.title,
            'summary': a.summary,
            'author_id': a.author_id,
            'author_name': author.nickname if author else '未知作者',
            'resource_id': a.resource_id,
            'status': a.status,
            'tags': a.tags,
            'created_at': a.created_at.isoformat(),
            'published_at': a.published_at.isoformat() if a.published_at else None,
            'content': a.content,
        })
    return jsonify({
        "code": 200,
        "msg": "获取成功",
        "data": {"items": out, "total": total, "page": page, "per_page": per_page},
    })


@bp.post('/')
@jwt_required()
def create_article():
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')  # markdown内容
    summary = data.get('summary')
    resource_id = data.get('resource_id')
    tags = data.get('tags')
    status = data.get('status', 'draft')
    if not title:
        return jsonify({'msg': 'title required'}), 400
    uid = get_jwt_identity()
    try:
        uid = int(uid)
    except Exception:
        return jsonify({'msg': 'invalid identity'}), 400
    author = User.query.get(uid)
    if status == 'published' and not (author and getattr(author, 'is_admin', False)):
        status = 'draft'
    a = Article(title=title, content=content, summary=summary, tags=','.join(tags) if isinstance(tags, list) else (tags or ''), status=status, author_id=uid)
    if resource_id:
        try:
            a.resource_id = int(resource_id)
        except Exception:
            a.resource_id = None
    if status == 'published':
        a.published_at = a.created_at
    extensions.db.session.add(a)
    extensions.db.session.commit()
    try:
        log_create('article', a.id, a.title)
    except Exception:
        pass
    return jsonify({'msg': 'created', 'id': a.id, 'resource_id': a.resource_id}), 201


@bp.get('/wiki/<slug>')
def get_wiki_by_slug(slug):
    """按 wiki slug 获取知识库文章（tags 含 wiki:{slug}）"""
    tag = f'wiki:{slug}'
    a = (
        Article.query.filter(Article.tags.contains(tag), Article.status == 'published')
        .order_by(Article.created_at.desc())
        .first()
    )
    if not a:
        a = Article.query.filter(
            Article.title.contains(slug.replace('-', ' ')),
            Article.status == 'published',
        ).first()
    if not a:
        return error_response('文章不存在', 404)
    author = User.query.get(a.author_id) if a.author_id else None
    return success_response({
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'summary': a.summary,
        'tags': a.tags,
        'author_name': author.nickname if author else '平台',
        'created_at': a.created_at.isoformat() if a.created_at else None,
        'slug': slug,
    })


@bp.get('/<int:aid>')
def get_article(aid):
    a = Article.query.get_or_404(aid)
    uid_int = None
    is_admin = False
    is_author = False
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid is not None:
            uid_int = int(uid)
            u = User.query.get(uid_int)
            is_admin = bool(u and getattr(u, 'is_admin', False))
            is_author = a.author_id == uid_int
    except Exception:
        pass

    if a.status != 'published' and not is_admin and not is_author:
        return error_response('文章不存在', 404)

    try:
        log_view('article', a.id, a.title)
    except Exception:
        pass
    return jsonify({
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'summary': a.summary,
        'author_id': a.author_id,
        'resource_id': a.resource_id,
        'status': a.status,
        'tags': a.tags,
        'created_at': a.created_at.isoformat(),
        'published_at': a.published_at.isoformat() if a.published_at else None,
    })


def _is_author_or_admin(uid_int, article):
    if not uid_int:
        return False
    u = User.query.get(uid_int)
    if not u:
        return False
    if getattr(u, 'is_admin', False):
        return True
    return article.author_id == uid_int


@bp.put('/<int:aid>')
@jwt_required()
def update_article(aid):
    a = Article.query.get_or_404(aid)
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({'msg': 'invalid identity'}), 400
    if not _is_author_or_admin(uid_int, a):
        return jsonify({'msg': 'forbidden'}), 403
    data = request.get_json() or {}
    author = User.query.get(uid_int)
    new_status = data.get('status')
    if new_status == 'published' and not (author and getattr(author, 'is_admin', False)):
        data['status'] = 'draft'
    for f in ('title', 'content', 'summary', 'status'):
        if f in data:
            setattr(a, f, data.get(f))
    if 'tags' in data:
        tags = data.get('tags')
        a.tags = ','.join(tags) if isinstance(tags, list) else (tags or '')
    if 'resource_id' in data:
        try:
            a.resource_id = int(data.get('resource_id'))
        except Exception:
            a.resource_id = None
    if a.status == 'published' and not a.published_at:
        a.published_at = a.created_at
    extensions.db.session.add(a)
    extensions.db.session.commit()
    try:
        log_update('article', a.id, a.title)
    except Exception:
        pass
    return jsonify({'msg': 'updated', 'id': a.id, 'resource_id': a.resource_id})


@bp.delete('/<int:aid>')
@jwt_required()
def delete_article(aid):
    a = Article.query.get_or_404(aid)
    uid = get_jwt_identity()
    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({'msg': 'invalid identity'}), 400
    if not _is_author_or_admin(uid_int, a):
        return jsonify({'msg': 'forbidden'}), 403
    
    import os
    
    # 删除关联的图片（如果没有其他文章引用）
    if a.resource_id:
        # 检查是否有其他文章引用该图片
        other_articles = Article.query.filter(
            Article.resource_id == a.resource_id,
            Article.id != aid
        ).count()
        
        if other_articles == 0:
            # 没有其他文章引用，删除图片文件和数据库记录
            fr = FileResource.query.get(a.resource_id)
            if fr:
                # 删除物理文件
                try:
                    file_path = os.path.join(current_app.root_path, 'static', fr.url.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        current_app.logger.info(f'Deleted file: {file_path}')
                except Exception as e:
                    current_app.logger.warning(f'Failed to delete file: {e}')
                
                # 从数据库删除资源记录
                try:
                    extensions.db.session.delete(fr)
                    current_app.logger.info(f'Deleted resource record: {fr.filename}')
                except Exception as e:
                    current_app.logger.warning(f'Failed to delete resource record: {e}')
    
    # 删除文章
    extensions.db.session.delete(a)
    extensions.db.session.commit()
    try:
        log_delete('article', aid, a.title)
    except Exception:
        pass
    return jsonify({'msg': 'deleted', 'id': aid})
