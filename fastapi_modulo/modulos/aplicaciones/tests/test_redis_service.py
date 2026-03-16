from __future__ import annotations

from fastapi import HTTPException

from fastapi_modulo.modulos.aplicaciones.servicios import catalog_service, redis_service


class _FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def setex(self, key: str, _ttl: int, value: str) -> None:
        self.storage[key] = value

    def get(self, key: str) -> str | None:
        return self.storage.get(key)

    def delete(self, key: str) -> None:
        self.storage.pop(key, None)

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):  # noqa: ARG002
        if nx and key in self.storage:
            return False
        self.storage[key] = value
        return True


def test_guarded_lock_blocks_second_holder(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(redis_service, "get_redis_client", lambda: fake)

    with redis_service.guarded_lock("app_upload:crm", detail="ocupado"):
        try:
            with redis_service.guarded_lock("app_upload:crm", detail="ocupado"):
                assert False, "second lock should fail"
        except HTTPException as exc:
            assert exc.status_code == 409
            assert exc.detail == "ocupado"


def test_catalog_service_uses_cached_payload(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(redis_service, "get_redis_client", lambda: fake)
    monkeypatch.setattr(catalog_service, "list_catalog_modules", lambda: [{"key": "crm", "label": "CRM", "enabled": True}])
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {"crm": {"ok": True, "missing": [], "module_dir": "/tmp/crm"}})
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/crm")
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    first = catalog_service.decorate_modules_payload()
    monkeypatch.setattr(catalog_service, "list_catalog_modules", lambda: (_ for _ in ()).throw(AssertionError("cache missed")))
    second = catalog_service.decorate_modules_payload()

    assert first[0]["key"] == "crm"
    assert second[0]["key"] == "crm"


def test_zip_inspection_cache_roundtrip(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(redis_service, "get_redis_client", lambda: fake)

    redis_service.cache_zip_inspection("crm", "ABC123", {"checksum": "ABC123", "total_files": 4})
    cached = redis_service.get_cached_zip_inspection("crm", "abc123")

    assert cached is not None
    assert cached["checksum"] == "ABC123"
    assert cached["total_files"] == 4
