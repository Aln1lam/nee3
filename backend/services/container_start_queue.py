# -*- coding: utf-8 -*-
"""启容器 Redis 可靠队列：RPOPLPUSH + processing 列表，崩溃可回收重试。"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

QUEUE_KEY = "neepu:container:start:queue"
PROCESSING_KEY = "neepu:container:start:processing"
CLAIM_META_PREFIX = "neepu:container:start:claim:"
RESULT_PREFIX = "neepu:container:start:result:"
STATUS_PREFIX = "neepu:container:start:status:"
INFLIGHT_KEY = "neepu:container:start:inflight"

# 处理中超时后回收回主队列；超过最大重试则标记失败
STALE_CLAIM_SEC = 180
MAX_JOB_RETRIES = 3


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


def get_job_status(job_id: str, *, requester_id: int | None = None, is_admin: bool = False) -> dict:
    """查询异步启容器任务状态；非管理员仅能查自己的 job。"""
    redis = _redis()
    if not redis:
        return {"status": "unavailable", "msg": "队列未启用（无 Redis），请同步启动"}
    raw = redis.get(STATUS_PREFIX + job_id)
    status_data = None
    if raw:
        try:
            status_data = json.loads(raw)
        except Exception:
            status_data = None

    owner_id = None
    if status_data is not None:
        owner_id = status_data.get("user_id")
    if owner_id is None:
        # 结果里也可能带 user_id
        result_raw = redis.get(RESULT_PREFIX + job_id)
        if result_raw:
            try:
                owner_id = (json.loads(result_raw) or {}).get("user_id")
            except Exception:
                pass

    if requester_id is not None and not is_admin:
        if owner_id is None:
            return {"status": "forbidden", "msg": "无权查看该任务"}
        try:
            if int(owner_id) != int(requester_id):
                return {"status": "forbidden", "msg": "无权查看该任务"}
        except (TypeError, ValueError):
            return {"status": "forbidden", "msg": "无权查看该任务"}

    if status_data is not None:
        return status_data

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
                "user_id": data.get("user_id"),
            }
        return {
            "status": "failed",
            "ok": False,
            "msg": data.get("msg") or "失败",
            "user_id": data.get("user_id"),
        }
    return {"status": "unknown", "msg": "任务不存在或已过期"}


def enqueue_container_start(challenge, user, team=None, expire_hours: int | None = None) -> Tuple[bool, Optional[str], str, dict]:
    """
    仅入队，立即返回 job_id（异步）。
    返回 (ok, job_id, msg, meta)
    无 Redis 时直接同步创建并返回伪 done。
    """
    from backend.services.container_expire import default_container_expire_hours
    from backend.services.container_service import container_service

    if expire_hours is None:
        expire_hours = default_container_expire_hours()

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
        "retry_count": 0,
        "enqueued_at": time.time(),
    }
    try:
        redis.lpush(QUEUE_KEY, json.dumps(payload))
        qlen = get_queue_length()
        _set_status(
            redis, job_id, "queued",
            position=qlen, challenge_id=challenge.id, user_id=user.id,
        )
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


def create_container_queued(challenge, user, team=None, expire_hours: int | None = None):
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
        _set_status(
            redis, job_id, "waiting",
            position=get_queue_length(), challenge_id=challenge.id, user_id=user.id,
        )
        raw = redis.get(result_key)
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            redis.delete(result_key)
            if not data.get("ok"):
                _set_status(redis, job_id, "failed", msg=data.get("msg"), user_id=user.id)
                return False, None, data.get("msg") or "容器启动失败"
            instance_id = data.get("instance_id")
            from backend.server.db_models import CtfGameInstance
            inst = CtfGameInstance.query.get(instance_id) if instance_id else None
            if not inst:
                _set_status(redis, job_id, "failed", msg="实例丢失", user_id=user.id)
                return False, None, "容器已启动但实例丢失"
            _set_status(
                redis, job_id, "done",
                instance_id=instance_id, msg=data.get("msg"), user_id=user.id,
            )
            return True, inst, data.get("msg") or "ok"
        time.sleep(0.4)

    _set_status(redis, job_id, "timeout", msg="排队超时", user_id=user.id)
    return False, None, "启容器排队超时，请稍后重试"


_INFLIGHT_ACQUIRE_LUA = """
local cur = tonumber(redis.call('GET', KEYS[1]) or '0')
local lim = tonumber(ARGV[1])
if cur >= lim then
  return -1
end
return redis.call('INCR', KEYS[1])
"""

_INFLIGHT_RELEASE_LUA = """
local v = redis.call('DECR', KEYS[1])
if v < 0 then
  redis.call('SET', KEYS[1], 0)
  return 0
end
return v
"""


def _try_acquire_inflight(redis, max_conc: int) -> bool:
    try:
        n = redis.redis.eval(_INFLIGHT_ACQUIRE_LUA, 1, INFLIGHT_KEY, int(max_conc))
        return int(n) > 0
    except Exception as exc:
        logger.debug("inflight acquire failed: %s", exc)
        return False


def _release_inflight(redis) -> None:
    try:
        redis.redis.eval(_INFLIGHT_RELEASE_LUA, 1, INFLIGHT_KEY)
    except Exception:
        try:
            redis.redis.decr(INFLIGHT_KEY)
        except Exception:
            pass


def _claim_raw(redis) -> Optional[str]:
    """可靠领取：主队列 → processing（RPOPLPUSH，崩溃可回收）。"""
    try:
        # BRPOPLPUSH 在 timeout=0 会永久阻塞；内联消费用非阻塞 RPOPLPUSH
        raw = redis.redis.rpoplpush(QUEUE_KEY, PROCESSING_KEY)
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
            job_id = payload.get("job_id")
            if job_id:
                redis.set(
                    CLAIM_META_PREFIX + str(job_id),
                    json.dumps({"claimed_at": time.time(), "raw": raw}),
                    expiration=STALE_CLAIM_SEC * 2,
                )
        except Exception:
            pass
        return raw
    except Exception as exc:
        logger.warning("claim job failed: %s", exc)
        return None


def _ack_raw(redis, raw: str, job_id: Optional[str] = None) -> None:
    try:
        redis.redis.lrem(PROCESSING_KEY, 1, raw)
    except Exception as exc:
        logger.debug("ack lrem failed: %s", exc)
    if job_id:
        try:
            redis.delete(CLAIM_META_PREFIX + str(job_id))
        except Exception:
            pass


def reclaim_stale_processing(max_age_sec: int = STALE_CLAIM_SEC) -> int:
    """将超时仍卡在 processing 的任务移回主队列（或超限失败）。"""
    redis = _redis()
    if not redis:
        return 0
    try:
        items = redis.redis.lrange(PROCESSING_KEY, 0, -1) or []
    except Exception as exc:
        logger.debug("lrange processing failed: %s", exc)
        return 0

    reclaimed = 0
    now = time.time()
    for raw in items:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            try:
                redis.redis.lrem(PROCESSING_KEY, 1, raw)
            except Exception:
                pass
            continue

        job_id = payload.get("job_id")
        claimed_at = None
        if job_id:
            meta_raw = redis.get(CLAIM_META_PREFIX + str(job_id))
            if meta_raw:
                try:
                    meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
                    if isinstance(meta, dict):
                        claimed_at = float(meta.get("claimed_at") or 0)
                except Exception:
                    claimed_at = None
        if claimed_at is None:
            claimed_at = float(payload.get("claimed_at") or payload.get("enqueued_at") or 0)
        if claimed_at and (now - claimed_at) < max_age_sec:
            continue

        retry = int(payload.get("retry_count") or 0) + 1
        payload["retry_count"] = retry
        payload.pop("claimed_at", None)
        _ack_raw(redis, raw, job_id)

        if retry > MAX_JOB_RETRIES:
            _write_result(
                redis, job_id, False, None,
                "启容器任务多次超时失败", user_id=payload.get("user_id"),
            )
            _set_status(
                redis, job_id, "failed",
                msg="启容器任务多次超时失败", user_id=payload.get("user_id"),
            )
            logger.warning("container job %s abandoned after %s retries", job_id, retry)
        else:
            try:
                redis.lpush(QUEUE_KEY, json.dumps(payload))
                _set_status(
                    redis, job_id, "queued",
                    msg=f"超时回收重试 #{retry}",
                    user_id=payload.get("user_id"),
                    challenge_id=payload.get("challenge_id"),
                )
                reclaimed += 1
                logger.info("requeued stale container job %s retry=%s", job_id, retry)
            except Exception as exc:
                logger.warning("requeue stale job failed: %s", exc)
    return reclaimed


def process_container_start_queue(max_jobs: int = 2) -> int:
    """消费队列；由 scheduler 或等待中的请求调用。返回处理条数。"""
    from backend.server.config import settings
    from backend.services.container_service import container_service
    from backend.server.db_models import CtfChallenge, User, Team
    from backend.server.extensions import db

    redis = _redis()
    if not redis:
        return 0

    try:
        reclaim_stale_processing()
    except Exception as exc:
        logger.debug("reclaim stale skipped: %s", exc)

    max_conc = int(getattr(settings, "CONTAINER_START_MAX_CONCURRENT", 2) or 2)
    processed = 0

    for _ in range(max_jobs):
        if not _try_acquire_inflight(redis, max_conc):
            break

        raw = _claim_raw(redis)
        if not raw:
            _release_inflight(redis)
            break

        job_id = None
        user_id = None
        try:
            payload = json.loads(raw)
            job_id = payload.get("job_id")
            user_id = payload.get("user_id")
            _set_status(
                redis, job_id, "running",
                challenge_id=payload.get("challenge_id"), user_id=user_id,
            )
            challenge = CtfChallenge.query.get(payload["challenge_id"])
            user = User.query.get(payload["user_id"])
            team = Team.query.get(payload["team_id"]) if payload.get("team_id") else None
            if not challenge or not user:
                _write_result(redis, job_id, False, None, "题目或用户不存在", user_id=user_id)
                _set_status(redis, job_id, "failed", msg="题目或用户不存在", user_id=user_id)
            else:
                from backend.services.container_expire import default_container_expire_hours
                raw_hours = payload.get("expire_hours")
                hours = default_container_expire_hours() if raw_hours is None else int(raw_hours)
                ok, inst, msg = container_service.create_container(
                    challenge=challenge,
                    user=user,
                    team=team,
                    expire_hours=hours,
                )
                _write_result(
                    redis, job_id, ok,
                    inst.id if inst else None, msg, user_id=user_id,
                )
                _set_status(
                    redis, job_id,
                    "done" if ok else "failed",
                    instance_id=inst.id if inst else None,
                    msg=msg, user_id=user_id,
                )
            processed += 1
        except Exception as e:
            logger.exception("process container start job failed: %s", e)
            try:
                db.session.rollback()
            except Exception:
                pass
            if job_id:
                _write_result(redis, job_id, False, None, "容器启动失败", user_id=user_id)
                _set_status(redis, job_id, "failed", msg="容器启动失败", user_id=user_id)
        finally:
            _ack_raw(redis, raw, job_id)
            _release_inflight(redis)

    return processed


def _write_result(redis, job_id, ok, instance_id, msg, user_id=None):
    if not job_id:
        return
    key = RESULT_PREFIX + str(job_id)
    redis.set(
        key,
        json.dumps({
            "ok": bool(ok),
            "instance_id": instance_id,
            "msg": msg,
            "user_id": user_id,
        }),
        expiration=120,
    )
