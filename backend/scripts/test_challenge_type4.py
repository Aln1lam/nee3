"""后端冒烟：题型 4（附件 + 动态容器）及互斥逻辑。用法: python backend/scripts/test_challenge_type4.py"""
import io
import json
import sys
import time

import requests

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuLocalAdmin!2026"}


def main():
    results = []

    def record(name, ok, detail=""):
        results.append({"test": name, "ok": bool(ok), "detail": detail})
        mark = "PASS" if ok else "FAIL"
        line = f"[{mark}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)

    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=10)
    logged_in = r.status_code == 200 and (s.cookies.get("neepu_token") or r.json().get("access_token"))
    record("管理员登录", logged_in, f"status={r.status_code}")
    if not logged_in:
        return finish(results, 1)

    h = {"Content-Type": "application/json"}
    h_file = {}

    r = s.get(f"{BASE}/api/competitions/", headers=h, timeout=10)
    items = r.json()
    if isinstance(items, dict):
        items = items.get("data") or items.get("games") or []
    training = [g for g in items if g.get("game_type") == "training"]
    game_id = training[0]["id"] if training else items[0]["id"]
    record("获取比赛", True, f"game_id={game_id}")

    r = s.post(
        f"{BASE}/api/admin/challenges/games/{game_id}/challenges",
        headers=h,
        json={
            "title": "x",
            "category": "Pwn",
            "flag": "f",
            "original_points": 100,
            "challenge_type": 2,
        },
        timeout=10,
    )
    record(
        "拒绝动态附件 type=2",
        r.json().get("code") == 400,
        r.json().get("msg", r.text[:80]),
    )

    r = s.post(
        f"{BASE}/api/admin/challenges/games/{game_id}/challenges",
        headers=h,
        json={
            "title": "TYPE4-NO-TPL",
            "category": "Pwn",
            "flag": "dynamic",
            "original_points": 500,
            "min_score_rate": 0.25,
            "difficulty": 10,
            "challenge_type": 4,
            "docker_image": "nginx:latest",
            "docker_port": 80,
        },
        timeout=10,
    )
    record("type=4 缺 Flag 模板应失败", r.json().get("code") == 400, r.json().get("msg", ""))

    title = f"PWN-T4-{int(time.time()) % 100000}"
    r = s.post(
        f"{BASE}/api/admin/challenges/games/{game_id}/challenges",
        headers=h,
        json={
            "title": title,
            "category": "Pwn",
            "flag": "dynamic",
            "flag_template": "flag{{{team_hash}}}",
            "description": "backend test type 4",
            "original_points": 500,
            "min_score_rate": 0.25,
            "difficulty": 10,
            "challenge_type": 4,
            "docker_image": "nginx:latest",
            "docker_port": 80,
            "submission_limit": 0,
            "disable_blood_bonus": False,
        },
        timeout=10,
    )
    body = r.json()
    data = body.get("data") or {}
    cid = data.get("id")
    record(
        "创建 type=4 题目",
        body.get("code") == 200 and cid,
        f"id={cid} challenge_type={data.get('challenge_type')}",
    )
    if not cid:
        return finish(results, 2)

    fake = io.BytesIO(b"ELF-PWN-BINARY-TEST")
    r = s.post(
        f"{BASE}/api/admin/challenges/games/{game_id}/challenges/{cid}/attachments",
        headers=h_file,
        files={"file": ("pwn.bin", fake, "application/octet-stream")},
        timeout=30,
    )
    up = r.json()
    aid = (up.get("data") or {}).get("attachment_id")
    record("type=4 上传附件", up.get("code") == 200 and aid, f"attachment_id={aid}")

    r = s.get(f"{BASE}/api/admin/challenges/games/{game_id}/challenges/{cid}", headers=h, timeout=10)
    d = r.json().get("data") or {}
    dual = d.get("challenge_type") == 4 and d.get("docker_image") and d.get("attachment_id")
    record(
        "管理端详情 镜像+附件+type4",
        dual,
        f"type={d.get('challenge_type')} docker={d.get('docker_image')} att={d.get('attachment_id')}",
    )

    r = s.get(f"{BASE}/api/challenges/games/{game_id}/challenges", headers=h, timeout=10)
    lst = r.json()
    if isinstance(lst, list):
        chs = lst
    elif isinstance(lst, dict):
        chs = lst.get("data") or lst.get("challenges") or []
    else:
        chs = []
    one = next((c for c in chs if c.get("id") == cid), None)
    record(
        "选手题目列表 attachment_id",
        one and one.get("attachment_id") == aid,
        f"attachment_id={one.get('attachment_id') if one else None}",
    )
    record(
        "选手列表 supports_container",
        one and one.get("supports_container") is True,
        str(one.get("supports_container") if one else None),
    )
    record(
        "选手列表 challenge_type=4",
        one and one.get("challenge_type") == 4,
        str(one.get("challenge_type") if one else None),
    )

    r = s.get(f"{BASE}/api/resources/{aid}/content", headers=h, timeout=10)
    record(
        "附件下载",
        r.status_code == 200 and b"ELF-PWN" in r.content,
        f"status={r.status_code} len={len(r.content)}",
    )

    r = s.post(f"{BASE}/api/challenges/{cid}/start-container", headers=h, json={}, timeout=120)
    st = r.json()
    st_data = st.get("data") or {}
    url = st_data.get("connection_url")
    start_ok = st.get("code") == 200 and url
    if st.get("code") == 429 and "实例" in (st.get("msg") or ""):
        # 配额满时复测：同题再次请求应返回已存在实例
        r2 = s.post(f"{BASE}/api/challenges/{cid}/start-container", headers=h, json={}, timeout=120)
        st2 = r2.json()
        url = (st2.get("data") or {}).get("connection_url")
        start_ok = st2.get("code") == 200 and url
        st = st2
    record("启动容器", start_ok, f"url={url} msg={st.get('msg')}")

    if url and str(url).startswith("http"):
        try:
            hr = requests.get(url, timeout=5)
            record("容器 HTTP 可达", hr.status_code == 200, f"status={hr.status_code}")
        except Exception as e:
            record("容器 HTTP 可达", False, str(e))

    r = s.post(
        f"{BASE}/api/admin/challenges/games/{game_id}/challenges",
        headers=h,
        json={
            "title": "STATIC-ATT-ONLY",
            "category": "Misc",
            "flag": "flag{static}",
            "original_points": 100,
            "challenge_type": 0,
            "docker_image": "nginx:latest",
        },
        timeout=10,
    )
    s0 = r.json()
    cid0 = (s0.get("data") or {}).get("id")
    d0 = s0.get("data") or {}
    record(
        "type=0 创建不带 docker",
        cid0 and not d0.get("docker_image"),
        f"docker_image={d0.get('docker_image')}",
    )

    if cid0:
        s.put(
            f"{BASE}/api/admin/challenges/games/{game_id}/challenges/{cid0}",
            headers=h,
            json={"challenge_type": 1, "docker_image": "nginx:latest"},
            timeout=10,
        )
        s.post(
            f"{BASE}/api/admin/challenges/games/{game_id}/challenges/{cid0}/attachments",
            headers=h_file,
            files={"file": ("a.txt", io.BytesIO(b"hi"), "text/plain")},
            timeout=10,
        )
        r = s.get(f"{BASE}/api/admin/challenges/games/{game_id}/challenges/{cid0}", headers=h, timeout=10)
        d1 = r.json().get("data") or {}
        record(
            "type=1 容器+附件并存",
            d1.get("challenge_type") == 1 and d1.get("attachment_id") and d1.get("docker_image"),
            f"att={d1.get('attachment_id')}",
        )

    return finish(results, 0)


def finish(results, code):
    passed = sum(1 for x in results if x["ok"])
    failed = sum(1 for x in results if not x["ok"])
    print()
    print("=" * 50)
    print(f"合计: {passed} 通过, {failed} 失败, 共 {len(results)} 项")
    print("=" * 50)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return code if failed else 0


if __name__ == "__main__":
    sys.exit(main())
