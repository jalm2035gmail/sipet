from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

from redis import Redis

REDIS_URL = (
    os.environ.get("WEB_SECURITY_REDIS_URL")
    or os.environ.get("REDIS_URL")
    or "redis://localhost:6379/0"
).strip()
REDIS_ENABLED = (os.environ.get("WEB_SECURITY_REDIS_ENABLED") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
REDIS_PREFIX = (os.environ.get("WEB_SECURITY_REDIS_PREFIX") or "web:security").strip() or "web:security"
_REDIS_CLIENT: Optional[Redis] = None
_REDIS_UNAVAILABLE = False


def get_redis_client() -> Optional[Redis]:
    global _REDIS_CLIENT, _REDIS_UNAVAILABLE
    if not REDIS_ENABLED or _REDIS_UNAVAILABLE:
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


def _key(*parts: str) -> str:
    safe_parts = [str(part or "").strip() for part in parts if str(part or "").strip()]
    return ":".join([REDIS_PREFIX, *safe_parts])


def rate_limit_increment(scope: str, identifier: str, window_seconds: int) -> int:
    client = get_redis_client()
    if client is None:
        return 0
    key = _key("rate", scope, identifier)
    count = int(client.incr(key))
    if count == 1:
        client.expire(key, max(1, int(window_seconds)))
    return count


def rate_limit_get(scope: str, identifier: str) -> int:
    client = get_redis_client()
    if client is None:
        return 0
    value = client.get(_key("rate", scope, identifier))
    try:
        return int(value or 0)
    except Exception:
        return 0


def rate_limit_clear(scope: str, identifier: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.delete(_key("rate", scope, identifier))


def sensitive_endpoint_key(path: str) -> str:
    normalized = str(path or "").strip().lower().replace("/", ":")
    return normalized.strip(":") or "root"


def cache_json(namespace: str, identifier: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.setex(_key("cache", namespace, identifier), max(1, int(ttl_seconds)), json.dumps(payload))


def get_cached_json(namespace: str, identifier: str) -> Optional[dict[str, Any]]:
    client = get_redis_client()
    if client is None:
        return None
    raw = client.get(_key("cache", namespace, identifier))
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def delete_cached(namespace: str, identifier: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.delete(_key("cache", namespace, identifier))


def mark_session_active(session_jti: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    cache_json("session_active", session_jti, payload, ttl_seconds)


def get_active_session(session_jti: str) -> Optional[dict[str, Any]]:
    return get_cached_json("session_active", session_jti)


def mark_session_revoked(session_jti: str, ttl_seconds: int) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.setex(_key("session_revoked", session_jti), max(1, int(ttl_seconds)), str(int(time.time())))
    client.delete(_key("cache", "session_active", session_jti))


def is_session_revoked(session_jti: str) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    return bool(client.exists(_key("session_revoked", session_jti)))
