from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from fastapi_modulo.modulos_sipet.aplicaciones.servicios import catalog_service


def test_get_cached_architecture_report_uses_cached_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "get_cached_payload",
        lambda namespace, identifier: {
            "architecture_ok": False,
            "architecture_errors": [{"code": "cached", "message": "cached", "path": "/tmp/a.py"}],
            "architecture_warnings": [],
            "validated_at": "2026-04-02T12:00:00+00:00",
        },
    )
    monkeypatch.setattr(catalog_service, "get_latest_registry_audit", lambda module_key, action: (_ for _ in ()).throw(AssertionError("db should not run")))
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda module_key, target_root=None: (_ for _ in ()).throw(AssertionError("compute should not run")))

    payload = catalog_service.get_cached_architecture_report("crm", "/tmp/crm")

    assert payload["architecture_ok"] is False
    assert payload["architecture_errors"][0]["code"] == "cached"
    assert payload["validated_at"] == "2026-04-02T12:00:00+00:00"


def test_get_cached_architecture_report_recomputes_when_refresh_is_true(monkeypatch) -> None:
    persisted_payloads: list[dict] = []
    monkeypatch.setattr(catalog_service, "get_cached_payload", lambda namespace, identifier: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": [], "validated_at": "stale"})
    monkeypatch.setattr(catalog_service, "get_latest_registry_audit", lambda module_key, action: None)
    monkeypatch.setattr(
        catalog_service,
        "get_module_architecture_report",
        lambda module_key, target_root=None: {
            "architecture_ok": False,
            "architecture_errors": [{"code": "fresh", "message": "fresh", "path": "/tmp/b.py"}],
            "architecture_warnings": [],
        },
    )
    monkeypatch.setattr(catalog_service, "create_registry_audit", lambda **kwargs: persisted_payloads.append(kwargs["payload"]))
    monkeypatch.setattr(catalog_service, "set_cached_payload", lambda namespace, identifier, payload, ttl_seconds: None)

    payload = catalog_service.get_cached_architecture_report("crm", "/tmp/crm", refresh=True)

    assert payload["architecture_ok"] is False
    assert payload["architecture_errors"][0]["code"] == "fresh"
    assert payload["validated_at"]
    assert persisted_payloads[0]["architecture_errors"][0]["code"] == "fresh"


def test_decorate_modules_payload_marks_upload_root_and_state(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [{"key": "crm", "label": "CRM", "enabled": False, "description": "demo", "icon": "fa-solid fa-address-card"}],
    )
    captured: list[list[dict]] = []
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: captured.append(payload))
    monkeypatch.setattr(
        catalog_service,
        "list_registry_state",
        lambda tenant_id=None: {"crm": SimpleNamespace(enabled=True, installed_version="2.1.0")},
    )
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {"crm": {"ok": True, "has_init": True, "has_manifest": True, "missing": [], "module_dir": "/tmp/crm"}})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos/crm")
    monkeypatch.setattr(
        catalog_service,
        "get_module_architecture_report",
        lambda key, target_root=None: {"architecture_ok": False, "architecture_errors": [{"code": "db.raw_engine", "message": "bad", "path": "/tmp/crm/a.py"}], "architecture_warnings": []},
    )
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "/tmp/project/fastapi_modulo/modulos/crm/static/img/icon.png")
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
    assert payload[0]["architecture_ok"] is False
    assert payload[0]["architecture_errors"][0]["code"] == "db.raw_engine"
    assert payload[0]["is_core_module"] is False
    assert payload[0]["package_management_note"] == ""
    assert captured


def test_decorate_modules_payload_prefers_icon_when_module_has_no_uploaded_image(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [{"key": "web", "label": "Web", "enabled": True, "description": "demo", "icon": "fa-solid fa-globe"}],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos_sipet/web")
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: "/api/aplicaciones/assets/web/preview.png?variant=card")
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert payload[0]["icon"] == "fa-solid fa-globe"
    assert payload[0]["image_url"] is None


def test_decorate_modules_payload_never_exposes_modulos_sipet_as_importable(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {
                "key": "frontend",
                "label": "Frontend",
                "enabled": True,
                "description": "demo",
                "manageable": True,
                "always_enabled": True,
                "manifest_file": "fastapi_modulo/modulos_sipet/frontend/__manifest__.py",
            }
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos/frontend")
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert payload[0]["key"] == "frontend"
    assert payload[0]["package_upload_enabled"] is False
    assert payload[0]["package_target_label"] == ""
    assert payload[0]["is_core_module"] is True
    assert "núcleo de SIPET" in payload[0]["package_management_note"]


def test_decorate_modules_payload_filters_uninstalled_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {"key": "crm", "label": "CRM", "enabled": True, "description": "demo"},
            {"key": "fantasma", "label": "Fantasma", "enabled": True, "description": "demo"},
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(
        catalog_service,
        "get_module_upload_root",
        lambda key: "/tmp/project/fastapi_modulo/modulos/crm" if key == "crm" else None,
    )
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert [item["key"] for item in payload] == ["crm"]


def test_decorate_modules_payload_hides_config_only_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {"key": "crm", "label": "CRM", "enabled": True, "description": "demo"},
            {"key": "bsc", "label": "Gobierno de Aplicaciones", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "instalacion_core", "label": "Instalación", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "modulo_base", "label": "Modulo base", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "ajustes_core", "label": "Ajustes", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "ajustes_ia_core", "label": "IA", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "ia_core", "label": "IA", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "predictivo_core", "label": "Analisis predictivo", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "personalizacion_core", "label": "Colores", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "roles_core", "label": "Roles", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "membresia_core", "label": "Membresia", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "plantillas_core", "label": "Plantillas", "enabled": True, "description": "demo", "always_enabled": True},
            {"key": "diagnostico_core", "label": "Diagnóstico", "enabled": True, "description": "demo", "always_enabled": True},
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos/crm" if key == "crm" else None)
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert [item["key"] for item in payload] == ["crm"]


def test_decorate_modules_payload_dedupes_by_route_and_hides_non_application_entries(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {"key": "system_admin", "label": "Gobierno de Aplicaciones", "enabled": True, "description": "demo", "route": "/aplicaciones", "always_enabled": True, "manageable": False},
            {"key": "aplicaciones", "label": "Gobierno de Aplicaciones", "enabled": True, "description": "demo", "route": "/aplicaciones", "application": False, "always_enabled": True},
            {"key": "empresa", "label": "Personalización", "enabled": True, "description": "demo", "route": "/identidad-institucional", "always_enabled": True, "manageable": True},
            {"key": "identidad_institucional", "label": "Personalización", "enabled": True, "description": "demo", "route": "/identidad-institucional", "application": True, "always_enabled": True, "manageable": True},
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: "/tmp/project/fastapi_modulo/modulos_sipet/demo")
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert [item["key"] for item in payload] == ["system_admin", "empresa"]
    assert payload[0]["package_upload_enabled"] is False
    assert payload[1]["package_upload_enabled"] is True


def test_decorate_modules_payload_enables_package_actions_for_empresa_alias(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {"key": "empresa", "label": "Personalización", "enabled": True, "description": "demo", "route": "/identidad-institucional", "always_enabled": True, "manageable": True},
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(catalog_service, "list_registry_state", lambda tenant_id=None: {})
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert payload[0]["key"] == "empresa"
    assert payload[0]["package_upload_enabled"] is False
    assert payload[0]["package_target_label"] == ""
    assert payload[0]["package_management_note"] == "Este módulo no tiene un destino importable por paquetes ZIP."


def test_decorate_modules_payload_keeps_always_enabled_alias_active_with_stale_registry_state(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_modules",
        lambda tenant_key=None, refresh=False, include_legacy=False: [
            {"key": "empresa", "label": "Personalización", "enabled": True, "description": "demo", "route": "/identidad-institucional", "always_enabled": True, "manageable": True},
        ],
    )
    monkeypatch.setattr(catalog_service, "cache_catalog", lambda payload: None)
    monkeypatch.setattr(
        catalog_service,
        "list_registry_state",
        lambda tenant_id=None: {"empresa": SimpleNamespace(enabled=False, installed_version="1.0.0")},
    )
    monkeypatch.setattr(catalog_service, "get_protocol_audit_map", lambda: {})
    monkeypatch.setattr(catalog_service, "get_module_architecture_report", lambda key, target_root=None: {"architecture_ok": True, "architecture_errors": [], "architecture_warnings": []})
    monkeypatch.setattr(catalog_service, "get_module_upload_root", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_module_image_path", lambda key: "")
    monkeypatch.setattr(catalog_service, "get_module_catalog_image_url", lambda key: None)
    monkeypatch.setattr(catalog_service, "get_latest_package_upload", lambda key: None)

    payload = catalog_service.decorate_modules_payload()

    assert payload[0]["key"] == "empresa"
    assert payload[0]["enabled"] is True
    assert payload[0]["installed_version"] == "1.0.0"
    assert payload[0]["package_management_note"] == "Este módulo no tiene un destino importable por paquetes ZIP."
