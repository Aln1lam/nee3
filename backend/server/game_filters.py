# -*- coding: utf-8 -*-
"""Shared helpers to keep E2E / probe competitions out of public listings."""
from __future__ import annotations

import re

# Titles created by backend/scripts/*_e2e.py and API probes — not real contests.
_EPHEMERAL_TITLE_RE = re.compile(
    r'(流量捕获|容器生命周期|E2E\s*全链路|CaptureTest|AutoTest|'
    r'API\s*Test\s*Game|EndpointSweep|Signup容器|全链路测试)',
    re.IGNORECASE,
)
_TIMESTAMP_SUFFIX_RE = re.compile(r'(?:\s|_)\d{6,}$')


def is_ephemeral_test_title(title: str | None) -> bool:
    t = (title or '').strip()
    if not t:
        return True
    if len(t) <= 2:
        return True
    if _EPHEMERAL_TITLE_RE.search(t):
        return True
    if _TIMESTAMP_SUFFIX_RE.search(t):
        return True
    return False


def is_ephemeral_test_game(game) -> bool:
    return is_ephemeral_test_title(getattr(game, 'title', None))
