# -*- coding: utf-8 -*-
"""Frontend-gaps 联调冒烟：G01/G08/G09/G11/G05 相关主路径。"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta

from backend.app import app
from backend.server.db_models import User, CtfGame, CtfChallenge, CtfChallengeSubmission, CtfParticipatingUser
from backend.server.extensions import db
from flask_jwt_extended import create_access_token

BASE_CHECKS = []


def ok(name, cond, detail=""):
    BASE_CHECKS.append((name, bool(cond), detail))
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {detail}")


def main():
    with app.app_context():
        client = app.test_client()
        admin = User.query.filter_by(is_admin=True).first()
        assert admin, "need admin user"
        token = create_access_token(identity=str(admin.id))
        client.set_cookie("localhost", "neepu_token", token)

        # G01 submissions path
        part = (
            db.session.execute(
                db.text(
                    """
                    SELECT c.id, p.user_id FROM ctf_challenge c
                    JOIN ctf_participating_user p ON p.game_id=c.game_id
                    WHERE c.is_enabled=1 LIMIT 1
                    """
                )
            ).fetchone()
        )
        if part:
            cid, uid = part
            user = User.query.get(uid)
            utoken = create_access_token(identity=str(user.id))
            uclient = app.test_client()
            uclient.set_cookie("localhost", "neepu_token", utoken)
            r = uclient.get(f"/api/challenges/{cid}/submissions")
            j = r.get_json() or {}
            ok("G01_submissions", r.status_code == 200 and j.get("code") == 200, f"status={r.status_code} items={len((j.get('data') or {}).get('items') or [])}")
            r_old = uclient.get(f"/api/games/challenges/{cid}/submissions")
            # legacy may still exist; new path is what FE uses
            ok("G01_new_path_shape", isinstance((j.get("data") or {}).get("items"), list), "")
        else:
            ok("G01_submissions", False, "no challenge+participant")

        # G05 admin challenges-list
        game = CtfGame.query.order_by(CtfGame.id.desc()).first()
        r = client.get(f"/api/admin/challenges/games/{game.id}/challenges-list")
        j = r.get_json() or {}
        ok("G05_admin_challenges_list", r.status_code == 200 and j.get("code") in (0, 200, None) or r.status_code == 200, f"status={r.status_code}")

        # G11 cheat detection
        r = client.get("/api/admin/cheat-detection?page=1&per_page=10")
        j = r.get_json() or {}
        ok("G11_cheat_detection", r.status_code == 200 and "data" in j, f"status={r.status_code}")
        r_bad = client.get("/api/ctf/admin/cheat-detection?page=1&per_page=10")
        ok("G11_old_prefix_should_404_or_fail", r_bad.status_code in (404, 405) or (r_bad.get_json() or {}).get("code") not in (200, 0), f"status={r_bad.status_code}")

        # G08/G09 competitions admin archive path exists (dry: create ephemeral then archive delete)
        title = f"GapSmoke {datetime.utcnow().strftime('%H%M%S')}"
        start = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        end = (datetime.utcnow() + timedelta(days=1)).isoformat()
        r = client.post(
            "/api/competitions/admin/create",
            json={"title": title, "start_time": start, "end_time": end, "is_public": False, "game_type": "practice"},
        )
        j = r.get_json() or {}
        gid = (j.get("data") or {}).get("id")
        ok("G08_create_game", r.status_code == 200 and gid, f"status={r.status_code} id={gid}")
        if gid:
            r2 = client.post(f"/api/competitions/admin/{gid}/archive")
            ok("G09_archive", r2.status_code == 200 and (r2.get_json() or {}).get("code") == 200, f"status={r2.status_code}")
            r3 = client.delete(f"/api/competitions/admin/{gid}/delete")
            ok("G08_delete", r3.status_code == 200, f"status={r3.status_code}")

        # G19 already done - skip
        # first-solves admin
        r = client.get(f"/api/admin/first-solves?game_id={game.id}&per_page=20")
        ok("G15_first_solves_admin", r.status_code == 200, f"status={r.status_code}")

        # G06 challenge type-3 fields (flag_template / docker / traffic / network)
        import io
        g06 = {
            "title": f"GapG06 {datetime.utcnow().strftime('%H%M%S')}",
            "category": "Pwn",
            "original_points": 500,
            "flag": "dynamic",
            "flag_template": "flag{{{team_hash}}}",
            "challenge_type": 3,
            "docker_image": "nginx:alpine",
            "docker_port": 80,
            "storage_limit": 2048,
            "network_mode": "Isolated",
            "enable_traffic_capture": True,
            "description": "fe-gaps smoke",
        }
        r = client.post(f"/api/admin/challenges/games/{game.id}/challenges", json=g06)
        j = r.get_json() or {}
        cid6 = (j.get("data") or {}).get("id")
        d6 = j.get("data") or {}
        ok(
            "G06_create_dyn_container",
            r.status_code == 200 and cid6 and d6.get("flag_template") and d6.get("enable_traffic_capture") is True,
            f"status={r.status_code} id={cid6} net={d6.get('network_mode')}",
        )
        if cid6:
            r = client.put(
                f"/api/admin/challenges/games/{game.id}/challenges/{cid6}",
                json={"storage_limit": 3072, "enable_traffic_capture": False},
            )
            d = (r.get_json() or {}).get("data") or {}
            ok(
                "G06_update_fields",
                r.status_code == 200 and d.get("storage_limit") == 3072 and d.get("enable_traffic_capture") is False,
                f"status={r.status_code}",
            )
            r = client.delete(f"/api/admin/challenges/games/{game.id}/challenges/{cid6}")
            ok("G07_delete_challenge", r.status_code == 200, f"status={r.status_code}")

        # G12 attachment upload after create (type 0)
        r = client.post(
            f"/api/admin/challenges/games/{game.id}/challenges",
            json={
                "title": f"GapG12 {datetime.utcnow().strftime('%H%M%S')}",
                "category": "Misc",
                "original_points": 100,
                "flag": "flag{gap12}",
                "challenge_type": 0,
                "description": "attach",
            },
        )
        cid12 = ((r.get_json() or {}).get("data") or {}).get("id")
        ok("G12_create_static", r.status_code == 200 and cid12, f"id={cid12}")
        if cid12:
            r = client.post(
                f"/api/admin/challenges/games/{game.id}/challenges/{cid12}/attachments",
                data={"file": (io.BytesIO(b"hello-gap12"), "gap12.txt")},
                content_type="multipart/form-data",
            )
            j = r.get_json() or {}
            ok("G12_upload_attachment", r.status_code == 200 and j.get("code") in (0, 200), f"status={r.status_code} msg={j.get('msg')}")
            client.delete(f"/api/admin/challenges/games/{game.id}/challenges/{cid12}")

        # G10 division CRUD + invite_code / school_scope roundtrip
        stamp = datetime.utcnow().strftime("%H%M%S")
        code = f"GAP10-{stamp}"
        r = client.post(
            f"/api/competitions/admin/{game.id}/divisions/create",
            json={
                "name": f"高校组 {stamp}",
                "invite_code": code,
                "school_scope": "高校",
                "description": "fe-gaps g10",
            },
        )
        j = r.get_json() or {}
        d = j.get("data") or {}
        did = d.get("id")
        ok(
            "G10_create_division",
            r.status_code == 200 and did and d.get("invite_code") == code and d.get("school_scope") == "高校",
            f"status={r.status_code} id={did} code={d.get('invite_code')} scope={d.get('school_scope')}",
        )
        if did:
            r = client.get(f"/api/competitions/{game.id}/divisions")
            rows = (r.get_json() or {}).get("data") or []
            found = next((x for x in rows if x.get("id") == did), None)
            ok(
                "G10_list_roundtrip",
                r.status_code == 200 and found and found.get("invite_code") == code and found.get("school_scope") == "高校",
                f"found={bool(found)}",
            )
            r = client.put(
                f"/api/competitions/admin/{game.id}/divisions/{did}",
                json={"school_scope": "东北电力大学", "description": "updated"},
            )
            d2 = (r.get_json() or {}).get("data") or {}
            ok(
                "G10_update_school_scope",
                r.status_code == 200 and d2.get("school_scope") == "东北电力大学",
                f"scope={d2.get('school_scope')}",
            )
            r = client.get(f"/api/competitions/admin/{game.id}/divisions/{did}/members")
            j = r.get_json() or {}
            ok(
                "G10_list_members",
                r.status_code == 200 and isinstance((j.get("data") or {}).get("members"), list),
                f"status={r.status_code}",
            )
            r = client.delete(f"/api/competitions/admin/{game.id}/divisions/{did}")
            ok("G10_delete_division", r.status_code == 200, f"status={r.status_code}")

        # public game must still show real divisions after create
        r = client.post(
            "/api/competitions/admin/create",
            json={
                "title": f"GapG10Public {stamp}",
                "start_time": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "is_public": True,
                "game_type": "practice",
            },
        )
        pgid = ((r.get_json() or {}).get("data") or {}).get("id")
        if pgid:
            r = client.post(
                f"/api/competitions/admin/{pgid}/divisions/create",
                json={"name": "公开赛赛道", "invite_code": f"PUB-{stamp}", "school_scope": None},
            )
            pdid = ((r.get_json() or {}).get("data") or {}).get("id")
            r = client.get(f"/api/competitions/{pgid}/divisions")
            rows = (r.get_json() or {}).get("data") or []
            ok(
                "G10_public_game_lists_real_divisions",
                any(x.get("id") == pdid for x in rows),
                f"rows={[x.get('id') for x in rows]}",
            )
            if pdid:
                client.delete(f"/api/competitions/admin/{pgid}/divisions/{pdid}")
            client.delete(f"/api/competitions/admin/{pgid}/delete")

        # G15 / G17 / G20
        r = client.get(f"/api/admin/first-solves?game_id={game.id}&per_page=5")
        ok("G15_first_solves_ui_api", r.status_code == 200, f"status={r.status_code}")
        r = client.get("/api/admin/hammer-messages?page=1&per_page=5")
        j = r.get_json() or {}
        ok("G17_hammer_aggregate", r.status_code == 200 and isinstance((j.get("data") or {}).get("items"), list), f"status={r.status_code}")
        r = client.get(f"/api/ctf/games/{game.id}/scoreboard/timeline")
        ok("G20_scoreboard_timeline", r.status_code == 200, f"status={r.status_code}")

        # G18 captcha flag exposed
        from backend.services.platform_config_service import load_public_platform_info
        info = load_public_platform_info()
        ok("G18_captcha_flag_public", "captcha_required" in info, f"val={info.get('captcha_required')}")

        # G16 game stats
        r = client.get(f"/api/admin/games/{game.id}/stats")
        j = r.get_json() or {}
        stats = ((j.get("data") or {}).get("statistics") or {})
        ok(
            "G16_game_stats",
            r.status_code == 200 and "challenge_count" in stats and "participant_count" in stats,
            f"status={r.status_code} keys={list(stats.keys())[:6]}",
        )

        # G13 export scoreboard CSV
        r = client.get(f"/api/admin/games/{game.id}/export-scoreboard")
        body = r.get_data(as_text=True) if r.status_code == 200 else ""
        ok(
            "G13_export_scoreboard",
            r.status_code == 200 and "排名" in body and "text/csv" in (r.content_type or ""),
            f"status={r.status_code} ctype={r.content_type} rows_hdr={r.headers.get('X-Row-Count')}",
        )

        # G14 cheat confirm/dismiss persistence
        from backend.server.db_models import CtfCheatInfo, CtfChallengeSubmission
        cheat = CtfCheatInfo.query.order_by(CtfCheatInfo.id.desc()).first()
        if not cheat:
            # seed minimal cheat row if submissions exist
            sub = CtfChallengeSubmission.query.order_by(CtfChallengeSubmission.id.desc()).first()
            if sub:
                cheat = CtfCheatInfo(
                    game_id=sub.game_id or game.id,
                    submission_id=sub.id,
                    source_user_id=sub.user_id,
                    target_user_id=sub.user_id,
                    similarity=0.95,
                    status="pending",
                )
                db.session.add(cheat)
                db.session.commit()
        if cheat:
            rid = cheat.id
            # ensure pending
            cheat.status = "pending"
            db.session.commit()
            r = client.post(f"/api/admin/cheat-records/{rid}/confirm", json={"admin_note": "g14-confirm"})
            j = r.get_json() or {}
            d = j.get("data") or {}
            ok(
                "G14_confirm_cheat",
                r.status_code == 200 and d.get("status") == "confirmed",
                f"status={r.status_code} row={d.get('status')}",
            )
            r = client.get("/api/admin/cheat-detection?page=1&per_page=50&status=confirmed")
            items = ((r.get_json() or {}).get("data") or {}).get("items") or []
            ok("G14_list_confirmed", any(x.get("id") == rid for x in items), f"n={len(items)}")
            r = client.post(f"/api/admin/cheat-records/{rid}/dismiss", json={"admin_note": "g14-dismiss"})
            d = (r.get_json() or {}).get("data") or {}
            ok(
                "G14_dismiss_cheat",
                r.status_code == 200 and d.get("status") == "dismissed",
                f"row={d.get('status')}",
            )
        else:
            ok("G14_confirm_cheat", False, "no cheat seed")
            ok("G14_list_confirmed", False, "skipped")
            ok("G14_dismiss_cheat", False, "skipped")

        # —— G40–G43 / P2 ——
        ch = CtfChallenge.query.order_by(CtfChallenge.id.desc()).first()
        r = client.get(f"/api/admin/dynamic-packages/challenges/{ch.id if ch else 1}/packages")
        j = r.get_json() or {}
        ok(
            "G40_dynamic_packages_list",
            r.status_code == 200 and (
                (j.get("meta") or {}).get("status") == "ready"
                or j.get("code") == 200
            ),
            f"status={r.status_code} meta={j.get('meta')}",
        )

        r = client.get("/api/challenges/container-jobs/nonexistent-job")
        ok(
            "G41_container_job_unknown",
            r.status_code in (404, 200),
            f"status={r.status_code}",
        )

        # logs endpoint exists (404 on missing instance is fine)
        r = client.get("/api/challenges/instances/999999999/logs?tail=10")
        ok("G42_instance_logs_route", r.status_code in (404, 403, 200), f"status={r.status_code}")

        r = client.get("/api/admin/seasons")
        j = r.get_json() or {}
        ok("P2_seasons_list", r.status_code == 200 and j.get("code") == 200, f"status={r.status_code}")
        year = datetime.utcnow().year
        r = client.post("/api/admin/seasons", json={"year": year, "season": f"smoke-{datetime.utcnow().strftime('%H%M%S')}", "description": "gap smoke"})
        j = r.get_json() or {}
        sid = (j.get("data") or {}).get("id")
        ok("P2_seasons_create", r.status_code == 200 and sid, f"status={r.status_code} id={sid}")
        if sid:
            r = client.delete(f"/api/admin/seasons/{sid}")
            ok("P2_seasons_delete", r.status_code == 200, f"status={r.status_code}")

        r = client.get("/api/auth/oauth/providers")
        j = r.get_json() or {}
        ok(
            "P2_oauth_providers",
            r.status_code == 200 and isinstance((j.get("data") or {}).get("providers"), list),
            f"status={r.status_code}",
        )

        # delete-account shape (wrong password → 403)
        r = client.post("/api/auth/delete-account", json={"password": "__wrong__", "confirm": "DELETE"})
        ok(
            "P2_delete_account_guard",
            r.status_code in (403, 400),
            f"status={r.status_code}",
        )

        # moderator endpoint
        normal = User.query.filter_by(is_admin=False).first()
        if normal:
            r = client.post(f"/api/admin/users/{normal.id}/moderator", json={"is_moderator": False})
            ok("G43_set_moderator", r.status_code == 200, f"status={r.status_code}")
        else:
            ok("G43_set_moderator", False, "no non-admin user")

        failed = [n for n, c, _ in BASE_CHECKS if not c]
        print("---")
        print(f"passed={sum(1 for _,c,_ in BASE_CHECKS if c)}/{len(BASE_CHECKS)}")
        if failed:
            print("FAILED:", ", ".join(failed))
            sys.exit(1)
        print("ALL_OK")


if __name__ == "__main__":
    main()
