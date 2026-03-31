from __future__ import annotations

from pathlib import Path


def test_backend_nav_catalog_includes_multitienda_submenus() -> None:
    content = Path("fastapi_modulo/modulos_sipet/web/vistas/backend_nav_catalog.html").read_text(encoding="utf-8")

    assert '"Multitienda": [' in content
    assert '/multitienda/configuracion' in content
    assert '/multitienda/administracion_tiendas' in content
    assert "{% if current_role in ['superadministrador', 'superadmin'] %}" in content
