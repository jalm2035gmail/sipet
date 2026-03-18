from __future__ import annotations

import json
import os
import secrets
from functools import lru_cache
from typing import Any

try:
    from redis import Redis
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover
    Redis = Any  # type: ignore[misc,assignment]
    RedisError = Exception  # type: ignore[misc,assignment]

REDIS_URL = (os.environ.get("MODULE_BASE_REDIS_URL") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0").strip()
REDIS_ENABLED = (os.environ.get("MODULE_BASE_REDIS_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"}
REDIS_PREFIX = (os.environ.get("MODULE_BASE_REDIS_PREFIX") or "modulo_base").strip() or "modulo_base"


@lru_cache(maxsize=1)
def _build_redis_client() -> "Redis | None":
    if not REDIS_ENABLED or Redis is Any:
        return None
    try:
        client = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        client.ping()
        return client
    except Exception:
        return None


def get_redis_client() -> "Redis | None":
    return _build_redis_client()


def reset_redis_client() -> None:
    """Limpia el cliente cacheado. Útil en tests y reconexiones."""
    _build_redis_client.cache_clear()


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


def _safe_execute(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Ejecuta una operación Redis capturando errores de red sin propagar."""
    try:
        return fn(*args, **kwargs)
    except RedisError:
        reset_redis_client()
        return None
    except Exception:
        return None


# ── Cache general ─────────────────────────────────────────────────────────────

def set_cached_payload(namespace: str, identifier: str, payload: Any, ttl_seconds: int = 60) -> None:
    client = get_redis_client()
    if client is None:
        return
    _safe_execute(
        client.setex,
        build_redis_key("cache", namespace, identifier),
        max(1, int(ttl_seconds)),
        _serialize(payload),
    )


def get_cached_payload(namespace: str, identifier: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    raw = _safe_execute(client.get, build_redis_key("cache", namespace, identifier))
    return _deserialize(raw)


def delete_cached_payload(namespace: str, identifier: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    _safe_execute(client.delete, build_redis_key("cache", namespace, identifier))


# ── Cache por tenant ──────────────────────────────────────────────────────────

def set_tenant_cache(tenant_id: str, namespace: str, identifier: str, payload: Any, ttl_seconds: int = 60) -> None:
    set_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier, payload, ttl_seconds)


def get_tenant_cache(tenant_id: str, namespace: str, identifier: str) -> Any | None:
    return get_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier)


def delete_tenant_cache(tenant_id: str, namespace: str, identifier: str) -> None:
    delete_cached_payload(f"tenant:{tenant_id}:{namespace}", identifier)


# ── Rate limiting ─────────────────────────────────────────────────────────────

def check_rate_limit(scope: str, identifier: str, *, limit: int, window_seconds: int = 60) -> dict[str, int | bool]:
    client = get_redis_client()
    if client is None:
        return {"allowed": True, "count": 0, "limit": limit, "remaining": limit}
    key = build_redis_key("rate_limit", scope, identifier)
    count = _safe_execute(client.incr, key)
    if count is None:
        return {"allowed": True, "count": 0, "limit": limit, "remaining": limit}
    count = int(count)
    if count == 1:
        _safe_execute(client.expire, key, max(1, int(window_seconds)))
    remaining = max(0, int(limit) - count)
    return {
        "allowed": count <= int(limit),
        "count": count,
        "limit": int(limit),
        "remaining": remaining,
    }


# ── Estado de tareas ──────────────────────────────────────────────────────────

def store_task_state(task_name: str, task_id: str, payload: dict[str, Any], ttl_seconds: int = 3600) -> None:
    set_cached_payload("task_state", f"{task_name}:{task_id}", payload, ttl_seconds)


def get_task_state(task_name: str, task_id: str) -> dict[str, Any] | None:
    payload = get_cached_payload("task_state", f"{task_name}:{task_id}")
    return payload if isinstance(payload, dict) else None


# ── Sesiones operacionales ────────────────────────────────────────────────────

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
    "reset_redis_client",
    "set_cached_payload",
    "set_tenant_cache",
    "store_task_state",
]
