"""
错误处理模块

功能: 统一处理 HTTP 错误和异常

错误映射:
- 400 Bad Request: 请求参数错误
- 401 Unauthorized: 认证失败
- 403 Forbidden: 无权限访问
- 404 Not Found: 资源不存在
- 429 Too Many Requests: 超过速率限制
- 500 Internal Server Error: 服务器异常

统一响应格式:
    {
        "error": "error_code",
        "message": "Human readable message",
        "details": {...}  // 可选
    }

使用方式:
    from flask import Flask
    from backend.middleware_refactored.error_handling import register_error_handlers
    
    app = Flask(__name__)
    register_error_handlers(app)
"""

import logging
from flask import jsonify

logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器"""
    
    # 错误消息模板
    ERROR_MESSAGES = {
        400: {
            'error': 'bad_request',
            'message': 'The request contains invalid parameters',
        },
        401: {
            'error': 'unauthorized',
            'message': 'Authentication required. Please log in',
        },
        403: {
            'error': 'forbidden',
            'message': 'You do not have permission to access this resource',
        },
        404: {
            'error': 'not_found',
            'message': 'The requested resource was not found',
        },
        429: {
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests. Please try again later',
        },
        500: {
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred on the server',
        },
    }
    
    @staticmethod
    def create_error_response(status_code: int, message: str = None, details: dict = None) -> tuple:
        """
        创建统一格式的错误响应
        
        Args:
            status_code: HTTP 状态码
            message: 自定义错误消息
            details: 额外的错误详情
            
        Returns:
            (响应体, 状态码) 元组
            
        示例:
            body, code = ErrorHandler.create_error_response(
                404,
                message='User not found',
                details={'user_id': 123}
            )
            return body, code
        """
        # 获取默认错误信息
        if status_code in ErrorHandler.ERROR_MESSAGES:
            error_info = ErrorHandler.ERROR_MESSAGES[status_code].copy()
        else:
            error_info = {
                'error': 'unknown_error',
                'message': 'An unknown error occurred',
            }
        
        # 覆盖消息（如果提供）
        if message:
            error_info['message'] = message
        
        # 添加详情
        if details:
            error_info['details'] = details
        
        # 添加状态码
        error_info['status_code'] = status_code
        
        return error_info, status_code
    
    @staticmethod
    def log_error(status_code: int, error, message: str = None) -> None:
        """
        记录错误
        
        Args:
            status_code: HTTP 状态码
            error: 原始错误对象或异常
            message: 自定义消息
        """
        error_message = message or str(error)
        
        if status_code >= 500:
            # 服务器错误：使用 error 日志
            logger.error(
                f"HTTP {status_code}: {error_message}",
                exc_info=True if hasattr(error, '__traceback__') else False
            )
        elif status_code >= 400:
            # 客户端错误：使用 warning 日志
            logger.warning(f"HTTP {status_code}: {error_message}")
        else:
            # 其他（不应该出现）
            logger.info(f"HTTP {status_code}: {error_message}")


def register_error_handlers(app) -> None:
    """
    为 Flask 应用注册错误处理器
    
    Args:
        app: Flask 应用实例
        
    使用方式:
        from flask import Flask
        from backend.middleware_refactored.error_handling import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理 400 Bad Request"""
        body, code = ErrorHandler.create_error_response(400, str(error))
        ErrorHandler.log_error(400, error)
        return jsonify(body), code
    
    @app.errorhandler(401)
    def unauthorized(error):
        """处理 401 Unauthorized"""
        body, code = ErrorHandler.create_error_response(401, str(error))
        ErrorHandler.log_error(401, error)
        return jsonify(body), code
    
    @app.errorhandler(403)
    def forbidden(error):
        """处理 403 Forbidden"""
        body, code = ErrorHandler.create_error_response(403, str(error))
        ErrorHandler.log_error(403, error)
        return jsonify(body), code
    
    @app.errorhandler(404)
    def not_found(error):
        """处理 404 Not Found"""
        body, code = ErrorHandler.create_error_response(404, str(error))
        ErrorHandler.log_error(404, error)
        return jsonify(body), code
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """处理 429 Too Many Requests"""
        body, code = ErrorHandler.create_error_response(
            429,
            'Too many requests. Please try again later',
            {'retry_after': 60}
        )
        ErrorHandler.log_error(429, error)
        return jsonify(body), code
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """处理 500 Internal Server Error"""
        body, code = ErrorHandler.create_error_response(
            500,
            'An unexpected error occurred'
        )
        ErrorHandler.log_error(500, error)
        return jsonify(body), code
    
    logger.info("Error handlers registered")


def make_error_response(status_code: int, error_code: str, message: str = None, details: dict = None) -> tuple:
    """
    快速创建错误响应
    
    Args:
        status_code: HTTP 状态码
        error_code: 应用级错误代码
        message: 错误消息
        details: 额外详情
        
    Returns:
        (响应体, 状态码) 元组
        
    示例:
        return make_error_response(
            400,
            'validation_error',
            'Email format is invalid',
            {'field': 'email'}
        )
    """
    response = {
        'error': error_code,
        'message': message or 'An error occurred',
        'status_code': status_code,
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code
