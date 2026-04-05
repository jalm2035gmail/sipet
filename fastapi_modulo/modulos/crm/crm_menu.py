from __future__ import annotations

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class CRMMenuItem:
    panel_id: str
    label: str
    href: str
    description: str


CRM_MENU_ITEMS: tuple[CRMMenuItem, ...] = (
    CRMMenuItem(
        panel_id="contactos",
        label="Contactos",
        href="/crm/contactos",
        description="Contactos de CRM.",
    ),
    CRMMenuItem(
        panel_id="oportunidades",
        label="Oportunidades",
        href="/crm/oportunidades",
        description="Oportunidades de CRM.",
    ),
    CRMMenuItem(
        panel_id="actividades",
        label="Actividades",
        href="/crm/actividades",
        description="Actividades de CRM.",
    ),
    CRMMenuItem(
        panel_id="notas",
        label="Notas",
        href="/crm/notas",
        description="Notas de CRM.",
    ),
    CRMMenuItem(
        panel_id="campanias",
        label="Campañas",
        href="/crm/campanias",
        description="Campañas de CRM.",
    ),
    CRMMenuItem(
        panel_id="pendientes",
        label="Mis pendientes",
        href="/crm/pendientes",
        description="Actividades vencidas, leads sin asignar y oportunidades sin acción.",
    ),
    CRMMenuItem(
        panel_id="leads",
        label="Leads nuevos",
        href="/crm/leads",
        description="Bandeja de leads y prospectos recientes.",
    ),
)


CRM_MENU_BY_PANEL = {item.panel_id: item for item in CRM_MENU_ITEMS}
DEFAULT_MENU_PANEL = CRM_MENU_ITEMS[0].panel_id


def get_crm_menu_item(panel_id: str) -> CRMMenuItem:
    return CRM_MENU_BY_PANEL.get(panel_id, CRM_MENU_BY_PANEL[DEFAULT_MENU_PANEL])


def render_crm_menu(active_panel: str = DEFAULT_MENU_PANEL) -> str:
    buttons: list[str] = []
    for item in CRM_MENU_ITEMS:
        classes = "crm-nav-btn"
        if item.panel_id == active_panel:
            classes += " is-active"
        buttons.append(
            (
                '<button type="button" class="{classes}" data-panel="{panel}">'
                "{label}</button>"
            ).format(
                classes=classes,
                panel=escape(item.panel_id, quote=True),
                label=escape(item.label),
            )
        )
    return '<nav class="crm-nav" id="crm-nav" aria-label="Secciones CRM">{buttons}</nav>'.format(
        buttons="".join(buttons)
    )
