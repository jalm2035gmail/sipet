from __future__ import annotations

import json
import os
import secrets
from typing import Any

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = Any  # type: ignore[misc,assignment]

REDIS_URL = (os.environ.get("MODULE_BASE_REDIS_URL") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0").strip()
REDIS_ENABLED = (os.environ.get("MODULE_BASE_REDIS_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"}
REDIS_PREFIX = (os.environ.get("MODULE_BASE_REDIS_PREFIX") or "modulo_base").strip() or "modulo_base"
_REDIS_CLIENT: Redis | None = None
_REDIS_UNAVAILABLE = False


def get_redis_client() -> Redis | None:
    global _REDIS_CLIENT, _REDIS_UNAVAILABLE
    if not REDIS_ENABLED or _REDIS_UNAVAILABLE or Redis is Any:
        return None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    try:
        _REDIS_CLIENT = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        _REDIS_CLIENT.ping()
        return _REDIS_CLIENT
    except Exception:
        _REDIS_UNAVAILABLE = True
        _REDIS_CLIENT = None
        return None


def build_redis_key(*parts: str) -> str:
    safe_parts = [str(part or "").strip() for part in parts if str(part or "").strip()]
    return ":".join([REDIS_PREFIX, *safe_parts])


def _serialize(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def _deserialize(raw: str | None) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_cached_payload(namespace: str, identifier: str, payload: Any, ttl_seconds: int = 60) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.setex(build_redis_key("cache", namespace, identifier), max(1, int(ttl_seconds)), _serialize(payload))


def get_cached_payload(namespace: str, identifier: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    return _deserialize(client.get(build_redis_key("cache", namespace, identifier)))


def delete_cached_payload(namespace: str, identifier: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.delete(build_redis_key("cache", namespace, identifier))


def set_tenant_cache(tenant_id: str, namespace: str, identifier: str, payload: Any, ttl_seconds: int = 60) -> None:
    set_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier, payload, ttl_seconds)


def get_tenant_cache(tenant_id: str, namespace: str, identifier: str) -> Any | None:
    return get_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier)


def delete_tenant_cache(tenant_id: str, namespace: str, identifier: str) -> None:
    delete_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier)


def check_rate_limit(scope: str, identifier: str, *, limit: int, window_seconds: int = 60) -> dict[str, int | bool]:
    client = get_redis_client()
    if client is None:
        return {"allowed": True, "count": 0, "limit": limit, "remaining": limit}
    key = build_redis_key("rate_limit", scope, identifier)
    count = int(client.incr(key))
    if count == 1:
        client.expire(key, max(1, int(window_seconds)))
    remaining = max(0, int(limit) - count)
    return {
        "allowed": count <= int(limit),
        "count": count,
        "limit": int(limit),
        "remaining": remaining,
    }


def store_task_state(task_name: str, task_id: str, payload: dict[str, Any], ttl_seconds: int = 3600) -> None:
    set_cached_payload("task_state", f"{task_name}:{task_id}", payload, ttl_seconds)


def get_task_state(task_name: str, task_id: str) -> dict[str, Any] | None:
    payload = get_cached_payload("task_state", f"{task_name}:{task_id}")
    return payload if isinstance(payload, dict) else None


def create_operational_session(subject: str, payload: dict[str, Any], ttl_seconds: int = 1800) -> dict[str, Any]:
    session_id = secrets.token_hex(16)
    record = {
        "session_id": session_id,
        "subject": str(subject or "").strip(),
        "payload": payload,
    }
    set_cached_payload("operational_session", session_id, record, ttl_seconds)
    return record


def get_operational_session(session_id: str) -> dict[str, Any] | None:
    payload = get_cached_payload("operational_session", session_id)
    return payload if isinstance(payload, dict) else None


def delete_operational_session(session_id: str) -> None:
    delete_cached_payload("operational_session", session_id)


__all__ = [
    "REDIS_ENABLED",
    "REDIS_PREFIX",
    "REDIS_URL",
    "build_redis_key",
    "check_rate_limit",
    "create_operational_session",
    "delete_cached_payload",
    "delete_operational_session",
    "delete_tenant_cache",
    "get_cached_payload",
    "get_operational_session",
    "get_redis_client",
    "get_task_state",
    "get_tenant_cache",
    "set_cached_payload",
    "set_tenant_cache",
    "store_task_state",
]
