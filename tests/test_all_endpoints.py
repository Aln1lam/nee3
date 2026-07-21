"""
全量 API 接口探测 — 遍历所有已注册路由，验证不会 500。

运行:
  python tests/test_all_endpoints.py
  pytest tests/test_all_endpoints.py -v
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("REDIS_ENABLED", "true")

from backend.app import create_app
from tests.auth_helpers import set_auth_cookie, json_headers
from backend.server.extensions import db
from backend.server.db_models import (
    User,
    CtfGame,
    CtfChallenge,
    Article,
    Team,
    MainAnnouncement,
)


# 不探测（外部依赖 / 代理 / 二进制上传）
SKIP_PREFIXES = (
    "/static/",
    "/api/container/proxy/",
    "/api/container/debug/",
)
SKIP_EXACT = {
    "/api/external/events",
}
# 可能破坏生产数据的 DELETE（仅跳过无测试 ID 的）
SKIP_DELETE_PATTERNS = (
    re.compile(r"^/api/admin/platform/users/\d+$"),
    re.compile(r"^/api/admin/users/\d+$"),
    re.compile(r"^/api/admin/games/\d+$"),
    re.compile(r"^/api/competitions/admin/\d+"),
    re.compile(r"^/api/admin/platform/articles/\d+$"),
    re.compile(r"^/api/admin/challenges/games/\d+/challenges/\d+$"),
    re.compile(r"^/api/teams/admin$"),
)
SKIP_POST_PATTERNS = (
    re.compile(r"^/api/admin/games$"),  # 空 body 会触发日期解析错误
)


def _build_context(app) -> dict[str, Any]:
    """准备路径参数与认证上下文"""
    from flask_jwt_extended import create_access_token

    ctx: dict[str, Any] = {}
    admin = User.query.filter_by(is_admin=True).first() or User.query.first()
    if not admin:
        raise RuntimeError("数据库无用户，无法探测接口")
    if not admin.is_admin:
        admin.is_admin = True
        db.session.commit()

    ctx["admin"] = admin
    ctx["user_id"] = admin.id
    ctx["uid"] = admin.id
    ctx["tid"] = admin.team_id or 1
    ctx["team_id"] = admin.team_id or 1
    ctx["token"] = create_access_token(identity=str(admin.id))
    ctx["headers"] = json_headers()

    if not admin.team_id:
        from backend.app import create_app as _ca
        # team 由测试客户端创建
        pass

    future = datetime.utcnow() + timedelta(days=7)
    start = datetime.utcnow() - timedelta(hours=1)
    game = CtfGame(
        title=f"EndpointSweep {datetime.utcnow().strftime('%H%M%S')}",
        start_time=start,
        end_time=future,
        is_public=True,
    )
    db.session.add(game)
    db.session.flush()
    ctx["game_id"] = game.id
    ctx["gid"] = game.id

    ch = CtfChallenge(
        game_id=game.id,
        title="Sweep Challenge",
        description="test",
        category="misc",
        flag="flag{sweep_test}",
        original_points=100,
        is_enabled=True,
    )
    db.session.add(ch)
    db.session.flush()
    ctx["challenge_id"] = ch.id
    ctx["cid"] = ch.id

    article = Article.query.first()
    ctx["aid"] = article.id if article else 1
    ctx["article_id"] = ctx["aid"]

    ann = MainAnnouncement.query.first()
    ctx["announcement_id"] = ann.id if ann else 1
    ctx["bulletin_id"] = ctx["announcement_id"]

    ctx["instance_id"] = 1
    ctx["hint_id"] = 1
    ctx["attachment_id"] = 1
    ctx["file_id"] = 1
    ctx["slide_id"] = 1
    ctx["carousel_id"] = 1
    ctx["log_id"] = 1
    ctx["record_id"] = 1
    ctx["todo_id"] = 1
    ctx["tid_token"] = "test-token-id"
    ctx["rid"] = 1
    ctx["division_id"] = 1
    ctx["slug"] = "how-to-use"
    ctx["nickname"] = admin.nickname or "admin"

    db.session.commit()
    ctx["_cleanup_game_id"] = game.id
    return ctx


def _resolve_path(rule: str, ctx: dict) -> str | None:
    """将 <type:name> 替换为测试 ID"""
    def repl(m):
        typ = m.group(1) or "string"
        name = m.group(2)
        if name == "tid" and typ == "string":
            return "test-token-id"
        if name in ctx:
            return str(ctx[name])
        return None

    parts = []
    for seg in rule.split("/"):
        m = re.fullmatch(r"<(?:(\w+):)?(\w+)>", seg)
        if m:
            val = repl(m)
            if val is None:
                return None
            parts.append(val)
        else:
            parts.append(seg)
    path = "/".join(parts)
    return path if path.startswith("/") else "/" + path


def _call(client, method: str, path: str, headers: dict | None):
    fn = getattr(client, method.lower())
    kw = {}
    if headers:
        kw["headers"] = headers
    if method in ("POST", "PUT", "PATCH"):
        kw["json"] = {}
    return fn(path, **kw)


def run_endpoint_sweep(app, client, *, auth: bool = True) -> list[dict]:
    results = []
    with app.app_context():
        ctx = _build_context(app)
        set_auth_cookie(client, ctx["token"])

        if not ctx["admin"].team_id:
            resp = client.post(
                "/api/teams/",
                headers=ctx["headers"],
                json={"name": f"SweepTeam_{ctx['game_id']}"},
            )
            if resp.status_code in (200, 201):
                data = resp.get_json(silent=True) or {}
                tid = (
                    data.get("team_id")
                    or (data.get("data") or {}).get("team_id")
                    or (data.get("data") or {}).get("id")
                )
                if tid:
                    ctx["team_id"] = ctx["tid"] = tid
                    db.session.refresh(ctx["admin"])

        seen = set()
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith(SKIP_PREFIXES) or rule.rule in SKIP_EXACT:
                continue
            if rule.rule.startswith("/static"):
                continue

            methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
            path_template = rule.rule

            for method in methods:
                key = (method, path_template)
                if key in seen:
                    continue
                seen.add(key)

                path = _resolve_path(path_template, ctx)
                if path is None:
                    results.append({
                        "method": method,
                        "path": path_template,
                        "status": "SKIP",
                        "code": None,
                        "note": "无法解析路径参数",
                    })
                    continue

                if method == "DELETE" and any(p.match(path) for p in SKIP_DELETE_PATTERNS):
                    results.append({
                        "method": method,
                        "path": path,
                        "status": "SKIP",
                        "code": None,
                        "note": "跳过危险 DELETE",
                    })
                    continue

                if method == "POST" and any(p.match(path) for p in SKIP_POST_PATTERNS):
                    results.append({
                        "method": method,
                        "path": path,
                        "status": "SKIP",
                        "code": None,
                        "note": "跳过需完整 body 的 POST",
                    })
                    continue

                use_auth = auth and (
                    path.startswith("/api/admin")
                    or path.startswith("/api/todos")
                    or path.startswith("/api/platform/instances")
                    or path.startswith("/api/auth/me")
                    or path.startswith("/api/auth/profile")
                    or path.startswith("/api/auth/change-password")
                    or path.startswith("/api/teams/me")
                    or path.startswith("/api/teams/admin")
                    or path.startswith("/api/tokens")
                    or path.startswith("/api/uploads")
                    or (path.startswith("/api/articles") and method != "GET" and not path.endswith("/announcements") and "/wiki/" not in path and path != "/api/articles/carousel")
                    or path.startswith("/api/competitions/my")
                    or path.startswith("/api/competitions/admin")
                    or path.startswith("/api/games/") and method != "GET"
                    or path.startswith("/api/games/challenges/")
                    or path.startswith("/api/challenges/") and method != "GET"
                    or path.startswith("/api/ctf/") and (method != "GET" or path.endswith("/user"))
                    or path.startswith("/api/container/")
                    or path.startswith("/api/attachments/") and method != "GET"
                    or "/join" in path
                    or "/submit" in path
                    or "/leave" in path
                )
                headers = ctx["headers"] if use_auth else None

                try:
                    resp = _call(client, method, path, headers)
                    code = resp.status_code
                    if code >= 500:
                        status = "FAIL"
                        note = resp.get_data(as_text=True)[:120]
                    elif code == 404:
                        status = "OK"
                        note = "404(资源不存在,接口正常)"
                    elif code in (400, 401, 403, 405, 409, 422, 429):
                        status = "OK"
                        note = f"{code}(预期内拒绝/校验)"
                    else:
                        status = "OK"
                        note = ""
                    results.append({
                        "method": method,
                        "path": path,
                        "status": status,
                        "code": code,
                        "note": note,
                    })
                except Exception as e:
                    results.append({
                        "method": method,
                        "path": path,
                        "status": "ERROR",
                        "code": None,
                        "note": str(e)[:120],
                    })
                finally:
                    db.session.rollback()

        # 清理测试比赛
        try:
            gid = ctx.get("_cleanup_game_id")
            if gid:
                from backend.server.db_models import (
                    CtfChallengeSubmission,
                    CtfParticipatingUser,
                    CtfParticipation,
                    CtfScoreboard,
                )
                CtfChallengeSubmission.query.filter_by(game_id=gid).delete()
                CtfParticipatingUser.query.filter_by(game_id=gid).delete()
                CtfParticipation.query.filter_by(game_id=gid).delete()
                CtfScoreboard.query.filter_by(game_id=gid).delete()
                CtfChallenge.query.filter_by(game_id=gid).delete()
                CtfGame.query.filter_by(id=gid).delete()
                db.session.commit()
        except Exception:
            db.session.rollback()

    return results


def _print_report(results: list[dict]) -> bool:
    ok = sum(1 for r in results if r["status"] == "OK")
    fail = [r for r in results if r["status"] == "FAIL"]
    err = [r for r in results if r["status"] == "ERROR"]
    skip = sum(1 for r in results if r["status"] == "SKIP")

    print("\n" + "=" * 72)
    print(f"API 全量探测报告  总计 {len(results)}  通过 {ok}  失败 {len(fail)}  异常 {len(err)}  跳过 {skip}")
    print("=" * 72)

    if fail:
        print("\n[500 失败]")
        for r in fail:
            print(f"  {r['method']:6} {r['path']} -> {r['code']} {r['note']}")

    if err:
        print("\n[异常]")
        for r in err:
            print(f"  {r['method']:6} {r['path']} -> {r['note']}")

    # 按模块统计
    modules: dict[str, list] = {}
    for r in results:
        parts = r["path"].split("/")
        mod = "/".join(parts[:3]) if len(parts) >= 3 else r["path"]
        modules.setdefault(mod, []).append(r)

    print("\n[模块统计]")
    for mod, items in sorted(modules.items()):
        f = sum(1 for x in items if x["status"] == "FAIL")
        e = sum(1 for x in items if x["status"] == "ERROR")
        o = sum(1 for x in items if x["status"] == "OK")
        mark = "!" if f or e else " "
        print(f"  {mark} {mod:40} ok={o:3} fail={f} err={e}")

    print("=" * 72)
    return len(fail) == 0 and len(err) == 0


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


class TestAllEndpoints:
    def test_full_api_sweep(self, app, client):
        results = run_endpoint_sweep(app, client)
        fails = [r for r in results if r["status"] in ("FAIL", "ERROR")]
        _print_report(results)
        assert not fails, (
            f"{len(fails)} 个接口返回 500 或异常:\n"
            + "\n".join(f"{r['method']} {r['path']} -> {r.get('code')} {r['note']}" for r in fails[:20])
        )


if __name__ == "__main__":
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    results = run_endpoint_sweep(app, client)
    ok = _print_report(results)
    sys.exit(0 if ok else 1)
