"""
全量 API 冒烟测试：遍历已注册路由，验证不会 500，并测试核心业务流程。
"""
import json
import os
import sys
import secrets
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from tests.auth_helpers import set_auth_cookie, json_headers
from backend.server.extensions import db
from backend.server.db_models import (
    User,
    Team,
    CtfGame,
    CtfChallenge,
    CtfParticipation,
    CtfParticipatingUser,
    CtfScoreboard,
)


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _reset_client_cookies(client):
    """避免模块级 client 在测试间残留 Cookie 会话"""
    client.delete_cookie("localhost", "neepu_token")
    yield
    client.delete_cookie("localhost", "neepu_token")


def _json(resp):
    return resp.get_json(silent=True)


class TestRouteSmoke:
    """所有 GET 路由不应返回 500"""

    SKIP_PREFIXES = (
        "/api/container/proxy/",
        "/api/container/debug/",
        "/api/uploads/",
        "/api/resources/",
        "/api/attachments/",
    )

    SKIP_EXACT = {
        "/api/external/events",
    }

    def test_all_get_routes_no_server_error(self, app, client):
        failures = []
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if "GET" not in rule.methods:
                    continue
                path = rule.rule
                if any(path.startswith(p) for p in self.SKIP_PREFIXES):
                    continue
                if path in self.SKIP_EXACT:
                    continue
                if "<" in path:
                    continue

                resp = client.get(path)
                if resp.status_code >= 500:
                    failures.append(f"GET {path} -> {resp.status_code}: {resp.get_data(as_text=True)[:200]}")

        assert not failures, "500 errors:\n" + "\n".join(failures)


class TestCoreFlow:
    """核心 CTF 业务流程"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        with app.app_context():
            suffix = datetime.utcnow().strftime("%H%M%S%f")
            self.test_email = f"apitest_{suffix}@test.local"
            self.test_password = "TestPass123!"
            self.test_nickname = f"apitest_{suffix}"

            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                admin = User.query.first()
                if admin:
                    admin.is_admin = True
                    db.session.commit()
            self.admin = admin

            yield

    def test_auth_and_profile(self, client):
        account = self.admin.email or self.admin.username or self.admin.nickname
        resp = client.post(
            "/api/auth/login",
            json={"account": account, "password": "wrong"},
        )
        assert resp.status_code == 401

        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_cookie_session_flow(self, app, client):
        from flask_jwt_extended import create_access_token

        with app.app_context():
            token = create_access_token(identity=str(self.admin.id))
            admin_id = self.admin.id

        set_auth_cookie(client, token)
        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert _json(me)["id"] == admin_id

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200

        me_after = client.get("/api/auth/me")
        assert me_after.status_code == 401

    def test_ctf_health(self, client):
        resp = client.get("/api/ctf/health")
        assert resp.status_code == 200
        data = _json(resp)
        assert data is not None

    def test_games_list(self, client):
        # /api/games 与 /api/ctf/games 列表已下线
        resp = client.get("/api/games/")
        assert resp.status_code == 410

        resp = client.get("/api/ctf/games")
        assert resp.status_code == 410

    def test_competitions_list(self, client):
        resp = client.get("/api/competitions/")
        assert resp.status_code == 200

    def test_articles_public(self, client):
        resp = client.get("/api/articles/")
        assert resp.status_code == 200

    def test_todos_requires_auth(self, client):
        pytest.skip("todos API 已下线")

    def test_admin_check_requires_auth(self, client):
        resp = client.get("/api/admin/check-current-user")
        assert resp.status_code in (401, 422)


class TestAuthenticatedFlow:
    """需要登录的完整流程（使用已有管理员账号）"""

    @pytest.fixture(autouse=True)
    def login_admin(self, app, client):
        with app.app_context():
            admin = User.query.filter_by(is_admin=True).first() or User.query.first()
            if not admin:
                pytest.skip("数据库无用户，跳过认证测试")
            self.admin = admin
            self.admin_id = admin.id

            from flask_jwt_extended import create_access_token

            self.token = create_access_token(identity=str(admin.id))
            set_auth_cookie(client, self.token)
            self.headers = json_headers()

            future = datetime.utcnow() + timedelta(days=7)
            start = datetime.utcnow() - timedelta(hours=1)

            game = CtfGame(
                title=f"API Test Game {datetime.utcnow().strftime('%H%M%S')}",
                start_time=start,
                end_time=future,
                is_public=True,
            )
            db.session.add(game)
            db.session.flush()
            self.game_id = game.id

            challenge = CtfChallenge(
                game_id=game.id,
                title="API Test Challenge",
                description="test",
                category="misc",
                flag="flag{api_test_flag}",
                original_points=100,
                is_enabled=True,
            )
            db.session.add(challenge)
            db.session.flush()
            self.challenge_id = challenge.id

            db.session.refresh(admin)
            if admin.team_id:
                self.team_id = admin.team_id
            else:
                team_name = f"APITeam_{secrets.token_hex(6)}"
                team_resp = client.post(
                    "/api/teams/",
                    headers=self.headers,
                    json={"name": team_name},
                )
                assert team_resp.status_code in (200, 201), team_resp.get_data(as_text=True)
                team_data = _json(team_resp)
                self.team_id = (
                    team_data.get("data", {}).get("team_id")
                    or team_data.get("team_id")
                )
                db.session.refresh(admin)

            db.session.commit()
            yield

            try:
                CtfChallengeSubmission = __import__(
                    "backend.server.db_models", fromlist=["CtfChallengeSubmission"]
                ).CtfChallengeSubmission
                CtfChallengeSubmission.query.filter_by(game_id=self.game_id).delete()
                CtfParticipatingUser.query.filter_by(game_id=self.game_id).delete()
                CtfParticipation.query.filter_by(game_id=self.game_id).delete()
                CtfScoreboard.query.filter_by(game_id=self.game_id).delete()
                CtfChallenge.query.filter_by(game_id=self.game_id).delete()
                CtfGame.query.filter_by(id=self.game_id).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()

    def test_auth_me(self, client):
        resp = client.get("/api/auth/me", headers=self.headers)
        assert resp.status_code == 200
        data = _json(resp)
        assert data["id"] == self.admin_id

    def test_teams_me(self, client):
        resp = client.get("/api/teams/me", headers=self.headers)
        assert resp.status_code == 200

    def test_games_challenges_legacy(self, client):
        resp = client.get(f"/api/games/{self.game_id}/challenges")
        assert resp.status_code == 410

    def test_ctf_game_detail(self, client):
        resp = client.get(f"/api/competitions/{self.game_id}", headers=self.headers)
        assert resp.status_code == 200

    def test_ctf_challenges(self, client):
        resp = client.get(
            f"/api/challenges/games/{self.game_id}/challenges",
            headers=self.headers,
        )
        assert resp.status_code == 200

    def test_ctf_challenge_detail(self, client, app):
        list_resp = client.get(
            f"/api/challenges/games/{self.game_id}/challenges",
            headers=self.headers,
        )
        assert list_resp.status_code == 200
        list_payload = _json(list_resp).get("data") or {}
        items = list_payload if isinstance(list_payload, list) else list_payload.get("items", [])
        for item in items:
            assert "flag" not in item
            assert "flag_template" not in item

        resp = client.get(
            f"/api/challenges/{self.challenge_id}",
            headers=self.headers,
        )
        assert resp.status_code == 200

        with app.app_context():
            challenge = CtfChallenge.query.get(self.challenge_id)
            public = challenge.to_public_dict()
            assert "flag" not in public
            assert "flag_template" not in public

    def test_join_game_and_submit(self, client):
        join_resp = client.post(
            f"/api/competitions/{self.game_id}/join",
            headers=self.headers,
            json={},
        )
        assert join_resp.status_code == 200, join_resp.get_data(as_text=True)

        submit_resp = client.post(
            f"/api/challenges/{self.challenge_id}/submit",
            headers=self.headers,
            json={"answer": "flag{api_test_flag}"},
        )
        assert submit_resp.status_code == 200, submit_resp.get_data(as_text=True)
        data = _json(submit_resp)
        assert data.get("code") in (0, 200) or data.get("data") is not None

    def test_scoreboard(self, client):
        resp = client.get(f"/api/ctf/games/{self.game_id}/scoreboard")
        assert resp.status_code == 200

    def test_container_status(self, client):
        resp = client.get(
            f"/api/container/status/{self.challenge_id}",
            headers=self.headers,
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)

    def test_challenges_container_status(self, client):
        resp = client.get(
            f"/api/challenges/{self.challenge_id}/container-status",
            headers=self.headers,
        )
        assert resp.status_code == 200

    def test_admin_endpoints(self, client):
        resp = client.get("/api/admin/check-current-user", headers=self.headers)
        assert resp.status_code == 200

        resp = client.get("/api/admin/stats/dashboard", headers=self.headers)
        assert resp.status_code == 200

    def test_ctf_admin_games(self, client):
        resp = client.get("/api/admin/games", headers=self.headers)
        assert resp.status_code == 410

        resp = client.get(f"/api/competitions/admin/{self.game_id}/stats", headers=self.headers)
        assert resp.status_code == 200

    def test_todos_crud(self, client):
        pytest.skip("todos API 已下线")
