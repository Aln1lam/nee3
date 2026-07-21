"""
速率限制装饰器

提供 Flask 路由装饰器形式的速率限制功能
"""

from functools import wraps
from flask import request, make_response
from flask_jwt_extended import get_jwt_identity
from .rate_limiter import rate_limiter, get_active_limiter, configure_redis_rate_limiter


def rate_limit(
    key_func=None,
    max_requests: int = 100,
    window_seconds: int = 60,
    error_message: str = "Too many requests"
):
    """
    通用速率限制装饰器
    
    对 Flask 路由应用速率限制
    
    Args:
        key_func: 获取限制键的函数，默认使用客户端 IP
        max_requests: 时间窗口内的最大请求数（默认 100）
        window_seconds: 时间窗口秒数（默认 60）
        error_message: 超出限制时的错误信息
    
    使用示例：
        # 基于 IP 的限制：100 请求/分钟
        @rate_limit(max_requests=100, window_seconds=60)
        def api_endpoint():
            return {'data': 'success'}
        
        # 基于用户 ID 的限制
        @rate_limit(
            key_func=lambda: get_jwt_identity(),
            max_requests=10,
            window_seconds=60
        )
        def user_endpoint():
            return {'data': 'success'}
        
        # 自定义限制键
        @rate_limit(
            key_func=lambda: f"{request.remote_addr}:{request.endpoint}",
            max_requests=50,
            window_seconds=60
        )
        def expensive_operation():
            return {'data': 'computed'}
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 获取限制键
            if key_func:
                try:
                    key = key_func()
                except Exception:
                    key = request.remote_addr
            else:
                key = request.remote_addr
            
            # 检查速率限制
            limiter = get_active_limiter()
            if not limiter.is_allowed(key, max_requests, window_seconds):
                remaining = limiter.get_remaining(key, max_requests, window_seconds)
                reset_time = limiter.get_reset_time(key, window_seconds)
                
                response = make_response({
                    'error': 'rate_limit_exceeded',
                    'message': error_message
                }, 429)
                
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(reset_time))
                
                return response
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def submission_rate_limit():
    """
    提交限制装饰器
    
    限制：每个用户每分钟最多提交 5 次 Flag
    
    使用示例：
        @submission_rate_limit()
        def submit_flag():
            return {'success': True}
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                if not user_id:
                    return {'error': 'Unauthorized'}, 401
            except Exception:
                return {'error': 'Unauthorized'}, 401
            
            key = f"submission:{user_id}"
            
            limiter = get_active_limiter()
            if not limiter.is_allowed(key, max_requests=5, window_seconds=60):
                remaining = limiter.get_remaining(key, 5, 60)
                reset_time = limiter.get_reset_time(key, 60)
                
                response = make_response({
                    'error': 'submission_rate_limit_exceeded',
                    'message': 'You can submit at most 5 times per minute'
                }, 429)
                
                response.headers['X-RateLimit-Limit'] = '5'
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(reset_time))
                
                return response
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def login_rate_limit():
    """
    登录限制装饰器
    
    限制：每个 IP 地址每分钟最多 5 次登录尝试
    防止暴力破解
    
    使用示例：
        @login_rate_limit()
        def login():
            return {'token': 'jwt_token'}
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"login:{request.remote_addr}"
            
            limiter = get_active_limiter()
            if not limiter.is_allowed(key, max_requests=5, window_seconds=60):
                remaining = limiter.get_remaining(key, 5, 60)
                reset_time = limiter.get_reset_time(key, 60)
                
                response = make_response({
                    'error': 'login_rate_limit_exceeded',
                    'message': 'Too many login attempts. Please try again later.'
                }, 429)
                
                response.headers['X-RateLimit-Limit'] = '5'
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(reset_time))
                
                return response
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator


def custom_rate_limit(
    key_prefix: str,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """
    自定义限制装饰器工厂
    
    创建一个自定义的速率限制装饰器
    
    Args:
        key_prefix: 限制键前缀
        max_requests: 最大请求数
        window_seconds: 时间窗口
    
    使用示例：
        download_limiter = custom_rate_limit('download', max_requests=3, window_seconds=3600)
        
        @download_limiter
        def download_file():
            return send_file('file.zip')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            key = f"{key_prefix}:{user_id or request.remote_addr}"
            
            limiter = get_active_limiter()
            if not limiter.is_allowed(key, max_requests, window_seconds):
                return {
                    'error': 'rate_limit_exceeded',
                    'message': f'Rate limit exceeded for {key_prefix}'
                }, 429
            
            return fn(*args, **kwargs)
        
        return wrapper
    
    return decorator
