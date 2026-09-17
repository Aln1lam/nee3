"""动态容器对外访问地址（公网 IP + 端口，不经 WebSocket 代理）"""
import os

from backend.server.config import settings

_HTTP_PORTS = {80, 443, 8080, 8000, 3000, 5000, 8888}
CONTAINER_PORT_MIN = int(os.environ.get("NEPU_CONTAINER_PORT_MIN", "10000"))
CONTAINER_PORT_MAX = int(os.environ.get("NEPU_CONTAINER_PORT_MAX", "20000"))


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


def public_access_port(instance) -> int | None:
    """选手应访问的宿主机端口：流量捕获时 tcpdump_pid 存的是代理端口。"""
    if not instance:
        return None
    proxy = getattr(instance, "tcpdump_pid", None)
    try:
        proxy_port = int(proxy) if proxy is not None else None
    except (TypeError, ValueError):
        proxy_port = None
    if proxy_port is not None and CONTAINER_PORT_MIN <= proxy_port <= CONTAINER_PORT_MAX:
        return proxy_port
    try:
        return int(instance.port) if instance.port is not None else None
    except (TypeError, ValueError):
        return None


def normalize_connection_url(instance, challenge=None) -> str:
    """用实例对外端口 + 公网主机修正 connection_url（兼容历史 localhost 代理数据）。"""
    if not instance:
        return ""
    port = public_access_port(instance)
    if port is None:
        return instance.connection_url or ""
    return build_connection_url(port, challenge=challenge)
