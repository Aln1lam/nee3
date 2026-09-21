"""动态容器流量捕获（比赛级开关）"""
from __future__ import annotations

import logging
from typing import Optional

from backend.server.container_ports import allocate_host_port
from backend.server.container_access import build_connection_url
from backend.server.db_models import CtfChallenge, CtfGame, CtfGameInstance, User, Team
from backend.server.traffic_capture import get_traffic_manager

logger = logging.getLogger(__name__)

DEFAULT_FLAG_TEMPLATE = "flag{[TEAM_HASH]}"


def maybe_start_traffic_capture(
    challenge: CtfChallenge,
    instance: CtfGameInstance,
    user: User,
    team: Optional[Team] = None,
) -> bool:
    """动态容器 + 比赛开启流量捕获时，启动 TCP 代理并写 PCAP。"""
    is_dynamic_container = int(challenge.challenge_type or 0) in (3, 4)
    if not is_dynamic_container or not instance.port:
        return False

    if challenge.network_mode == "Isolated":
        logger.warning("Traffic capture skipped for isolated instance %s", instance.id)
        return False

    game = CtfGame.query.get(challenge.game_id)
    if not game or not game.enable_traffic_capture:
        return False

    proxy_port = allocate_host_port(int(instance.port))
    if not proxy_port:
        logger.error("No free port for traffic proxy (instance %s)", instance.id)
        return False

    try:
        manager = get_traffic_manager()
        team_id = team.id if team else (instance.team_id or user.id)
        result = manager.start_capture(
            container_id=instance.container_id or str(instance.id),
            instance_id=instance.id,
            user_id=user.id,
            challenge_id=challenge.id,
            target_port=int(instance.port),
            team_id=team_id,
            enable_traffic_capture=True,
            duration_seconds=7200,
            challenge_name=challenge.title,
            proxy_port=proxy_port,
        )
        if result.get("status") != "started":
            logger.warning("Traffic capture not started for instance %s: %s", instance.id, result)
            return False

        instance.tcpdump_pid = result["proxy_port"]
        instance.connection_url = build_connection_url(result["proxy_port"], challenge=challenge)

        pcap_path = result.get("pcap_path")
        if pcap_path:
            manager.save_capture_record(
                challenge_id=challenge.id,
                instance_id=instance.id,
                team_id=team_id,
                user_id=user.id,
                file_path=pcap_path,
            )

        logger.info(
            "Traffic capture enabled instance=%s game=%s proxy=%s -> target=%s",
            instance.id,
            game.id,
            result["proxy_port"],
            instance.port,
        )
        return True
    except Exception as exc:
        logger.error("Failed to start traffic capture for instance %s: %s", instance.id, exc)
        return False
