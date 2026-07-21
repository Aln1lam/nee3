"""比赛容器对外端口池（默认 10000–20000）"""
from __future__ import annotations

import os

from backend.server.db_models import CtfGameInstance

CONTAINER_PORT_MIN = int(os.environ.get("NEPU_CONTAINER_PORT_MIN", "10000"))
CONTAINER_PORT_MAX = int(os.environ.get("NEPU_CONTAINER_PORT_MAX", "20000"))


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


def allocate_host_port(*extra_used: int) -> int | None:
    used = collect_used_host_ports()
    used.update(int(p) for p in extra_used if p)
    for port in range(CONTAINER_PORT_MIN, CONTAINER_PORT_MAX + 1):
        if port not in used:
            return port
    return None
