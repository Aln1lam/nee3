"""容器实例默认存活时间（可通过环境变量覆盖）"""

from __future__ import annotations

import os


def default_container_expire_hours() -> int:
    raw = os.environ.get("NEEPU_CONTAINER_EXPIRE_HOURS", "1")
    try:
        hours = int(raw)
    except (TypeError, ValueError):
        hours = 1
    return max(1, min(4, hours))
