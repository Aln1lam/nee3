# -*- coding: utf-8 -*-
"""启容器 Redis 队列：高峰串行/限并发，无 Redis 时直通。支持异步 job 查询。"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

QUEUE_KEY = "neepu:container:start:queue"
RESULT_PREFIX = "neepu:container:start:result:"
STATUS_PREFIX = "neepu:container:start:status:"
INFLIGHT_KEY = "neepu:container:start:inflight"


def _redis():
    from backend.services.redis_service import get_redis
    svc = get_redis()
    if svc and svc.is_available():
        return svc
    return None


def _set_status(redis, job_id: str, status: str, **extra):
    if not redis or not job_id:
        return
    payload = {"status": status, "updated_at": time.time(), **extra}
    try:
        redis.set(STATUS_PREFIX + job_id, json.dumps(payload), expiration=600)
    except Exception as e:
        logger.debug("set status failed: %s", e)


def get_queue_length() -> int:
    redis = _redis()
    if not redis:
        return 0
    try:
        return int(redis.redis.llen(QUEUE_KEY) or 0)
    except Exception:
        return 0


def get_job_status(job_id: str) -> dict:
    """查询异步启容器任务状态。"""
    redis = _redis()
    if not redis:
        return {"status": "unavailable", "msg": "队列未启用（无 Redis），请同步启动"}
    raw = redis.get(STATUS_PREFIX + job_id)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    # 结果已写出
    result_raw = redis.get(RESULT_PREFIX + job_id)
    if result_raw:
        try:
            data = json.loads(result_raw)
        except Exception:
            data = {}
        if data.get("ok"):
            return {
                "status": "done",
                "ok": True,
                "instance_id": data.get("instance_id"),
                "msg": data.get("msg") or "ok",
            }
        return {
            "status": "failed",
            "ok": False,
            "msg": data.get("msg") or "失败",
        }
    return {"status": "unknown", "msg": "任务不存在或已过期"}


def enqueue_container_start(challenge, user, team=None, expire_hours: int = 2) -> Tuple[bool, Optional[str], str, dict]:
    """
    仅入队，立即返回 job_id（异步）。
    返回 (ok, job_id, msg, meta)
    无 Redis 时直接同步创建并返回伪 done。
    """
    from backend.services.container_service import container_service

    redis = _redis()
    if not redis:
        ok, inst, msg = container_service.create_container(
            challenge=challenge, user=user, team=team, expire_hours=expire_hours,
        )
        if not ok:
            return False, None, msg or "启动失败", {"queued": False}
        return True, None, msg or "ok", {
            "queued": False,
            "instance_id": inst.id if inst else None,
            "status": "done",
        }

    job_id = uuid.uuid4().hex
    payload = {
        "job_id": job_id,
        "challenge_id": challenge.id,
        "user_id": user.id,
        "team_id": team.id if team else None,
        "expire_hours": expire_hours,
    }
    try:
        redis.lpush(QUEUE_KEY, json.dumps(payload))
        qlen = get_queue_length()
        _set_status(redis, job_id, "queued", position=qlen, challenge_id=challenge.id)
    except Exception as e:
        logger.warning("enqueue failed, sync fallback: %s", e)
        ok, inst, msg = container_service.create_container(
            challenge=challenge, user=user, team=team, expire_hours=expire_hours,
        )
        if not ok:
            return False, None, msg or "启动失败", {"queued": False}
        return True, None, msg or "ok", {
            "queued": False,
            "instance_id": inst.id if inst else None,
            "status": "done",
        }

    return True, job_id, "已进入启动队列", {
        "queued": True,
        "status": "queued",
        "position": get_queue_length(),
        "queue_length": get_queue_length(),
    }


def create_container_queued(challenge, user, team=None, expire_hours: int = 2):
    """与 container_service.create_container 同签名；有 Redis 时入队等待结果。"""
    from backend.services.container_service import container_service
    from backend.server.config import settings

    redis = _redis()
    if not redis:
        return container_service.create_container(
            challenge=challenge, user=user, team=team, expire_hours=expire_hours,
        )

    ok, job_id, msg, meta = enqueue_container_start(
        challenge=challenge, user=user, team=team, expire_hours=expire_hours,
    )
    if not ok:
        return False, None, msg
    if not job_id:
        # 同步完成
        from backend.server.db_models import CtfGameInstance
        inst = CtfGameInstance.query.get(meta.get("instance_id")) if meta.get("instance_id") else None
        return True, inst, msg

    wait_sec = int(getattr(settings, "CONTAINER_START_QUEUE_WAIT_SEC", 90) or 90)
    result_key = RESULT_PREFIX + job_id
    deadline = time.time() + wait_sec
    while time.time() < deadline:
        try:
            process_container_start_queue(max_jobs=1)
        except Exception as e:
            logger.debug("inline queue process: %s", e)
        # 更新排队位置（粗略）
        _set_status(redis, job_id, "waiting", position=get_queue_length(), challenge_id=challenge.id)
        raw = redis.get(result_key)
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            redis.delete(result_key)
            if not data.get("ok"):
                _set_status(redis, job_id, "failed", msg=data.get("msg"))
                return False, None, data.get("msg") or "容器启动失败"
            instance_id = data.get("instance_id")
            from backend.server.db_models import CtfGameInstance
            inst = CtfGameInstance.query.get(instance_id) if instance_id else None
            if not inst:
                _set_status(redis, job_id, "failed", msg="实例丢失")
                return False, None, "容器已启动但实例丢失"
            _set_status(redis, job_id, "done", instance_id=instance_id, msg=data.get("msg"))
            return True, inst, data.get("msg") or "ok"
        time.sleep(0.4)

    _set_status(redis, job_id, "timeout", msg="排队超时")
    return False, None, "启容器排队超时，请稍后重试"


def process_container_start_queue(max_jobs: int = 2) -> int:
    """消费队列；由 scheduler 或等待中的请求调用。返回处理条数。"""
    from backend.server.config import settings
    from backend.services.container_service import container_service
    from backend.server.db_models import CtfChallenge, User, Team
    from backend.server.extensions import db

    redis = _redis()
    if not redis:
        return 0

    max_conc = int(getattr(settings, "CONTAINER_START_MAX_CONCURRENT", 2) or 2)
    processed = 0

    for _ in range(max_jobs):
        try:
            inflight = int(redis.get(INFLIGHT_KEY) or 0)
        except Exception:
            inflight = 0
        if inflight >= max_conc:
            break

        raw = redis.rpop(QUEUE_KEY)
        if not raw:
            break

        try:
            redis.redis.incr(INFLIGHT_KEY)
        except Exception:
            pass

        job_id = None
        try:
            payload = json.loads(raw)
            job_id = payload.get("job_id")
            _set_status(redis, job_id, "running", challenge_id=payload.get("challenge_id"))
            challenge = CtfChallenge.query.get(payload["challenge_id"])
            user = User.query.get(payload["user_id"])
            team = Team.query.get(payload["team_id"]) if payload.get("team_id") else None
            if not challenge or not user:
                _write_result(redis, job_id, False, None, "题目或用户不存在")
                _set_status(redis, job_id, "failed", msg="题目或用户不存在")
            else:
                ok, inst, msg = container_service.create_container(
                    challenge=challenge,
                    user=user,
                    team=team,
                    expire_hours=int(payload.get("expire_hours") or 2),
                )
                _write_result(
                    redis,
                    job_id,
                    ok,
                    inst.id if inst else None,
                    msg,
                )
                _set_status(
                    redis,
                    job_id,
                    "done" if ok else "failed",
                    instance_id=inst.id if inst else None,
                    msg=msg,
                )
            processed += 1
        except Exception as e:
            logger.exception("process container start job failed: %s", e)
            try:
                db.session.rollback()
            except Exception:
                pass
            if job_id:
                _write_result(redis, job_id, False, None, str(e))
                _set_status(redis, job_id, "failed", msg=str(e))
        finally:
            try:
                redis.redis.decr(INFLIGHT_KEY)
            except Exception:
                pass

    return processed


def _write_result(redis, job_id, ok, instance_id, msg):
    if not job_id:
        return
    key = RESULT_PREFIX + str(job_id)
    redis.set(
        key,
        json.dumps({"ok": bool(ok), "instance_id": instance_id, "msg": msg}),
        expiration=120,
    )
