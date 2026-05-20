"""
压缩模块导出

导出主要的压缩相关类和函数
"""

from .gzip_compressor import (
    GzipCompressor,
    register_gzip_compression,
    get_compression_stats,
)

__all__ = [
    'GzipCompressor',
    'register_gzip_compression',
    'get_compression_stats',
]
