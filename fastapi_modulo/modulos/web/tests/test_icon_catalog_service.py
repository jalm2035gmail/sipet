from __future__ import annotations

from fastapi_modulo.modulos.web.servicios import icon_catalog_service


def test_resolve_module_and_role_icons() -> None:
    assert icon_catalog_service.resolve_module_icon("crm").startswith("fa-")
    assert icon_catalog_service.resolve_role_icon("superadmin").startswith("fa-")
    assert icon_catalog_service.resolve_action_icon("export").startswith("fa-")
