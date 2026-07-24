"""比赛容器对外端口池（默认 10000–20000）

分配策略：
1. 排除 DB 中 is_running 占用的端口
2. Redis NX 短时预留，降低 50 人同时启机时的端口撞车
3. 本机 bind 探测，避开 Docker/系统已占用但未入库的端口
"""
from __future__ import annotations

import logging
import os
import socket

from backend.server.db_models import CtfGameInstance

logger = logging.getLogger(__name__)

CONTAINER_PORT_MIN = int(os.environ.get("NEPU_CONTAINER_PORT_MIN", "10000"))
CONTAINER_PORT_MAX = int(os.environ.get("NEPU_CONTAINER_PORT_MAX", "20000"))
PORT_RESERVE_TTL = int(os.environ.get("NEPU_CONTAINER_PORT_RESERVE_TTL", "120"))
PORT_RESERVE_PREFIX = "neepu:port:reserve:"


def collect_used_host_ports() -> set[int]:
    used: set[int] = set()
    for inst in CtfGameInstance.query.filter_by(is_running=True).all():
        if inst.port:
            try:
                used.add(int(inst.port))
            except (TypeError, ValueError):
                pass
        if inst.tcpdump_pid:
            try:
                pid = int(inst.tcpdump_pid)
                if CONTAINER_PORT_MIN <= pid <= CONTAINER_PORT_MAX:
                    used.add(pid)
            except (TypeError, ValueError):
                pass
    return used


def _redis_client():
    try:
        from backend.services.redis_service import get_redis

        svc = get_redis()
        if svc and svc.is_available():
            return svc.redis
    except Exception as exc:
        logger.debug("port reserve redis unavailable: %s", exc)
    return None


def _port_free_on_host(port: int) -> bool:
    """探测本机是否还能 bind 该端口（避免与幽灵 Docker 映射冲突）。"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", int(port)))
        return True
    except OSError:
        return False


def release_host_port(port: int | None) -> None:
    if not port:
        return
    redis = _redis_client()
    if not redis:
        return
    try:
        redis.delete(f"{PORT_RESERVE_PREFIX}{int(port)}")
    except Exception as exc:
        logger.debug("release port %s failed: %s", port, exc)


def allocate_host_port(*extra_used: int) -> int | None:
    used = collect_used_host_ports()
    used.update(int(p) for p in extra_used if p)
    redis = _redis_client()

    for port in range(CONTAINER_PORT_MIN, CONTAINER_PORT_MAX + 1):
        if port in used:
            continue
        if not _port_free_on_host(port):
            continue
        if redis is not None:
            try:
                ok = redis.set(f"{PORT_RESERVE_PREFIX}{port}", "1", nx=True, ex=PORT_RESERVE_TTL)
                if not ok:
                    continue
            except Exception as exc:
                logger.debug("port reserve %s failed, fallback: %s", port, exc)
        return port
    return None
