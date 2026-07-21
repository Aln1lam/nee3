"""轮播图：路径规范化、文件校验、公开读序列化与 Redis 缓存载荷。"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from flask import current_app

logger = logging.getLogger(__name__)


def upload_root() -> str:
    return os.path.abspath(os.path.join(current_app.root_path, "static", "uploads"))


def normalize_carousel_image_url(url: Optional[str]) -> str:
    """统一为相对路径 /static/uploads/...，便于入库与跨环境访问。"""
    if not url:
        return ""
    raw = str(url).strip()
    if raw.startswith("data:"):
        return raw
    if raw.startswith("http://") or raw.startswith("https://"):
        raw = urlparse(raw).path or ""
    if raw.startswith("static/"):
        raw = "/" + raw
    if not raw.startswith("/"):
        raw = "/" + raw
    if raw.startswith("/uploads/"):
        raw = "/static" + raw
    return raw


def image_file_exists(image_url: Optional[str], resource_id: Optional[int] = None) -> bool:
    from backend.server.db_models import FileResource

    if resource_id:
        fr = FileResource.query.get(resource_id)
        if fr and fr.path and os.path.isfile(fr.path):
            return True

    rel = normalize_carousel_image_url(image_url)
    if not rel.startswith("/static/uploads/"):
        return False
    rel_path = rel[len("/static/uploads/") :].replace("\\", "/").lstrip("/")
    if not rel_path or ".." in rel_path:
        return False
    root = upload_root()
    full = os.path.abspath(os.path.join(root, rel_path.replace("/", os.sep)))
    if full.startswith(root + os.sep) and os.path.isfile(full):
        return True

    fr = FileResource.query.filter_by(url=rel).first()
    if fr and fr.path and os.path.isfile(fr.path):
        return True
    return False


def resolve_slide_image_url(slide) -> str:
    from backend.server.db_models import FileResource

    if getattr(slide, "resource_id", None):
        fr = FileResource.query.get(slide.resource_id)
        if fr and fr.url:
            return normalize_carousel_image_url(fr.url)
    return normalize_carousel_image_url(getattr(slide, "image_url", None))


def bind_slide_resource(slide, image_url: str, resource_id: Optional[int] = None) -> None:
    """写入轮播图记录并尽量关联 FileResource。"""
    from backend.server.db_models import FileResource

    normalized = normalize_carousel_image_url(image_url)
    slide.image_url = normalized
    if resource_id:
        slide.resource_id = resource_id
        return
    fr = FileResource.query.filter_by(url=normalized).first()
    if fr:
        slide.resource_id = fr.id


def carousel_slide_to_dict(slide, *, admin: bool = False) -> Dict[str, Any]:
    image_url = resolve_slide_image_url(slide)
    payload = {
        "id": slide.id,
        "title": slide.title,
        "description": slide.description,
        "image_url": image_url,
        "link_url": slide.link_url,
        "resource_id": slide.resource_id,
        "sort_order": slide.sort_order,
        "is_active": slide.is_active,
    }
    if admin:
        payload["file_ok"] = bool(image_url and image_file_exists(image_url, slide.resource_id))
    return payload


def load_public_carousel_slides(*, sanitize: bool = True) -> List[Dict[str, Any]]:
    """
    公开读：仅返回磁盘上真实存在的轮播图。
    sanitize=True 时自动停用文件丢失的记录并失效 Redis 缓存。
    """
    from backend.server.extensions import db
    from backend.server.db_models import CarouselSlide
    from backend.services.cache_aside import invalidate_carousel_read_cache

    slides = (
        CarouselSlide.query.filter_by(is_active=True)
        .order_by(CarouselSlide.sort_order, CarouselSlide.id)
        .all()
    )

    valid: List[Dict[str, Any]] = []
    changed = False

    for slide in slides:
        image_url = resolve_slide_image_url(slide)
        if not image_file_exists(image_url):
            if sanitize:
                slide.is_active = False
                changed = True
                logger.warning(
                    "carousel slide %s deactivated: missing file %s",
                    slide.id,
                    image_url,
                )
            continue

        normalized = normalize_carousel_image_url(image_url)
        if slide.image_url != normalized:
            slide.image_url = normalized
            changed = True

        valid.append(carousel_slide_to_dict(slide))

    if changed and sanitize:
        db.session.commit()
        invalidate_carousel_read_cache()

    return valid
