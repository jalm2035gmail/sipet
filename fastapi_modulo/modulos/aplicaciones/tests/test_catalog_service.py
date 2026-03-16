from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from fastapi_modulo.modulos.aplicaciones.servicios import catalog_service


def test_decorate_modules_payload_marks_upload_root_and_state(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda: [{"key": "crm", "label": "CRM", "enabled": False, "description": "demo"}],
    )
    monkeypatch.setattr(catalog_service, "get_cached_catalog", lambda: None)
    captured: list[list[dict]] = []
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: captured.append(payload))
    monkeypatch.setattr(
        catalog_service,
        "list_registry_state",
        lambda: {"crm": SimpleNamespace(enabled=True, installed_version="2.1.0")},
    )
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {"crm": {"ok": True, "has_init": True, "has_manifest": True, "missing": [], "module_dir": "/tmp/crm"}})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos/crm")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: "/api/aplicaciones/assets/crm/preview.png?variant=card")
    monkeypatch.setattr(
        catalog_service,
        "get_latest_package_upload",
        lambda key: SimpleNamespace(uploaded_at=datetime(2026, 1, 2), original_filename="crm.zip"),
    )

    payload = catalog_service.decorate_modules_payload()

    assert payload[0]["enabled"] is True
    assert payload[0]["installed_version"] == "2.1.0"
    assert payload[0]["package_upload_enabled"] is True
    assert payload[0]["package_target_label"].endswith("fastapi_modulo/modulos/crm")
    assert payload[0]["image_url"].endswith("preview.png?variant=card")
    assert payload[0]["uploaded_filename"] == "crm.zip"
    assert captured


def test_decorate_modules_payload_uses_cached_catalog(monkeypatch) -> None:
    monkeypatch.setattr(catalog_service, "get_cached_catalog", lambda: [{"key": "cached"}])
    monkeypatch.setattr(catalog_service, "list_catalog_modules", lambda: (_ for _ in ()).throw(AssertionError("cache missed")))

    payload = catalog_service.decorate_modules_payload()

    assert payload == [{"key": "cached"}]
