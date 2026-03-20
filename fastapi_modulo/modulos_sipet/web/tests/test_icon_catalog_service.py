from __future__ import annotations

from fastapi_modulo.modulos_sipet.web.servicios import icon_catalog_service


def test_resolve_module_and_role_icons() -> None:
    assert icon_catalog_service.resolve_module_icon("crm").startswith("fa-")
    assert icon_catalog_service.resolve_role_icon("superadmin").startswith("fa-")
    assert icon_catalog_service.resolve_action_icon("export").startswith("fa-")


def test_resolve_module_icon_accepts_legacy_fontawesome_formats() -> None:
    assert icon_catalog_service.resolve_module_icon("custom", "fa fa-square-poll-vertical") == "fa fa-square-poll-vertical"
    assert icon_catalog_service.resolve_module_icon("custom", "fas fa-user") == "fa-solid fa-user"
    assert icon_catalog_service.resolve_module_icon("custom", "fa-square-poll-vertical") == "fa fa-square-poll-vertical"
    assert icon_catalog_service.resolve_module_icon("custom", "fafa-square-poll-vertical") == "fa fa-square-poll-vertical"
