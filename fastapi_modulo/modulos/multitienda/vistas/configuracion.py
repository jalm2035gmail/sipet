from __future__ import annotations
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent.parent / "marketplace" / "backend" / "templates" / "backend_template.html"


def configuracion_html() -> str:
    return (
        _TEMPLATE_PATH.read_text(encoding="utf-8")
        .replace("{{ config_path }}", "/multitienda/configuracion")
        .replace("{{ blank_path }}", "/multitienda/administracion_tiendas")
        .replace("{{ add_user_path }}", "/empresa/usuarios")
    )
