"""端到端测试：动态容器 + 动态 Flag 生成与提交校验"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}


def login(session: requests.Session) -> dict:
    r = session.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=10)
    r.raise_for_status()
    data = r.json()
    token = data["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    return data["user"]


def section(title: str):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main():
    from backend.app import create_app
    from backend.server.db_models import CtfChallenge, CtfGameInstance
    from backend.services.flag_generator import ContainerFlagService

    app = create_app()
    s = requests.Session()

    section("1. 登录")
    user = login(s)
    print(f"用户: {user['username']} (id={user['id']}, admin={user['is_admin']})")

    with app.app_context():
        challenges = (
            CtfChallenge.query
            .filter(CtfChallenge.docker_image.isnot(None))
            .filter(CtfChallenge.flag_template.isnot(None))
            .order_by(CtfChallenge.id.asc())
            .all()
        )
        if not challenges:
            challenges = (
                CtfChallenge.query
                .filter(CtfChallenge.docker_image.isnot(None))
                .filter(CtfChallenge.challenge_type == 3)
                .order_by(CtfChallenge.id.asc())
                .all()
            )
        if not challenges:
            print("未找到带 flag_template 的动态容器题，退出")
            return 1
        ch = challenges[0]
        ch_id = ch.id
        ch_title = ch.title
        ch_game_id = ch.game_id
        ch_type = ch.challenge_type
        ch_image = ch.docker_image
        ch_template = ch.flag_template
        print(f"测试题目: #{ch_id} {ch_title}")
        print(f"  game_id={ch_game_id}, type={ch_type}")
        print(f"  image={ch_image}")
        print(f"  template={ch_template}")

    section("2. API 测试 flag 生成 (/api/container/test-flag-generation)")
    r = s.post(
        f"{BASE}/api/container/test-flag-generation",
        json={
            "flag_template": ch_template,
            "challenge_id": ch_id,
            "user_id": user["id"],
            "team_id": user.get("team_id") or user["id"],
            "game_id": ch_game_id,
        },
        timeout=10,
    )
    print(f"HTTP {r.status_code}")
    gen = r.json()
    print(json.dumps(gen, ensure_ascii=False, indent=2))
    if not gen.get("success"):
        return 1
    api_flag = gen["data"]["generated_flag"]
    if gen["data"].get("has_placeholders"):
        print("FAIL: API 生成的 flag 仍含占位符")
        return 1

    section("3. 本地服务生成一致性校验")
    with app.app_context():
        from backend.server.db_models import CtfGame
        from backend.services.flag_generator import ensure_team_hash_salt

        game = CtfGame.query.get(ch_game_id)
        salt = ensure_team_hash_salt(game)
        local_flag = ContainerFlagService.generate_dynamic_flag(
            flag_template=ch_template,
            challenge_id=ch_id,
            user_id=user["id"],
            game_id=ch_game_id,
            team_id=user.get("team_id") or user["id"],
            team_hash_salt=salt,
        )
        print(f"API flag : {api_flag}")
        print(f"Local flag: {local_flag}")
        if "[GUID]" in (ch_template or ""):
            ok = "[" not in local_flag and "]" not in local_flag
            print(f"GUID 模式占位符替换: {'OK' if ok else 'FAIL'}")
        else:
            ok = api_flag == local_flag
            print(f"同参数生成一致: {'OK' if ok else 'FAIL'}")

    section("4. 启动动态容器 (/api/container/start/<id>)")
    # 先停掉旧实例
    with app.app_context():
        old = (
            CtfGameInstance.query
            .filter_by(challenge_id=ch_id, user_id=user["id"], is_running=True)
            .all()
        )
        for inst in old:
            try:
                s.post(f"{BASE}/api/container/stop/{inst.id}", timeout=15)
                print(f"已停止旧实例 #{inst.id}")
            except Exception as e:
                print(f"停止旧实例 #{inst.id} 失败: {e}")

    r = s.post(f"{BASE}/api/container/start/{ch_id}", timeout=60)
    print(f"HTTP {r.status_code}")
    start_data = r.json()
    print(json.dumps(start_data, ensure_ascii=False, indent=2)[:1200])
    if not start_data.get("success"):
        print("容器启动失败，跳过后续 Docker 校验")
        return 1

    instance_id = start_data.get("data", {}).get("instance_id") or start_data.get("instance_id")
    if not instance_id and "data" in start_data:
        instance_id = start_data["data"].get("id")
    print(f"instance_id={instance_id}")

    time.sleep(2)

    section("5. 调试接口查看 dynamic_flag (/api/container/debug/<instance_id>)")
    r = s.get(f"{BASE}/api/container/debug/{instance_id}", timeout=10)
    print(f"HTTP {r.status_code}")
    debug = r.json()
    # 管理员调试接口可能返回 flag，仅打印摘要
    data = debug.get("data", debug)
    dynamic_flag = data.get("dynamic_flag") or data.get("instance", {}).get("dynamic_flag")
    env_match = data.get("env_match")
    has_ph = data.get("has_placeholders")
    print(f"dynamic_flag: {dynamic_flag}")
    print(f"has_placeholders: {has_ph}")
    print(f"env_match (容器 FLAG 环境变量): {env_match}")
    if not dynamic_flag:
        print("FAIL: 实例未记录 dynamic_flag")
        return 1
    if "[" in dynamic_flag or "]" in dynamic_flag:
        print("FAIL: dynamic_flag 含未替换占位符")
        return 1

    section("6. 提交动态 flag (/api/container/submit-flag)")
    # 正确 flag
    r_ok = s.post(
        f"{BASE}/api/container/submit-flag",
        json={"challenge_id": ch_id, "flag": dynamic_flag},
        timeout=15,
    )
    print(f"正确提交 HTTP {r_ok.status_code}: {r_ok.json()}")

    # 错误 flag
    r_bad = s.post(
        f"{BASE}/api/container/submit-flag",
        json={"challenge_id": ch_id, "flag": "flag{wrong_flag}"},
        timeout=15,
    )
    print(f"错误提交 HTTP {r_bad.status_code}: {r_bad.json()}")

    section("7. 主做题接口校验 (/api/challenges/<id>/submit)")
    # 若容器已关闭，重新启动一次用于 challenges 路由测试
    with app.app_context():
        inst = CtfGameInstance.query.get(instance_id)
        if not inst or not inst.is_running:
            print("实例已关闭，重新启动用于 challenges 路由测试...")
            r = s.post(f"{BASE}/api/container/start/{ch_id}", timeout=60)
            start_data = r.json()
            instance_id = start_data.get("data", {}).get("instance_id") or start_data.get("data", {}).get("id")
            r = s.get(f"{BASE}/api/container/debug/{instance_id}", timeout=10)
            dynamic_flag = r.json().get("data", {}).get("dynamic_flag")

    r_ch = s.post(
        f"{BASE}/api/challenges/{ch_id}/submit",
        json={"answer": dynamic_flag},
        timeout=15,
    )
    print(f"challenges submit HTTP {r_ch.status_code}")
    try:
        body = r_ch.json()
        print(json.dumps(body, ensure_ascii=False, indent=2)[:800])
        is_correct = body.get("data", {}).get("is_correct")
        print(f"is_correct={is_correct}")
    except Exception as e:
        print(f"解析失败: {e}, body={r_ch.text[:300]}")

    section("结果汇总")
    ok_submit = r_ok.json().get("correct") or r_ok.json().get("success")
    print(f"动态 flag 生成: OK")
    print(f"容器注入 FLAG: {'OK' if env_match else '未验证/不匹配'}")
    print(f"container/submit-flag 正确提交: {'OK' if ok_submit else 'FAIL'}")
    print(f"dynamic_flag 示例: {dynamic_flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
