from __future__ import annotations

from fastapi_modulo.modulos.web.servicios import redis_security_service


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
