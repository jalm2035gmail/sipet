from __future__ import annotations

from fastapi_modulo.modulos_sipet.web.servicios import redis_security_service


class _FakeRedis:
    def __init__(self) -> None:
        self.store = {}

    def incr(self, key):
        value = int(self.store.get(key, 0)) + 1
        self.store[key] = value
        return value

    def expire(self, key, _ttl):
        return True

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)
        return 1

    def setex(self, key, _ttl, value):
        self.store[key] = value
        return True

    def exists(self, key):
        return 1 if key in self.store else 0


def test_rate_limit_and_cache_helpers(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(redis_security_service, "get_redis_client", lambda: fake)

    assert redis_security_service.rate_limit_increment("ip", "1.1.1.1", 60) == 1
    assert redis_security_service.rate_limit_get("ip", "1.1.1.1") == 1
    redis_security_service.cache_json("challenge", "abc", {"ok": True}, 60)
    assert redis_security_service.get_cached_json("challenge", "abc") == {"ok": True}
    redis_security_service.mark_session_revoked("jti1", 60)
    assert redis_security_service.is_session_revoked("jti1") is True


def test_rate_limit_get_disables_broken_redis_client(monkeypatch) -> None:
    class _BrokenRedis:
        def get(self, _key):
            raise RuntimeError("redis down")

    monkeypatch.setattr(redis_security_service, "_REDIS_CLIENT", _BrokenRedis())
    monkeypatch.setattr(redis_security_service, "_REDIS_UNAVAILABLE", False)
    monkeypatch.setattr(redis_security_service, "REDIS_ENABLED", True)

    assert redis_security_service.rate_limit_get("ip", "127.0.0.1") == 0
    assert redis_security_service._REDIS_UNAVAILABLE is True


def test_resolve_redis_enabled_defaults_to_disabled_in_local_without_config(monkeypatch) -> None:
    monkeypatch.delenv("WEB_SECURITY_REDIS_ENABLED", raising=False)
    monkeypatch.delenv("WEB_SECURITY_REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(redis_security_service, "APP_ENV", "development")

    assert redis_security_service._resolve_redis_enabled() is False


def test_resolve_redis_enabled_ignores_generic_redis_url_in_local(monkeypatch) -> None:
    monkeypatch.delenv("WEB_SECURITY_REDIS_ENABLED", raising=False)
    monkeypatch.delenv("WEB_SECURITY_REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(redis_security_service, "APP_ENV", "development")

    assert redis_security_service._resolve_redis_enabled() is False


def test_resolve_redis_enabled_accepts_module_specific_url_in_local(monkeypatch) -> None:
    monkeypatch.delenv("WEB_SECURITY_REDIS_ENABLED", raising=False)
    monkeypatch.setenv("WEB_SECURITY_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(redis_security_service, "APP_ENV", "development")

    assert redis_security_service._resolve_redis_enabled() is True
