"""队名等文本敏感词审核（轻量，对齐 Ret2Shell auditor 思路）"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_DEFAULT_WORDS = [
    "法轮",
    "习近平",
    "台独",
    "藏独",
    "疆独",
    "色情",
    "赌博",
    "毒品",
    "傻逼",
    "去死",
    "fuck",
    "shit",
]


@lru_cache(maxsize=1)
def _load_words() -> tuple[str, ...]:
    path = Path(__file__).resolve().parents[1] / "config" / "sensitive_word_list.txt"
    words: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            w = line.strip()
            if not w or w.startswith("#"):
                continue
            words.append(w.lower())
    if not words:
        words = [w.lower() for w in _DEFAULT_WORDS]
    return tuple(words)


def find_sensitive_hit(text: str | None) -> str | None:
    """若命中返回命中词，否则 None。"""
    if not text:
        return None
    hay = str(text).lower()
    for w in _load_words():
        if w and w in hay:
            return w
    # 连续重复字符刷屏（如 aaaaaaaa）
    if re.search(r"(.)\1{7,}", hay):
        return "spam"
    return None


def assert_clean_team_name(name: str) -> tuple[bool, str]:
    hit = find_sensitive_hit(name)
    if hit:
        return False, "队名包含不允许的内容，请修改后重试"
    if len(name.strip()) < 2:
        return False, "队名过短"
    if len(name.strip()) > 32:
        return False, "队名过长（最多 32 字）"
    return True, ""
