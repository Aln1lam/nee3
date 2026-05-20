"""
Gzip 响应压缩模块

功能: 对 HTTP 响应体进行 Gzip 压缩，减小网络传输大小
- JSON 数据: 减小 60-80%
- HTML 文档: 减小 70-90%
- 图片等二进制: 无法压缩

使用方式:
    from flask import Flask
    from backend.middleware_refactored.compression import register_gzip_compression
    
    app = Flask(__name__)
    register_gzip_compression(app)
"""

import gzip
import logging
from typing import Optional
from flask import Response

logger = logging.getLogger(__name__)


class GzipCompressor:
    """Gzip 响应压缩器"""
    
    # 最小压缩大小（字节）- 小于此值不压缩
    MIN_SIZE = 500
    
    # 可压缩的内容类型
    COMPRESSIBLE_TYPES = [
        'application/json',
        'text/plain',
        'text/html',
        'text/css',
        'application/javascript',
        'text/xml',
        'application/xml',
        'application/xml+rss',
    ]
    
    @classmethod
    def compress_response(cls, response: Response) -> Response:
        """
        对响应进行 Gzip 压缩
        
        Args:
            response: Flask 响应对象
            
        Returns:
            压缩后的响应对象
            
        示例:
            @app.after_request
            def compress(response):
                return GzipCompressor.compress_response(response)
        """
        # 检查是否应该压缩
        if not cls._should_compress(response):
            return response
        
        # 压缩响应
        try:
            gzip_data = gzip.compress(response.get_data(), compresslevel=6)
            
            # 更新响应
            response.set_data(gzip_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(gzip_data)
            
            logger.debug(
                f"Compressed response: "
                f"{len(response.get_data())} → {len(gzip_data)} bytes"
            )
            
        except Exception as e:
            logger.warning(f"Gzip compression failed: {e}")
        
        return response
    
    @classmethod
    def _should_compress(cls, response: Response) -> bool:
        """
        判断是否应该压缩响应
        
        检查以下条件:
        1. 内容类型是否可压缩
        2. 响应大小是否超过最小值
        3. 响应是否已压缩
        
        Args:
            response: Flask 响应对象
            
        Returns:
            是否应该压缩
        """
        # 1. 检查内容类型
        content_type = response.headers.get('Content-Type', '').lower()
        
        if not cls._is_compressible_type(content_type):
            logger.debug(f"Skipping compression for content-type: {content_type}")
            return False
        
        # 2. 检查大小
        content_length = len(response.get_data())
        if content_length < cls.MIN_SIZE:
            logger.debug(
                f"Skipping compression: "
                f"size ({content_length}) < MIN_SIZE ({cls.MIN_SIZE})"
            )
            return False
        
        # 3. 检查是否已压缩
        if response.headers.get('Content-Encoding'):
            logger.debug(
                f"Already compressed: "
                f"{response.headers.get('Content-Encoding')}"
            )
            return False
        
        return True
    
    @classmethod
    def _is_compressible_type(cls, content_type: str) -> bool:
        """
        检查内容类型是否可压缩
        
        Args:
            content_type: Content-Type 响应头值
            
        Returns:
            是否可压缩
        """
        for compressible in cls.COMPRESSIBLE_TYPES:
            if compressible in content_type:
                return True
        
        return False


def register_gzip_compression(app) -> None:
    """
    为 Flask 应用注册 Gzip 压缩
    
    Args:
        app: Flask 应用实例
        
    使用方式:
        from flask import Flask
        from backend.middleware_refactored.compression import register_gzip_compression
        
        app = Flask(__name__)
        register_gzip_compression(app)
    """
    @app.after_request
    def compress(response):
        return GzipCompressor.compress_response(response)
    
    logger.info("Gzip compression registered")


def get_compression_stats(original_size: int, compressed_size: int) -> dict:
    """
    获取压缩统计信息
    
    Args:
        original_size: 原始大小（字节）
        compressed_size: 压缩后大小（字节）
        
    Returns:
        包含压缩比、节省等信息的字典
        
    示例:
        >>> stats = get_compression_stats(1000, 300)
        >>> print(stats)
        {
            'original': 1000,
            'compressed': 300,
            'ratio': 0.30,
            'saved': 700,
            'saved_percent': 70.0
        }
    """
    if original_size == 0:
        return {
            'original': 0,
            'compressed': 0,
            'ratio': 0,
            'saved': 0,
            'saved_percent': 0,
        }
    
    saved = original_size - compressed_size
    saved_percent = (saved / original_size) * 100
    ratio = compressed_size / original_size
    
    return {
        'original': original_size,
        'compressed': compressed_size,
        'ratio': round(ratio, 2),
        'saved': saved,
        'saved_percent': round(saved_percent, 1),
    }
