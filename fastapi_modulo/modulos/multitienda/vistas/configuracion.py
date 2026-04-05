from __future__ import annotations
from html import escape
import json
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent.parent / "marketplace" / "backend" / "templates" / "backend_template.html"


def _normalize_logo_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "/multitienda/static/imagenes/logo_vale.png"
    if raw.startswith("/multitienda/static/"):
        return "/static/" + raw[len("/multitienda/static/"):]
    return raw


def _resolve_config_shell_template() -> str:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    start_marker = "{% if is_config_shell %}"
    else_marker = "{% else %}"
    end_marker = "{% endif %}"
    if start_marker in template and else_marker in template and end_marker in template:
        before, remainder = template.split(start_marker, 1)
        config_block, remainder = remainder.split(else_marker, 1)
        _, after = remainder.split(end_marker, 1)
        template = before + config_block + after
    return template


def configuracion_html(
    *,
    initial_store_id: str = "",
    initial_store_name: str = "",
    initial_store_type: str = "",
    initial_store_admin: str = "",
    default_logo_url: str = "/multitienda/static/imagenes/logo_vale.png",
    initial_config_json: str = "{}",
) -> str:
    return (
        _resolve_config_shell_template()
        .replace("{{ config_path }}", "/multitienda/configuracion")
        .replace("{{ blank_path }}", "/multitienda/administracion_tiendas")
        .replace("{{ add_user_path }}", "/empresa/usuarios")
        .replace("{{ initial_store_id }}", escape(initial_store_id))
        .replace("{{ initial_store_name }}", escape(initial_store_name))
        .replace("{{ initial_store_type }}", escape(initial_store_type))
        .replace("{{ initial_store_admin }}", escape(initial_store_admin))
        .replace("{{ default_logo_url }}", escape(_normalize_logo_url(default_logo_url)))
        .replace("{{ initial_config_json }}", initial_config_json or json.dumps({}))
    )
