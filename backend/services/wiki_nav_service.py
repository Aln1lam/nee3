"""Wiki 导航：唯一数据源为 Article 表"""

import re
from typing import Optional

WIKI_CODE_MAP = {
    "how-to-use": "HOW",
    "ctf-roadmap": "CTF",
    "connector": "CON",
    "netcat": "NCT",
    "ics-security": "ICS",
    "power-grid-sec": "PWR",
}


def extract_wiki_slug(tags: Optional[str]) -> str:
    if not tags:
        return ""
    match = re.search(r"wiki:([\w-]+)", str(tags))
    return match.group(1) if match else ""


def wiki_item_code(slug: str, title: str = "") -> str:
    if slug and slug in WIKI_CODE_MAP:
        return WIKI_CODE_MAP[slug]
    base = (slug or title or "").replace(" ", "")
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "", base)
    return cleaned[:3].upper().ljust(3, "X")[:3]


def build_wiki_nav_from_db(*, wiki_only: bool = True):
    """从数据库构建 Wiki 导航列表（已发布文章）。"""
    from backend.server.db_models import Article

    rows = (
        Article.query.filter_by(status="published")
        .order_by(Article.created_at.asc(), Article.id.asc())
        .all()
    )

    items = []
    for article in rows:
        slug = extract_wiki_slug(article.tags)
        if wiki_only and not slug:
            continue
        slug = slug or f"article-{article.id}"
        items.append(
            {
                "id": article.id,
                "title": article.title,
                "slug": slug,
                "article_id": article.id,
                "path": f"/wiki/{article.id}",
                "code": wiki_item_code(slug, article.title or ""),
                "summary": article.summary,
                "tags": article.tags,
                "created_at": article.created_at.isoformat() if article.created_at else None,
            }
        )
    return items
