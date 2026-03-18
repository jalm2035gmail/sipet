from __future__ import annotations

import json
import os
import secrets
import time
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from fastapi import HTTPException
from redis import Redis

REDIS_URL = (
    os.environ.get("APPLICATIONS_REDIS_URL")
    or os.environ.get("REDIS_URL")
    or "redis://localhost:6379/0"
).strip()
REDIS_ENABLED = (os.environ.get("APPLICATIONS_REDIS_ENABLED") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
REDIS_PREFIX = (os.environ.get("APPLICATIONS_REDIS_PREFIX") or "applications").strip() or "applications"
REDIS_RETRY_INTERVAL = int((os.environ.get("APPLICATIONS_REDIS_RETRY_SECONDS") or "30").strip() or "30")

_REDIS_CLIENT: Optional[Redis] = None
_REDIS_UNAVAILABLE = False
_REDIS_LAST_ATTEMPT: float = 0.0


def get_redis_client() -> Optional[Redis]:
    global _REDIS_CLIENT, _REDIS_UNAVAILABLE, _REDIS_LAST_ATTEMPT
    if not REDIS_ENABLED:
        return None
    if _REDIS_UNAVAILABLE:
        if time.monotonic() - _REDIS_LAST_ATTEMPT < REDIS_RETRY_INTERVAL:
            return None
        # Intervalo de reintento cumplido — resetear para intentar reconexión
        _REDIS_UNAVAILABLE = False
        _REDIS_CLIENT = None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    _REDIS_LAST_ATTEMPT = time.monotonic()
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


def set_cached_payload(namespace: str, identifier: str, payload: Any, ttl_seconds: int) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(_key("cache", namespace, identifier), max(1, int(ttl_seconds)), json.dumps(payload, ensure_ascii=True))
    except Exception:
        _mark_unavailable()


def get_cached_payload(namespace: str, identifier: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(_key("cache", namespace, identifier))
    except Exception:
        _mark_unavailable()
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def delete_cached_payload(namespace: str, identifier: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(_key("cache", namespace, identifier))
    except Exception:
        _mark_unavailable()


def _mark_unavailable() -> None:
    """Marca Redis como no disponible para forzar reintento en el próximo ciclo."""
    global _REDIS_CLIENT, _REDIS_UNAVAILABLE, _REDIS_LAST_ATTEMPT
    _REDIS_UNAVAILABLE = True
    _REDIS_CLIENT = None
    _REDIS_LAST_ATTEMPT = time.monotonic()


def cache_catalog(payload: list[dict[str, Any]], ttl_seconds: int = 60) -> None:
    set_cached_payload("catalog", "modules", payload, ttl_seconds)


def get_cached_catalog() -> list[dict[str, Any]] | None:
    payload = get_cached_payload("catalog", "modules")
    return payload if isinstance(payload, list) else None


def invalidate_catalog_cache() -> None:
    delete_cached_payload("catalog", "modules")


def _inspection_key(module_key: str, checksum: str) -> str:
    return f"{str(module_key or '').strip()}:{str(checksum or '').strip().lower()}"


def cache_zip_inspection(module_key: str, checksum: str, payload: dict[str, Any], ttl_seconds: int = 600) -> None:
    set_cached_payload("zip_inspection", _inspection_key(module_key, checksum), payload, ttl_seconds)


def get_cached_zip_inspection(module_key: str, checksum: str) -> dict[str, Any] | None:
    payload = get_cached_payload("zip_inspection", _inspection_key(module_key, checksum))
    return payload if isinstance(payload, dict) else None


def invalidate_zip_inspection(module_key: str, checksum: str) -> None:
    delete_cached_payload("zip_inspection", _inspection_key(module_key, checksum))


def store_task_state(task_name: str, task_id: str, payload: dict[str, Any], ttl_seconds: int = 3600) -> None:
    set_cached_payload("task_state", f"{task_name}:{task_id}", payload, ttl_seconds)


def get_task_state(task_name: str, task_id: str) -> dict[str, Any] | None:
    payload = get_cached_payload("task_state", f"{task_name}:{task_id}")
    return payload if isinstance(payload, dict) else None


def acquire_lock(lock_name: str, ttl_seconds: int = 120) -> str:
    client = get_redis_client()
    if client is None:
        return ""
    token = secrets.token_hex(16)
    try:
        locked = client.set(_key("lock", lock_name), token, nx=True, ex=max(1, int(ttl_seconds)))
    except Exception:
        _mark_unavailable()
        return ""
    return token if locked else ""


def release_lock(lock_name: str, token: str) -> None:
    client = get_redis_client()
    if client is None or not token:
        return
    redis_key = _key("lock", lock_name)
    try:
        current = client.get(redis_key)
        if current == token:
            client.delete(redis_key)
    except Exception:
        _mark_unavailable()


@contextmanager
def guarded_lock(lock_name: str, *, ttl_seconds: int = 120, detail: str) -> Iterator[None]:
    token = acquire_lock(lock_name, ttl_seconds=ttl_seconds)
    if get_redis_client() is not None and not token:
        raise HTTPException(status_code=409, detail=detail)
    try:
        yield
    finally:
        release_lock(lock_name, token)


__all__ = [
    "acquire_lock",
    "cache_catalog",
    "cache_zip_inspection",
    "delete_cached_payload",
    "get_cached_catalog",
    "get_cached_payload",
    "get_cached_zip_inspection",
    "get_redis_client",
    "get_task_state",
    "guarded_lock",
    "invalidate_catalog_cache",
    "invalidate_zip_inspection",
    "release_lock",
    "set_cached_payload",
    "store_task_state",
]
