# -*- coding: utf-8 -*-
"""提交审计字段：IP / 耗时解析。"""
from __future__ import annotations

from datetime import datetime

from flask import request


def request_client_ip() -> str | None:
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if xff:
        return xff.split(",")[0].strip()[:64]
    return (request.remote_addr or "")[:64] or None


def resolve_submit_duration_ms(data, running_instance) -> int | None:
    """优先用客户端 elapsed_ms；否则用容器 started_at 起算。"""
    raw = None
    if isinstance(data, dict):
        raw = data.get("elapsed_ms", data.get("duration_ms"))
    if raw is not None and raw != "":
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            pass
    if running_instance and getattr(running_instance, "started_at", None):
        try:
            delta = datetime.utcnow() - running_instance.started_at
            return max(0, int(delta.total_seconds() * 1000))
        except Exception:
            pass
    return None
