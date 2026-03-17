from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos.personalizacion.modelos.theme_system import MAIN_THEME_KEYS, build_institutional_theme
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores


def build_view_buttons_html(view_buttons: Optional[List[Dict]]) -> str:
    if not view_buttons:
        return ""
    icon_map = {
        "form": "/templates/icon/form.svg",
        "lista": "/templates/icon/list.svg",
        "kanban": "/templates/icon/kanban.svg",
        "cuadricula": "/templates/icon/grid.svg",
        "organigrama": "/templates/icon/organigrama.svg",
        "grafica": "/templates/icon/grafica.svg",
    }
    pieces = []
    for button in view_buttons:
        label = str(button.get("label", "")).strip()
        if not label:
            continue
        normalized_label = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii").strip().lower()
        icon = button.get("icon") or icon_map.get(normalized_label)
        view = button.get("view")
        url = button.get("url")
        classes = "view-pill"
        if button.get("active"):
            classes += " active"
        attrs = []
        if view:
            attrs.append(f'data-view="{view}"')
        if url:
            attrs.append(f'data-url="{url}"')
        attr_str = f' {" ".join(attrs)}' if attrs else ""
        icon_html = ""
        if icon:
            icon_html = (
                f'<span class="view-pill-icon-mask" aria-hidden="true" '
                f'style="--view-pill-icon-url:url(\'{icon}\')"></span>'
            )
        pieces.append(f'<button class="{classes}" type="button"{attr_str}>{icon_html}<span class="view-pill-label">{label}</span></button>')
    return "".join(pieces)


def get_colores_context() -> Dict[str, str]:
    db = SessionLocal()
    try:
        stored_colors = {str(c.key or "").strip(): str(c.value or "").strip() for c in db.query(Colores).all()}
    finally:
        db.close()
    main_colors = {key: stored_colors.get(key, "") for key in MAIN_THEME_KEYS}
    return build_institutional_theme(main_colors)

