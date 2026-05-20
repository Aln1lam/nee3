"""
安全响应头模块

功能: 设置 HTTP 响应头，指导浏览器的安全行为

安全头清单:
- X-Frame-Options: 防止点击劫持 (Clickjacking)
- X-Content-Type-Options: 防止 MIME 嗅探
- Content-Security-Policy: XSS 跨站脚本攻击防护
- Referrer-Policy: 控制 Referrer 信息泄露
- Strict-Transport-Security: 强制 HTTPS

使用方式:
    from flask import Flask
    from backend.middleware_refactored.security import register_security_headers
    
    app = Flask(__name__)
    register_security_headers(app)
"""

import logging
from flask import Response

logger = logging.getLogger(__name__)


class SecurityHeaderManager:
    """安全响应头管理器"""
    
    # 默认安全头配置
    DEFAULT_HEADERS = {
        # 防止点击劫持 - 只允许同源 iframe
        'X-Frame-Options': 'SAMEORIGIN',
        
        # 防止 MIME 嗅探 - 强制按照 Content-Type 解析
        'X-Content-Type-Options': 'nosniff',
        
        # 防止 XSS 攻击（旧浏览器）
        'X-XSS-Protection': '1; mode=block',
        
        # 引用策略 - 限制 Referrer 信息泄露
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # 权限政策（Permissions Policy）- 控制浏览器功能
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    @classmethod
    def add_headers(cls, response: Response, custom_headers: dict = None) -> Response:
        """
        添加安全响应头
        
        Args:
            response: Flask 响应对象
            custom_headers: 自定义头（覆盖默认值）
            
        Returns:
            添加安全头后的响应对象
            
        示例:
            @app.after_request
            def add_security(response):
                return SecurityHeaderManager.add_headers(response)
        """
        # 使用默认头
        headers_to_add = cls.DEFAULT_HEADERS.copy()
        
        # 应用自定义头
        if custom_headers:
            headers_to_add.update(custom_headers)
        
        # 添加到响应
        for header, value in headers_to_add.items():
            response.headers[header] = value
        
        logger.debug(f"Added {len(headers_to_add)} security headers")
        
        return response
    
    @classmethod
    def get_csp_header(cls, policy_level: str = 'strict') -> str:
        """
        获取 Content Security Policy 头值
        
        Args:
            policy_level: 策略等级
                - 'strict': 最严格（推荐用于内容区域）
                - 'moderate': 中等（推荐用于大多数应用）
                - 'permissive': 宽松（仅用于调试）
        
        Returns:
            CSP 头值
            
        示例:
            >>> csp = SecurityHeaderManager.get_csp_header('strict')
            >>> print(csp)
            default-src 'self'; ...
        """
        policies = {
            'strict': (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            'moderate': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            'permissive': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
        }
        
        return policies.get(policy_level, policies['moderate'])


def register_security_headers(app, policy_level: str = 'moderate') -> None:
    """
    为 Flask 应用注册安全响应头
    
    Args:
        app: Flask 应用实例
        policy_level: CSP 策略等级 ('strict', 'moderate', 'permissive')
        
    使用方式:
        from flask import Flask
        from backend.middleware_refactored.security import register_security_headers
        
        app = Flask(__name__)
        register_security_headers(app, policy_level='strict')
    """
    @app.after_request
    def add_security(response):
        # 添加默认安全头
        response = SecurityHeaderManager.add_headers(response)
        
        # 添加 CSP 头
        csp_policy = SecurityHeaderManager.get_csp_header(policy_level)
        response.headers['Content-Security-Policy'] = csp_policy
        
        return response
    
    logger.info(f"Security headers registered with policy level: {policy_level}")


def add_hsts_header(response: Response, max_age: int = 31536000, include_subdomains: bool = True) -> Response:
    """
    添加 HSTS (HTTP Strict Transport Security) 头
    
    强制浏览器使用 HTTPS，防止中间人攻击
    
    Args:
        response: Flask 响应对象
        max_age: 有效期（秒），默认 1 年
        include_subdomains: 是否包含子域名
        
    Returns:
        更新后的响应对象
        
    示例:
        @app.after_request
        def add_hsts(response):
            return add_hsts_header(response)
    """
    hsts_value = f'max-age={max_age}'
    
    if include_subdomains:
        hsts_value += '; includeSubDomains'
    
    response.headers['Strict-Transport-Security'] = hsts_value
    
    logger.debug(f"Added HSTS header: {hsts_value}")
    
    return response


def remove_header(response: Response, header_name: str) -> Response:
    """
    删除响应头（用于移除不需要的头）
    
    Args:
        response: Flask 响应对象
        header_name: 要删除的头名称
        
    Returns:
        更新后的响应对象
        
    示例:
        @app.after_request
        def remove_server_info(response):
            return remove_header(response, 'Server')
    """
    if header_name in response.headers:
        del response.headers[header_name]
        logger.debug(f"Removed header: {header_name}")
    
    return response
