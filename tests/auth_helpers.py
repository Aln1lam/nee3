"""测试用 Cookie 会话辅助（配合 HttpOnly JWT）"""

JWT_COOKIE_NAME = "neepu_token"
DEFAULT_SERVER_NAME = "localhost"


def set_auth_cookie(client, token: str, server_name: str = DEFAULT_SERVER_NAME) -> None:
    # Werkzeug 3+ 测试客户端需指定 server_name 才能正确附带 Cookie
    client.set_cookie(server_name, JWT_COOKIE_NAME, token, path="/")


def json_headers(extra: dict | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if extra:
        headers.update(extra)
    return headers
