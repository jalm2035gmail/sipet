from __future__ import annotations

import secrets
from contextlib import contextmanager
from typing import Iterator

from fastapi import HTTPException

from fastapi_modulo.modulos_sipet.modulo_base.core.cache_service import build_redis_key, get_redis_client


def acquire_lock(lock_name: str, ttl_seconds: int = 120) -> str:
    client = get_redis_client()
    if client is None:
        return ""
    token = secrets.token_hex(16)
    locked = client.set(build_redis_key("lock", lock_name), token, nx=True, ex=max(1, int(ttl_seconds)))
    return token if locked else ""


def release_lock(lock_name: str, token: str) -> None:
    client = get_redis_client()
    if client is None or not token:
        return
    key = build_redis_key("lock", lock_name)
    try:
        if client.get(key) == token:
            client.delete(key)
    except Exception:
        return


@contextmanager
def guarded_lock(lock_name: str, *, ttl_seconds: int = 120, detail: str = "Recurso bloqueado") -> Iterator[None]:
    token = acquire_lock(lock_name, ttl_seconds=ttl_seconds)
    if get_redis_client() is not None and not token:
        raise HTTPException(status_code=409, detail=detail)
    try:
        yield
    finally:
        release_lock(lock_name, token)


__all__ = [
    "acquire_lock",
    "guarded_lock",
    "release_lock",
]
