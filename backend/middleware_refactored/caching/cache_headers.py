"""
缓存控制模块

功能: 设置 HTTP 缓存策略，指导浏览器缓存行为

缓存头:
- Cache-Control: 缓存控制策略
- ETag: 资源唯一标识（强验证）
- Last-Modified: 资源最后修改时间（弱验证）

缓存场景:
- 静态资源 (JS/CSS): 长期缓存（1 年）
- 图片资源: 中期缓存（1 个月）
- API 数据: 短期缓存或不缓存
- 实时数据: 不缓存

使用方式:
    from flask import Flask
    from backend.middleware_refactored.caching import set_cache_headers, no_cache
    
    app = Flask(__name__)
    
    @app.route('/api/data')
    @no_cache
    def get_data():
        return {'data': 'example'}
    
    @app.route('/static/style.css')
    @set_cache_headers(max_age=31536000)  # 1 年
    def get_css():
        ...
"""

import logging
import hashlib
from datetime import datetime, timedelta
from flask import Response, request

logger = logging.getLogger(__name__)


class CacheHeaderManager:
    """缓存头管理器"""
    
    @staticmethod
    def set_cache_control(
        response: Response,
        max_age: int = 3600,
        public: bool = True,
        must_revalidate: bool = False,
    ) -> Response:
        """
        设置 Cache-Control 响应头
        
        Args:
            response: Flask 响应对象
            max_age: 缓存有效期（秒）
            public: 是否公开缓存（True 允许所有客户端缓存，False 仅用户缓存）
            must_revalidate: 是否强制重新验证
            
        Returns:
            更新后的响应对象
            
        示例:
            @app.after_request
            def cache_response(response):
                return CacheHeaderManager.set_cache_control(
                    response,
                    max_age=3600,
                    public=True
                )
        """
        cache_control_parts = []
        
        # 缓存类型
        if public:
            cache_control_parts.append('public')
        else:
            cache_control_parts.append('private')
        
        # 缓存有效期
        cache_control_parts.append(f'max-age={max_age}')
        
        # 强制重新验证
        if must_revalidate:
            cache_control_parts.append('must-revalidate')
        
        cache_control = ', '.join(cache_control_parts)
        response.headers['Cache-Control'] = cache_control
        
        logger.debug(f"Set Cache-Control: {cache_control}")
        
        return response
    
    @staticmethod
    def set_etag(response: Response) -> Response:
        """
        设置 ETag 响应头（资源唯一标识）
        
        ETag 用于强验证，浏览器会在请求时发送 If-None-Match,
        服务器比较 ETag，如果相同则返回 304 Not Modified
        
        Args:
            response: Flask 响应对象
            
        Returns:
            更新后的响应对象
            
        示例:
            @app.after_request
            def set_etag_header(response):
                return CacheHeaderManager.set_etag(response)
        """
        data = response.get_data()
        
        # 生成 ETag (MD5 哈希值)
        etag = hashlib.md5(data).hexdigest()
        response.headers['ETag'] = f'"{etag}"'
        
        # 检查 If-None-Match（客户端缓存的 ETag）
        if request.headers.get('If-None-Match') == f'"{etag}"':
            logger.debug(f"ETag match: returning 304 Not Modified")
            response.status_code = 304
            response.set_data('')  # 清空响应体
        
        return response
    
    @staticmethod
    def set_last_modified(response: Response, modified_time: datetime = None) -> Response:
        """
        设置 Last-Modified 响应头（弱验证）
        
        Args:
            response: Flask 响应对象
            modified_time: 资源修改时间，默认为当前时间
            
        Returns:
            更新后的响应对象
            
        示例:
            from datetime import datetime
            
            @app.route('/api/data')
            def get_data():
                response = make_response({'data': 'example'})
                modified_time = datetime(2026, 1, 1, 12, 0, 0)
                return CacheHeaderManager.set_last_modified(response, modified_time)
        """
        if modified_time is None:
            modified_time = datetime.utcnow()
        
        # RFC 1123 格式: 'Mon, 01 Jan 2026 00:00:00 GMT'
        last_modified = modified_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers['Last-Modified'] = last_modified
        
        # 检查 If-Modified-Since（客户端缓存的时间）
        if_modified_since = request.headers.get('If-Modified-Since')
        if if_modified_since:
            try:
                client_time = datetime.strptime(
                    if_modified_since,
                    '%a, %d %b %Y %H:%M:%S GMT'
                )
                
                if client_time >= modified_time:
                    logger.debug("Not modified since client cache time: returning 304")
                    response.status_code = 304
                    response.set_data('')
            except ValueError:
                logger.warning(f"Invalid If-Modified-Since: {if_modified_since}")
        
        return response


def no_cache(fn=None):
    """
    禁用缓存装饰器
    
    用于需要实时更新的端点（如 API）
    
    使用方式:
        @app.route('/api/status')
        @no_cache
        def get_status():
            return {'status': 'ok'}
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # 转换为 Flask Response 对象
            if not isinstance(response, Response):
                from flask import make_response
                response = make_response(response)
            
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            logger.debug(f"No-cache applied to {f.__name__}")
            
            return response
        
        wrapper.__name__ = f.__name__
        return wrapper
    
    if fn is None:
        return decorator
    else:
        return decorator(fn)


def set_cache_headers(max_age: int = 3600, public: bool = True):
    """
    设置缓存头装饰器
    
    Args:
        max_age: 缓存有效期（秒）
        public: 是否公开缓存
        
    使用方式:
        @app.route('/static/script.js')
        @set_cache_headers(max_age=31536000)  # 1 年
        def get_js():
            ...
        
        @app.route('/api/data')
        @set_cache_headers(max_age=300, public=False)  # 5 分钟，仅用户缓存
        def get_data():
            ...
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)
            
            # 转换为 Flask Response 对象
            if not isinstance(response, Response):
                from flask import make_response
                response = make_response(response)
            
            # 设置缓存头
            response = CacheHeaderManager.set_cache_control(
                response,
                max_age=max_age,
                public=public
            )
            
            # 添加 ETag
            response = CacheHeaderManager.set_etag(response)
            
            logger.debug(f"Cache headers applied to {fn.__name__}: max_age={max_age}")
            
            return response
        
        wrapper.__name__ = fn.__name__
        return wrapper
    
    return decorator


def get_cache_expiration_time(max_age: int) -> datetime:
    """
    计算缓存过期时间
    
    Args:
        max_age: 缓存有效期（秒）
        
    Returns:
        过期时间 datetime 对象
        
    示例:
        >>> expiration = get_cache_expiration_time(3600)
        >>> print(expiration)
        2026-01-17 14:30:00  # 假设当前时间是 13:30:00
    """
    return datetime.utcnow() + timedelta(seconds=max_age)
