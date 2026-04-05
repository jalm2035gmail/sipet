from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.access_roles import MULTITIENDA_ROLE_DEFINITIONS


def test_multitienda_access_roles_define_store_admin_and_seller_profiles() -> None:
    roles = {entry["role_name"]: entry for entry in MULTITIENDA_ROLE_DEFINITIONS}

    assert "administrador_tienda" in roles
    assert "vendedor_tienda" in roles
    assert roles["administrador_tienda"]["screen_access_levels"]["Multitienda"]["full_access"] is True
    assert roles["administrador_tienda"]["screen_access_levels"]["multitienda.configuracion"]["full_access"] is True
    assert "Reportes" not in roles["administrador_tienda"]["screen_access_levels"]
    assert roles["vendedor_tienda"]["screen_access_levels"]["Multitienda"]["special_permissions"] is True
    assert roles["vendedor_tienda"]["screen_access_levels"]["Reportes"]["read_only"] is True
