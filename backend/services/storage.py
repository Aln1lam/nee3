# -*- coding: utf-8 -*-
"""上传存储抽象：默认本地，可切换 S3/MinIO 兼容。"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

from backend.server.config import settings

logger = logging.getLogger(__name__)

BytesLike = Union[bytes, bytearray, memoryview]


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: Union[BytesLike, BinaryIO], content_type: str = "") -> Tuple[str, str]:
        """保存对象。返回 (storage_path, public_url)。"""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    def absolute_path(self, key: str) -> Optional[str]:
        """本地后端返回绝对路径；对象存储返回 None。"""
        return None


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Optional[str] = None, url_prefix: Optional[str] = None):
        self.root = Path(root or settings.STORAGE_LOCAL_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.url_prefix = (url_prefix or settings.STORAGE_PUBLIC_URL_PREFIX).rstrip("/")

    def _resolve(self, key: str) -> Path:
        safe = key.replace("\\", "/").lstrip("/")
        full = (self.root / safe).resolve()
        if not str(full).startswith(str(self.root)):
            raise ValueError("非法存储路径")
        return full

    def save(self, key: str, data: Union[BytesLike, BinaryIO], content_type: str = "") -> Tuple[str, str]:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(data, "read"):
            with open(path, "wb") as fh:
                while True:
                    chunk = data.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
        else:
            path.write_bytes(bytes(data))
        url = f"{self.url_prefix}/{key.replace(chr(92), '/').lstrip('/')}"
        return str(path), url

    def open(self, key: str) -> BinaryIO:
        return open(self._resolve(key), "rb")

    def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def absolute_path(self, key: str) -> Optional[str]:
        return str(self._resolve(key))


class S3StorageBackend(StorageBackend):
    """可选对象存储；未安装 boto3 或未配置 bucket 时初始化失败。"""

    def __init__(self):
        try:
            import boto3
        except ImportError as e:
            raise RuntimeError("STORAGE_BACKEND=s3 需要安装 boto3") from e
        bucket = settings.STORAGE_S3_BUCKET
        if not bucket:
            raise RuntimeError("STORAGE_S3_BUCKET 未配置")
        kwargs = {}
        if settings.STORAGE_S3_ENDPOINT:
            kwargs["endpoint_url"] = settings.STORAGE_S3_ENDPOINT
        self.client = boto3.client("s3", **kwargs)
        self.bucket = bucket
        self.prefix = (settings.STORAGE_S3_PREFIX or "").lstrip("/")
        self.url_prefix = settings.STORAGE_PUBLIC_URL_PREFIX.rstrip("/")

    def _obj_key(self, key: str) -> str:
        return f"{self.prefix}{key.lstrip('/')}".replace("\\", "/")

    def save(self, key: str, data: Union[BytesLike, BinaryIO], content_type: str = "") -> Tuple[str, str]:
        obj_key = self._obj_key(key)
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        body = data.read() if hasattr(data, "read") else bytes(data)
        self.client.put_object(Bucket=self.bucket, Key=obj_key, Body=body, **extra)
        url = f"{self.url_prefix}/{key.replace(chr(92), '/').lstrip('/')}"
        return f"s3://{self.bucket}/{obj_key}", url

    def open(self, key: str) -> BinaryIO:
        import io
        obj = self.client.get_object(Bucket=self.bucket, Key=self._obj_key(key))
        return io.BytesIO(obj["Body"].read())

    def delete(self, key: str) -> bool:
        self.client.delete_object(Bucket=self.bucket, Key=self._obj_key(key))
        return True

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._obj_key(key))
            return True
        except Exception:
            return False


_storage: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is not None:
        return _storage
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        try:
            _storage = S3StorageBackend()
            logger.info("Storage backend: s3 bucket=%s", settings.STORAGE_S3_BUCKET)
            return _storage
        except Exception as e:
            logger.warning("S3 storage init failed, fallback local: %s", e)
    # 默认本地；若配置路径不存在则回退到 Flask static/uploads
    root = settings.STORAGE_LOCAL_ROOT
    if not os.path.isdir(os.path.dirname(root)) and not os.path.isdir(root):
        alt = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
        root = alt
    _storage = LocalStorageBackend(root=root)
    logger.info("Storage backend: local root=%s", _storage.root)
    return _storage
