from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos_sipet.web.servicios import module_catalog_service


def _request() -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace(tenant_key="default"), cookies={})


def test_sidebar_hides_capacitacion_without_role_assignment(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(
        module_catalog_service,
        "_cached_modules_payload",
        lambda: (
            {
                "key": "capacitacion",
                "label": "Capacitación",
                "route": "/capacitacion",
                "icon": "fa-solid fa-graduation-cap",
                "icon_url": "",
                "sidebar_visible": True,
                "app_access_name": "Capacitacion",
                "sequence": "10",
            },
        ),
    )
    monkeypatch.setattr(module_catalog_service, "is_module_enabled", lambda key, tenant_key=None: True)
    monkeypatch.setattr(module_catalog_service, "get_user_app_access", lambda request: ["Capacitacion"])
    monkeypatch.setattr(module_catalog_service, "get_user_screen_access_levels", lambda request: {})
    monkeypatch.setattr(module_catalog_service, "is_superadmin", lambda request: False)
    monkeypatch.setattr(module_catalog_service, "is_admin_or_superadmin", lambda request: False)

    modules = module_catalog_service.build_sidebar_modules(request)

    assert modules == []


def test_sidebar_shows_capacitacion_with_screen_role_assignment(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(
        module_catalog_service,
        "_cached_modules_payload",
        lambda: (
            {
                "key": "capacitacion",
                "label": "Capacitación",
                "route": "/capacitacion",
                "icon": "fa-solid fa-graduation-cap",
                "icon_url": "",
                "sidebar_visible": True,
                "app_access_name": "Capacitacion",
                "sequence": "10",
            },
        ),
    )
    monkeypatch.setattr(module_catalog_service, "is_module_enabled", lambda key, tenant_key=None: True)
    monkeypatch.setattr(module_catalog_service, "get_user_app_access", lambda request: ["Capacitacion"])
    monkeypatch.setattr(
        module_catalog_service,
        "get_user_screen_access_levels",
        lambda request: {"capacitacion": {"user_only": True}},
    )
    monkeypatch.setattr(module_catalog_service, "is_superadmin", lambda request: False)
    monkeypatch.setattr(module_catalog_service, "is_admin_or_superadmin", lambda request: False)

    modules = module_catalog_service.build_sidebar_modules(request)

    assert len(modules) == 1
    assert modules[0]["key"] == "capacitacion"
