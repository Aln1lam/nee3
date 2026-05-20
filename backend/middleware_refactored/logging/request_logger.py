"""
请求日志记录器

记录所有 HTTP 请求和响应信息，用于调试和监控
"""

import logging
import time
from flask import request

logger = logging.getLogger(__name__)


class RequestLogger:
    """
    请求和响应日志记录器
    
    功能：
    - 记录请求方法、路径、参数
    - 记录响应状态码和耗时
    - 支持详细和简洁两种模式
    """
    
    # 日志级别配置
    DEBUG_MODE = True  # 开发环境下启用详细日志
    
    @staticmethod
    def log_request():
        """
        在请求前记录请求信息
        
        记录内容：
        - HTTP 方法
        - 请求路径
        - 请求参数
        - 客户端 IP
        - User-Agent
        """
        request.start_time = time.time()
        
        # 基础信息
        logger.debug(f"→ {request.method} {request.path}")
        
        # 记录查询参数
        if request.args:
            logger.debug(f"  Query: {dict(request.args)}")
        
        # 记录请求体（仅限 POST/PUT/PATCH）
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                data = request.get_data(as_text=True)
                if data and len(data) < 500:
                    logger.debug(f"  Body: {data[:200]}")
            except Exception:
                pass
        
        # 记录请求头
        if RequestLogger.DEBUG_MODE:
            logger.debug(f"  Client: {request.remote_addr}")
            logger.debug(f"  User-Agent: {request.headers.get('User-Agent', 'N/A')[:80]}")
    
    @staticmethod
    def log_response(response):
        """
        在响应后记录响应信息
        
        记录内容：
        - 响应状态码
        - 响应耗时
        - 响应大小
        - 所有处理信息
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # 根据状态码选择日志级别
            if response.status_code >= 500:
                log_func = logger.error
                status_icon = "✗"
            elif response.status_code >= 400:
                log_func = logger.warning
                status_icon = "⚠"
            elif response.status_code >= 300:
                log_func = logger.info
                status_icon = "→"
            else:
                log_func = logger.debug
                status_icon = "✓"
            
            # 获取响应大小（需要处理直接传递模式）
            try:
                # 如果响应处于直接传递模式，使用 content_length
                if hasattr(response, 'direct_passthrough') and response.direct_passthrough:
                    response_size = response.content_length or 0
                else:
                    response_data = response.get_data()
                    response_size = len(response_data) if response_data else 0
            except (RuntimeError, AttributeError):
                # 如果无法获取数据，使用 content_length 或 0
                response_size = response.content_length or 0
            
            log_func(
                f"{status_icon} {request.method} {request.path} - "
                f"[{response.status_code}] "
                f"{duration:.3f}s "
                f"({response_size} bytes)"
            )
        
        return response
    
    @staticmethod
    def log_error(error, status_code=500):
        """
        记录错误信息
        
        Args:
            error: 异常对象
            status_code: HTTP 状态码
        """
        logger.error(
            f"✗ {request.method} {request.path} - "
            f"[{status_code}] {str(error)}",
            exc_info=True
        )


def enable_request_logging():
    """启用请求日志记录"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    logger.info("Request logging enabled")


def disable_debug_logging():
    """禁用详细日志（生产环境）"""
    RequestLogger.DEBUG_MODE = False
    logger.info("Debug logging disabled (production mode)")
