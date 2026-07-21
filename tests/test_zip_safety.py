"""ZIP 安全校验单测。"""
import io
import zipfile
import pytest

from backend.services.zip_safety import (
    ZipSafetyError,
    ZipLimits,
    validate_zip_bytes,
    inspect_zip,
)


def _make_zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_accepts_normal_zip():
    data = _make_zip({"readme.md": b"# hi", "a.png": b"\x89PNG\r\n"})
    validate_zip_bytes(data, allow_ext={"md", "png"})


def test_rejects_path_traversal():
    data = _make_zip({"../evil.md": b"x"})
    with pytest.raises(ZipSafetyError, match="穿越"):
        validate_zip_bytes(data)


def test_rejects_absolute_path():
    data = _make_zip({"/tmp/x.md": b"x"})
    with pytest.raises(ZipSafetyError):
        validate_zip_bytes(data)


def test_rejects_zip_bomb_ratio():
    # 高度可压缩内容
    payload = b"A" * (2 * 1024 * 1024)
    data = _make_zip({"big.txt": payload})
    with pytest.raises(ZipSafetyError):
        validate_zip_bytes(
            data,
            limits=ZipLimits(
                max_compressed=5 * 1024 * 1024,
                max_uncompressed=10 * 1024 * 1024,
                max_ratio=5,
                max_single_file=10 * 1024 * 1024,
            ),
            allow_ext={"txt"},
        )


def test_rejects_too_many_files():
    entries = {f"f{i}.md": b"x" for i in range(10)}
    data = _make_zip(entries)
    with pytest.raises(ZipSafetyError, match="文件数"):
        validate_zip_bytes(data, limits=ZipLimits(max_files=5), allow_ext={"md"})


def test_rejects_disallowed_ext():
    data = _make_zip({"shell.php": b"<?php"})
    with pytest.raises(ZipSafetyError, match="不允许"):
        validate_zip_bytes(data, allow_ext={"md", "png"})


def test_rejects_non_zip_bytes():
    with pytest.raises(ZipSafetyError, match="不是有效"):
        validate_zip_bytes(b"not-a-zip")
