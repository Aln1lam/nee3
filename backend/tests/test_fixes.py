"""回归测试：flag 提交时间、动态模板、注册模型字段。"""
from datetime import datetime, timedelta

import pytest

from backend.server.time_utils import effective_start_utc, game_has_started, parse_admin_datetime, sync_game_status_if_due
from backend.services.flag_generator import DynamicFlagGenerator, ContainerFlagService
from backend.server.container_access import public_access_port, normalize_connection_url


class _Game:
    def __init__(self, **kw):
        self.game_type = kw.get("game_type", "official")
        self.status = kw.get("status", "not_started")
        self.start_time = kw.get("start_time")


def test_parse_admin_datetime_local_to_utc():
    # 管理员输入 19:00 东八区 → 存 11:00 UTC
    got = parse_admin_datetime("2026-09-17T19:00")
    assert got == datetime(2026, 9, 17, 11, 0)


def test_game_has_started_when_status_ongoing():
    future = datetime.utcnow() + timedelta(days=1)
    g = _Game(status="ongoing", start_time=future)
    assert game_has_started(g) is True


def test_game_has_started_respects_utc_start_time():
    # parse_admin_datetime 写入的 UTC naive 不再二次偏移
    utc_start = datetime.utcnow() + timedelta(hours=1)
    assert effective_start_utc(utc_start) == utc_start


def test_game_has_started_legacy_local_mode(monkeypatch):
    monkeypatch.setenv("NEPU_START_TIME_LEGACY_LOCAL", "1")
    local_start = datetime.utcnow() + timedelta(hours=1) + timedelta(hours=8)
    assert effective_start_utc(local_start) == local_start - timedelta(hours=8)


def test_flag_template_team_hash_brace_syntax():
    tpl = "NEEPUCTF{{{team_hash}}}"
    gen = DynamicFlagGenerator(tpl)
    flag = gen.generate_with_team_hash(lambda: "abc-def-123")
    assert flag == "NEEPUCTF{abc-def-123}"
    assert "734M" not in flag


def test_sync_game_status_if_due():
    past = datetime.utcnow() - timedelta(minutes=5)
    g = _Game(status="not_started", start_time=past)
    assert sync_game_status_if_due(g) is True
    assert g.status == "ongoing"


def test_public_access_port_prefers_traffic_proxy():
    class _Inst:
        port = 10001
        tcpdump_pid = 10088
        connection_url = "http://old.example:10001"

    assert public_access_port(_Inst()) == 10088
    url = normalize_connection_url(_Inst())
    assert url.endswith(":10088")


def test_container_flag_service_team_hash():
    flag = ContainerFlagService.generate_dynamic_flag(
        flag_template="NEEPUCTF{{{team_hash}}}",
        challenge_id=1,
        user_id=42,
        game_id=1,
        team_id=7,
        team_hash_salt="salt",
    )
    assert flag.startswith("NEEPUCTF{")
    assert flag.endswith("}")
    assert "734M" not in flag
    # 同队同题稳定
    flag2 = ContainerFlagService.generate_dynamic_flag(
        flag_template="NEEPUCTF{{{team_hash}}}",
        challenge_id=1,
        user_id=99,
        game_id=1,
        team_id=7,
        team_hash_salt="salt",
    )
    assert flag == flag2
