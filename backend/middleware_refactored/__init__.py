"""
Neepu 中间件模块化包

将原始的 middleware.py 拆分为 6 个独立模块:
1. rate_limiting  - 速率限制
2. logging        - 请求日志
3. compression    - 响应压缩  
4. security       - 安全头
5. caching        - 缓存控制
6. error_handling - 错误处理

【使用示例】

# 方式 1: 从包导入
from backend.middleware_refactored import (
    rate_limit,
    submission_rate_limit,
    RequestLogger,
)

# 方式 2: 从子模块导入  
from backend.middleware_refactored.rate_limiting import rate_limit
from backend.middleware_refactored.logging import RequestLogger

# 方式 3: 在 Flask 应用中初始化（推荐）
from backend.middleware_refactored import init_all_middleware

app = Flask(__name__)
init_all_middleware(app)
"""

import logging as _logging

# ==================== Rate Limiting ====================
from .rate_limiting import (
    RateLimiter,
    rate_limiter,
    rate_limit,
    submission_rate_limit,
    login_rate_limit,
    TokenBucketStrategy,
)

# ==================== Logging ====================
from .logging import (
    RequestLogger,
)

# ==================== Compression ====================
from .compression import (
    GzipCompressor,
    register_gzip_compression,
    get_compression_stats,
)

# ==================== Security ====================
from .security import (
    SecurityHeaderManager,
    register_security_headers,
    add_hsts_header,
    remove_header,
)

# ==================== Caching ====================
from .caching import (
    CacheHeaderManager,
    no_cache,
    set_cache_headers,
    get_cache_expiration_time,
)

# ==================== Error Handling ====================
from .error_handling import (
    ErrorHandler,
    register_error_handlers,
    make_error_response,
)

__all__ = [
    # Rate Limiting
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'submission_rate_limit',
    'login_rate_limit',
    'TokenBucketStrategy',
    
    # Logging
    'RequestLogger',
    
    # Compression
    'GzipCompressor',
    'register_gzip_compression',
    'get_compression_stats',
    
    # Security
    'SecurityHeaderManager',
    'register_security_headers',
    'add_hsts_header',
    'remove_header',
    
    # Caching
    'CacheHeaderManager',
    'no_cache',
    'set_cache_headers',
    'get_cache_expiration_time',
    
    # Error Handling
    'ErrorHandler',
    'register_error_handlers',
    'make_error_response',
    
    # Init function
    'init_all_middleware',
]

logger = _logging.getLogger(__name__)


def init_all_middleware(app, enable_compression: bool = True, security_policy: str = 'moderate') -> None:
    """
    初始化所有中间件
    
    这个函数应该在 Flask 应用创建后立即调用
    
    Args:
        app: Flask 应用实例
        enable_compression: 是否启用响应压缩（默认 True）
        security_policy: 安全策略级别 ('strict', 'moderate', 'permissive', 默认 'moderate')
    
    使用示例:
        from flask import Flask
        from backend.middleware_refactored import init_all_middleware
        
        app = Flask(__name__)
        
        # 使用默认配置
        init_all_middleware(app)
        
        # 或自定义配置
        init_all_middleware(
            app,
            enable_compression=True,
            security_policy='strict'
        )
        
        @app.route('/api/data')
        def get_data():
            return {'data': 'example'}
    
    此后，所有中间件功能将自动启用:
    ✓ 请求日志记录
    ✓ 安全头添加（XSS/MIME/点击劫持防护）
    ✓ 缓存控制（ETag/Cache-Control）
    ✓ 响应压缩（Gzip）
    ✓ 错误统一处理
    ✓ 速率限制装饰器可用
    """
    
    # 1. 错误处理（必须首先注册，以便捕获其他中间件的错误）
    register_error_handlers(app)
    logger.info("✓ Error handling registered")
    
    # 2. 请求日志
    app.before_request(RequestLogger.log_request)
    app.after_request(RequestLogger.log_response)
    logger.info("✓ Request logging enabled")
    
    # 3. 安全头
    register_security_headers(app, policy_level=security_policy)
    logger.info(f"✓ Security headers enabled (policy: {security_policy})")
    
    # 4. 响应压缩（可选）
    if enable_compression:
        register_gzip_compression(app)
        logger.info("✓ Response compression enabled")
    else:
        logger.info("⊘ Response compression disabled")
    
    logger.info("=" * 50)
    logger.info("All middleware initialized successfully! ✓")
    logger.info("=" * 50)
    logger.info(f"  Rate limiting: Available via @rate_limit decorator")
    logger.info(f"  Logging: Automatic for all requests")
    logger.info(f"  Security: {security_policy.upper()} CSP policy applied")
    logger.info(f"  Compression: {'Enabled' if enable_compression else 'Disabled'}")
    logger.info(f"  Caching: Available via @no_cache or @set_cache_headers")
    logger.info(f"  Error handling: Automatic for all errors")
    logger.info("=" * 50)
