"""动态容器对外访问地址（公网 IP + 端口，不经 WebSocket 代理）"""
from urllib.parse import urlparse

from backend.server.config import settings

_HTTP_PORTS = {80, 443, 8080, 8000, 3000, 5000, 8888}


def get_container_public_host() -> str:
    return (settings.CONTAINER_PUBLIC_HOST or "127.0.0.1").strip()


def build_connection_url(port, challenge=None, scheme=None) -> str:
    """生成选手可见的连接地址：公网主机 + 映射端口。"""
    if port is None:
        return ""

    host = get_container_public_host()
    port = int(port)

    if scheme is None and challenge is not None:
        docker_port = getattr(challenge, "docker_port", None) or 80
        scheme = "http" if int(docker_port) in _HTTP_PORTS else None

    if scheme == "http":
        return f"http://{host}:{port}"
    return f"{host}:{port}"


def normalize_connection_url(instance, challenge=None) -> str:
    """用实例 port + 公网主机修正 connection_url（兼容历史 localhost 代理数据）。"""
    if not instance or not instance.port:
        return instance.connection_url or "" if instance else ""

    return build_connection_url(instance.port, challenge=challenge)
