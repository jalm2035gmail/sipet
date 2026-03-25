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


def test_sidebar_preserves_expected_module_order(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(
        module_catalog_service,
        "_cached_modules_payload",
        lambda: (
            {"key": "organizacion", "label": "Organización", "route": "/inicio/departamentos", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "Organizacion", "sequence": "100"},
            {"key": "frontend", "label": "Web", "route": "/web", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "Frontend", "sequence": "200"},
            {"key": "multitienda", "label": "Multitienda", "route": "/multitienda", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "Multitienda", "sequence": "300"},
            {"key": "empresa", "label": "Empresa", "route": "/identidad-institucional", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "Empresa", "sequence": "400"},
            {"key": "multiempresa", "label": "Multiempresa", "route": "/multiempresa", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "Multiempresa", "sequence": "500"},
            {"key": "system_admin", "label": "Aplicaciones", "route": "/aplicaciones", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "", "sequence": "600"},
            {"key": "backend", "label": "Configuración", "route": "/ajustes/configuracion", "icon": "", "icon_url": "", "sidebar_visible": True, "app_access_name": "", "sequence": "700"},
        ),
    )
    monkeypatch.setattr(module_catalog_service, "is_module_enabled", lambda key, tenant_key=None: True)
    monkeypatch.setattr(
        module_catalog_service,
        "get_user_app_access",
        lambda request: ["Organizacion", "Frontend", "Multitienda", "Empresa", "Multiempresa"],
    )
    monkeypatch.setattr(module_catalog_service, "get_user_screen_access_levels", lambda request: {})
    monkeypatch.setattr(module_catalog_service, "is_superadmin", lambda request: True)
    monkeypatch.setattr(module_catalog_service, "is_admin_or_superadmin", lambda request: True)

    modules = module_catalog_service.build_sidebar_modules(request)

    assert [item["key"] for item in modules] == [
        "organizacion",
        "frontend",
        "multitienda",
        "empresa",
        "multiempresa",
        "system_admin",
        "backend",
    ]
