"""
tests/test_cache_service.py
─────────────────────────────────────────────────────────────────────────────
Pruebas unitarias del cache_service sin Redis real.
Se parchea el cliente Redis con un dict en memoria para simular comportamiento.
"""

from __future__ import annotations

import pickle
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Helper: construir cliente Redis stub ──────────────────────────────────────

class _FakeRedis:
    """Stub mínimo de redis.Redis que almacena en un dict local."""

    def __init__(self):
        self._store: dict = {}

    def ping(self):
        return True

    def setex(self, key: str, ttl: int, value: bytes):
        self._store[key] = value

    def get(self, key: str):
        return self._store.get(key)

    def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)

    def scan_iter(self, match: str = "*"):
        import fnmatch
        pattern = match.replace("*", "")
        yield from (k for k in self._store if pattern in k)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.fixture()
def cache(monkeypatch):
    """
    Importa cache_service fresco con el cliente Redis sustituido por _FakeRedis.
    Recarga el módulo para evitar que lru_cache de _get_client interfiera.
    """
    import importlib
    import fastapi_modulo.modulos_sipet.frontend.servicios.cache_service as cs
    importlib.reload(cs)

    fake = _FakeRedis()
    monkeypatch.setattr(cs, "_get_client", lambda: fake)
    return cs


def test_set_and_get(cache):
    cache.set("page:home", "<html>home</html>")
    result = cache.get("page:home")
    assert result == "<html>home</html>"


def test_get_missing_returns_none(cache):
    assert cache.get("page:nonexistent") is None


def test_delete_removes_key(cache):
    cache.set("page:bye", "content")
    cache.delete("page:bye")
    assert cache.get("page:bye") is None


def test_set_dict_and_get_roundtrip(cache):
    data = {"items": [{"id": "a", "status": "optimized"}]}
    cache.set("gallery:list", data)
    result = cache.get("gallery:list")
    assert isinstance(result, dict)
    assert result["items"][0]["id"] == "a"


def test_clear_all_removes_prefixed_keys(cache):
    cache.set("page:x", "x")
    cache.set("page:y", "y")
    cache.clear_all()
    assert cache.get("page:x") is None
    assert cache.get("page:y") is None


def test_get_returns_none_when_redis_unavailable(monkeypatch):
    import importlib
    import fastapi_modulo.modulos_sipet.frontend.servicios.cache_service as cs
    importlib.reload(cs)
    monkeypatch.setattr(cs, "_get_client", lambda: None)
    assert cs.get("any-key") is None


def test_set_is_noop_when_redis_unavailable(monkeypatch):
    import importlib
    import fastapi_modulo.modulos_sipet.frontend.servicios.cache_service as cs
    importlib.reload(cs)
    monkeypatch.setattr(cs, "_get_client", lambda: None)
    # Should not raise
    cs.set("any-key", "any-value")


def test_delete_is_noop_when_redis_unavailable(monkeypatch):
    import importlib
    import fastapi_modulo.modulos_sipet.frontend.servicios.cache_service as cs
    importlib.reload(cs)
    monkeypatch.setattr(cs, "_get_client", lambda: None)
    cs.delete("missing-key")  # Must not raise
