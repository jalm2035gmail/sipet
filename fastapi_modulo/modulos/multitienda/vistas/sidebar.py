from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
SIDEBAR_CSS_PATH = MODULE_DIR / "static" / "css" / "sidebar.css"

SECTION_HINTS = {
    "inicio": "Resumen del marketplace",
    "videos": "Contenido de tienda",
    "productos": "Catalogo y fichas",
    "referidos": "Programa de crecimiento",
    "reservaciones": "Agenda y seguimiento",
    "cupones": "Descuentos y promociones",
    "fidelizacion": "Clientes frecuentes",
    "whatsapp": "Campanas y mensajeria",
    "empleados": "Equipo interno",
    "seguidores": "Clientes y socios",
    "proveedores": "Red comercial",
    "ia": "Asistentes del negocio",
    "institucion_financiera": "Creditos y comisiones",
    "apartados": "Abonos y entregas",
    "subastas": "Pujas y adjudicacion",
    "configuracion": "Ajustes de tienda",
    "gestion": "Operacion del marketplace",
    "repartidores": "Logistica y entregas",
}

SECTION_GROUPS = [
    ("General", {"inicio", "gestion"}),
    ("Contenido", {"videos", "productos"}),
    ("Comercial", {"referidos", "cupones", "fidelizacion", "whatsapp", "seguidores", "proveedores", "subastas"}),
    ("Operacion", {"reservaciones", "empleados", "apartados", "repartidores", "institucion_financiera", "ia"}),
    ("Ajustes", {"configuracion"}),
]

GESTION_SUBSECTIONS = [
    ("tiendas", "Alta de tienda"),
]


@lru_cache(maxsize=1)
def load_sidebar_css() -> str:
    return SIDEBAR_CSS_PATH.read_text(encoding="utf-8")


def _group_for_section(section_id: str) -> str:
    normalized_id = str(section_id or "").strip()
    for label, members in SECTION_GROUPS:
        if normalized_id in members:
            return label
    return "General"


def build_sidebar_markup(
    sections: list[dict[str, str]],
    current_section: str,
    viewer_name: str,
    store_name: str = "",
) -> str:
    can_open_config = any(section.get("id") == "configuracion" for section in sections)
    grouped_items: dict[str, list[str]] = {}
    for section in sections:
        is_active = section["id"] == current_section
        group_label = _group_for_section(section["id"])
        if section["id"] == "gestion":
            submenu_links = "".join(
                '<a class="sb-subitem" href="/multitienda/administracion_tiendas?panel={panel}" data-gestion-panel="{panel}">{label}</a>'.format(
                    panel=escape(panel),
                    label=escape(label),
                )
                for panel, label in GESTION_SUBSECTIONS
            )
            grouped_items.setdefault(group_label, []).append(
                '<div class="sb-collapsible{active}" data-sb-collapsible="gestion">'
                '<button class="sb-item sb-item--toggle{active}" type="button" data-sb-collapsible-toggle="gestion" aria-expanded="{expanded}">'
                '<div class="sb-item-icon"><i class="{icon}" aria-hidden="true"></i></div>'
                '<div class="sb-item-body"><div class="sb-item-title">{label}</div><div class="sb-item-subtitle">{hint}</div></div>'
                '<div class="sb-item-caret"><i class="fa-solid fa-chevron-down" aria-hidden="true"></i></div>'
                "</button>"
                '<div class="sb-submenu" data-sb-collapsible-body="gestion">{submenu}</div>'
                "</div>".format(
                    active=" is-active is-open" if is_active else "",
                    expanded="true" if is_active else "false",
                    icon=escape(section["icon"]),
                    label=escape(section["label"]),
                    hint=escape(SECTION_HINTS.get(section["id"], "Panel del modulo")),
                    submenu=submenu_links,
                )
            )
            continue
        grouped_items.setdefault(group_label, []).append(
            '<a class="sb-item{active}" href="{route}">'
            '<div class="sb-item-icon"><i class="{icon}" aria-hidden="true"></i></div>'
            '<div class="sb-item-body"><div class="sb-item-title">{label}</div><div class="sb-item-subtitle">{hint}</div></div>'
            "</a>".format(
                active=" is-active" if is_active else "",
                route=escape(section["route"]),
                icon=escape(section["icon"]),
                label=escape(section["label"]),
                hint=escape(SECTION_HINTS.get(section["id"], "Panel del modulo")),
            )
        )

    nav_groups = []
    for group_label, _members in SECTION_GROUPS:
        items = grouped_items.get(group_label)
        if not items:
            continue
        nav_groups.append(
            '<section class="sb-section">'
            '<div class="sb-section-label"><span>{label}</span></div>'
            "{items}"
            "</section>".format(label=escape(group_label), items="".join(items))
        )

    return (
        '<aside class="sidebar-dark">'
        '<div class="sb-header">'
        '<div class="sb-logo"><i class="fa-solid fa-store" aria-hidden="true"></i></div>'
        '<div class="sb-title-wrap"><h2 class="sb-title">Multitienda</h2><div class="sb-subtitle">Operacion comercial</div></div>'
        '<button type="button" class="sb-toggle" data-multitienda-sidebar-toggle="1" aria-expanded="true" aria-label="Compactar menu"><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>'
        "</div>"
        '<div class="sb-divider"></div>'
        '<div class="sb-scroll">'
        + "".join(nav_groups)
        + "</div>"
        + '<div class="sb-footer">'
        + '<div class="sb-footer-card">'
        + '<div class="sb-avatar">'
        + escape((viewer_name or "U")[:1].upper())
        + "</div>"
        + '<div class="sb-user"><div class="sb-user-name">'
        + escape(viewer_name or "Usuario")
        + '</div><div class="sb-user-meta" data-multitienda-sidebar-store>'
        + escape(store_name or "Sin tienda")
        + "</div></div>"
        + '<div class="sb-footer-actions">'
        + (
            '<a class="sb-action" href="/multitienda/configuracion" aria-label="Configuracion"><i class="fa-solid fa-gear" aria-hidden="true"></i></a>'
            if can_open_config else ""
        )
        + "</div>"
        + "</div>"
        + "</div>"
        + "</aside>"
    )


__all__ = ["build_sidebar_markup", "load_sidebar_css"]
