"""
Redis 与中间件专项验证
运行: python tests/test_redis_middleware.py
"""
import os
import sys

# 确保 Redis 默认启用（可被外部环境变量覆盖）
os.environ.setdefault("REDIS_ENABLED", "true")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.services.redis_service import get_redis


def test_redis_and_middleware():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    results = []
    rs = get_redis()

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))

    check("Redis 连接", rs and rs.is_available(), str(rs.get_info() if rs and rs.is_available() else "unavailable"))

    r = client.get("/api/health/live")
    check("健康检查 live", r.status_code == 200, f"status={r.status_code}")

    r = client.get("/api/health/ready")
    body = r.get_json() or {}
    checks = body.get("checks", {})
    redis_check = checks.get("redis")
    redis_ok = isinstance(redis_check, dict) and redis_check.get("status") == "ok"
    if rs and rs.is_available():
        check("健康检查 ready", r.status_code == 200 and redis_ok, str(checks))
    else:
        check("健康检查 ready", r.status_code in (200, 503), str(checks))

    r1 = client.get("/api/platform/info")
    cache1 = r1.headers.get("X-Cache", "")
    r2 = client.get("/api/platform/info")
    cache2 = r2.headers.get("X-Cache", "")
    if rs and rs.is_available():
        check("平台信息缓存", r1.status_code == 200 and cache2 == "HIT", f"1st={cache1 or 'MISS'}, 2nd={cache2}")
    else:
        check("平台信息缓存", r1.status_code == 200, "Redis 不可用，跳过 HIT 验证")

    r = client.get("/api/platform/info", headers={"Accept-Encoding": "gzip"})
    enc = r.headers.get("Content-Encoding", "")
    check("Gzip 压缩", enc == "gzip", f"Content-Encoding={enc or 'none'}")

    r = client.get("/api/platform/info")
    check("安全响应头", "X-Content-Type-Options" in r.headers, r.headers.get("X-Content-Type-Options"))

    hit_429 = False
    last_status = None
    for _ in range(6):
        resp = client.post(
            "/api/auth/login",
            json={"account": "nonexistent@test.com", "password": "wrong"},
        )
        last_status = resp.status_code
        if resp.status_code == 429:
            hit_429 = True
            break
    check("登录速率限制", hit_429, f"触发429" if hit_429 else f"最后状态={last_status}")

    cap = client.get("/api/captcha/")
    cap_id = cap.headers.get("X-Captcha-Id")
    stored = bool(cap_id and rs and rs.is_available() and rs.get(f"captcha:{cap_id}"))
    check("验证码 Redis 存储", cap.status_code == 200 and (stored or not (rs and rs.is_available())), f"id={cap_id}")

    sb1 = client.get("/api/ctf/games/1/scoreboard")
    if sb1.status_code == 200 and rs and rs.is_available():
        c1 = sb1.headers.get("X-Cache", "MISS")
        sb2 = client.get("/api/ctf/games/1/scoreboard")
        c2 = sb2.headers.get("X-Cache", "")
        check("排行榜缓存", c2 == "HIT", f"1st={c1}, 2nd={c2}")
    else:
        check("排行榜缓存", True, f"跳过(status={sb1.status_code})")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n合计: {passed}/{total} 通过")
    return passed == total


if __name__ == "__main__":
    ok = test_redis_and_middleware()
    sys.exit(0 if ok else 1)
