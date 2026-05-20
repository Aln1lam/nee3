from flask import Blueprint, jsonify, Response, current_app
from backend.server import extensions
from backend.server.db_models import FileResource
import os

bp = Blueprint('resources', __name__)


@bp.get('/<int:rid>')
def get_resource_meta(rid):
    r = FileResource.query.get_or_404(rid)
    return jsonify({
        'id': r.id,
        'filename': r.filename,
        'url': r.url,
        'mime_type': r.mime_type,
        'size': r.size,
        'created_at': r.created_at.isoformat() if r.created_at else None,
        'uploader_id': r.uploader_id,
    })


@bp.get('/<int:rid>/content')
def get_resource_content(rid):
    r = FileResource.query.get_or_404(rid)
    
    # Try to serve from the path or url
    try:
        # First try using the stored path
        if r.path and os.path.exists(r.path):
            with open(r.path, 'rb') as f:
                data = f.read()
            resp = Response(data, mimetype=r.mime_type or 'application/octet-stream')
            # 允许PDF等文件在iframe中显示
            resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
            resp.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
            return resp
        
        # Fallback to url - construct full file path from url
        if r.url:
            # url like /static/uploads/filename or /uploads/filename
            # Strip leading slash and use it relative to root_path
            url_path = r.url.lstrip('/')
            file_path = os.path.join(current_app.root_path, url_path)
            
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                resp = Response(data, mimetype=r.mime_type or 'application/octet-stream')
                # 允许PDF等文件在iframe中显示
                resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
                resp.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
                return resp
        
        return jsonify({'msg': 'file not found', 'path': r.path, 'url': r.url}), 404
    except Exception as e:
        current_app.logger.error(f'Error reading file: {e}')
        return jsonify({'msg': f'Error reading file: {str(e)}'}), 500
