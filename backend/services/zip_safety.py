"""ZIP 上传安全校验：防炸弹、路径穿越、符号链接、超限条目。"""
from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass
from typing import BinaryIO, Optional, Set, Tuple, Union


# 压缩包本身上限（与多数上传接口对齐，可用环境变量覆盖）
DEFAULT_MAX_COMPRESSED = int(os.environ.get("NEPU_ZIP_MAX_COMPRESSED", str(20 * 1024 * 1024)))
DEFAULT_MAX_UNCOMPRESSED = int(os.environ.get("NEPU_ZIP_MAX_UNCOMPRESSED", str(80 * 1024 * 1024)))
DEFAULT_MAX_RATIO = float(os.environ.get("NEPU_ZIP_MAX_RATIO", "40"))
DEFAULT_MAX_FILES = int(os.environ.get("NEPU_ZIP_MAX_FILES", "200"))
DEFAULT_MAX_SINGLE = int(os.environ.get("NEPU_ZIP_MAX_SINGLE_FILE", str(20 * 1024 * 1024)))

ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


class ZipSafetyError(ValueError):
    """不可接受的 ZIP。"""


@dataclass
class ZipLimits:
    max_compressed: int = DEFAULT_MAX_COMPRESSED
    max_uncompressed: int = DEFAULT_MAX_UNCOMPRESSED
    max_ratio: float = DEFAULT_MAX_RATIO
    max_files: int = DEFAULT_MAX_FILES
    max_single_file: int = DEFAULT_MAX_SINGLE


def looks_like_zip(header: bytes) -> bool:
    return any(header.startswith(m) for m in ZIP_MAGIC)


def _safe_member_name(name: str) -> str:
    if not name or name.endswith("/"):
        return ""
    # null / 绝对路径 / Windows 盘符
    if "\x00" in name:
        raise ZipSafetyError("ZIP 成员名含非法字符")
    norm = name.replace("\\", "/")
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":"):
        raise ZipSafetyError("禁止绝对路径成员")
    parts = [p for p in norm.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise ZipSafetyError("禁止路径穿越成员 (..)")
    if not parts:
        raise ZipSafetyError("非法成员名")
    return "/".join(parts)


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    # Unix external_attr: upper 16 bits are mode
    return ((info.external_attr >> 16) & 0o170000) == 0o120000


def inspect_zip(
    source: Union[str, bytes, BinaryIO],
    *,
    limits: Optional[ZipLimits] = None,
    allow_ext: Optional[Set[str]] = None,
) -> Tuple[int, int, int]:
    """
    校验 ZIP。返回 (file_count, compressed_total, uncompressed_total)。
    allow_ext: 若给定，则非目录成员扩展名必须在集合内（小写，无点）。
    """
    limits = limits or ZipLimits()

    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
        compressed_size = len(data)
        if compressed_size > limits.max_compressed:
            raise ZipSafetyError(f"ZIP 过大（上限 {limits.max_compressed} 字节）")
        if not looks_like_zip(data[:4]):
            raise ZipSafetyError("不是有效的 ZIP 文件")
        opener = lambda: zipfile.ZipFile(io.BytesIO(data), "r")
    elif hasattr(source, "read"):
        pos = source.tell()
        header = source.read(4)
        source.seek(pos)
        if not looks_like_zip(header):
            raise ZipSafetyError("不是有效的 ZIP 文件")
        # 尽量取长度
        try:
            source.seek(0, os.SEEK_END)
            compressed_size = source.tell()
            source.seek(pos)
        except Exception:
            compressed_size = 0
        if compressed_size and compressed_size > limits.max_compressed:
            raise ZipSafetyError(f"ZIP 过大（上限 {limits.max_compressed} 字节）")
        opener = lambda: zipfile.ZipFile(source, "r")
    else:
        path = str(source)
        compressed_size = os.path.getsize(path)
        if compressed_size > limits.max_compressed:
            raise ZipSafetyError(f"ZIP 过大（上限 {limits.max_compressed} 字节）")
        with open(path, "rb") as fh:
            if not looks_like_zip(fh.read(4)):
                raise ZipSafetyError("不是有效的 ZIP 文件")
        opener = lambda: zipfile.ZipFile(path, "r")

    try:
        zf = opener()
    except zipfile.BadZipFile as exc:
        raise ZipSafetyError("损坏的 ZIP 文件") from exc

    file_count = 0
    uncompressed_total = 0
    try:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if _is_symlink(info):
                raise ZipSafetyError("禁止 ZIP 内符号链接")
            safe = _safe_member_name(info.filename)
            if allow_ext is not None:
                ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
                if ext not in allow_ext:
                    raise ZipSafetyError(f"ZIP 内不允许的文件类型: .{ext or '?'}")
            file_count += 1
            if file_count > limits.max_files:
                raise ZipSafetyError(f"ZIP 文件数超限（上限 {limits.max_files}）")
            usize = int(info.file_size or 0)
            if usize < 0:
                raise ZipSafetyError("非法未压缩大小")
            if usize > limits.max_single_file:
                raise ZipSafetyError(f"单个成员过大（上限 {limits.max_single_file} 字节）")
            uncompressed_total += usize
            if uncompressed_total > limits.max_uncompressed:
                raise ZipSafetyError(f"解压后总体过大（上限 {limits.max_uncompressed} 字节）")
            csize = int(info.compress_size or 0) or 1
            if usize / csize > limits.max_ratio and usize > 1024 * 1024:
                raise ZipSafetyError("压缩比异常，疑似 ZIP 炸弹")
        if compressed_size and uncompressed_total / max(compressed_size, 1) > limits.max_ratio:
            if uncompressed_total > 1024 * 1024:
                raise ZipSafetyError("整体压缩比异常，疑似 ZIP 炸弹")
    finally:
        zf.close()

    return file_count, compressed_size, uncompressed_total


def validate_zip_bytes(data: bytes, *, limits: Optional[ZipLimits] = None, allow_ext: Optional[Set[str]] = None) -> None:
    inspect_zip(data, limits=limits, allow_ext=allow_ext)


def validate_zip_path(path: str, *, limits: Optional[ZipLimits] = None, allow_ext: Optional[Set[str]] = None) -> None:
    inspect_zip(path, limits=limits, allow_ext=allow_ext)


def safe_read_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, max_bytes: int) -> Tuple[bytes, str]:
    """带上限读取单个成员，防止声明 size 很小但实际膨胀。"""
    safe = _safe_member_name(info.filename)
    if _is_symlink(info):
        raise ZipSafetyError("禁止 ZIP 内符号链接")
    if int(info.file_size or 0) > max_bytes:
        raise ZipSafetyError("成员过大")
    with zf.open(info, "r") as fh:
        chunks = []
        total = 0
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ZipSafetyError("成员实际大小超限")
            chunks.append(chunk)
    return b"".join(chunks), safe
