from __future__ import annotations

from html import escape
import json
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from sqlalchemy import text

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos.multitienda.controladores.marketplace_backend import (
    build_marketplace_backend_app,
    SessionLocal,
    create_business_type,
    list_business_types,
    save_store_settings,
)
from fastapi_modulo.modulos.multitienda.servicios.access_roles import ensure_multitienda_access_roles
from fastapi_modulo.modulos.multitienda.vistas.utils import _prefix_root_relative_urls
from fastapi_modulo.modulos.multitienda.vistas.configuracion import configuracion_html
from fastapi_modulo.modulos.multitienda.vistas.gestion import gestion_html
from fastapi_modulo.modulos.multitienda.vistas.inicio import inicio_html
from fastapi_modulo.modulos.multitienda.vistas.productos import productos_html
from fastapi_modulo.modulos.multitienda.vistas.tienda import tienda_html
from fastapi_modulo.modulos.multitienda.vistas.cupones import cupones_html
from fastapi_modulo.modulos.multitienda.vistas.empleados import empleados_html
from fastapi_modulo.modulos.multitienda.vistas.seguidores import seguidores_html
from fastapi_modulo.modulos.multitienda.vistas.whatsapp import whatsapp_html
from fastapi_modulo.modulos.multitienda.vistas.reservaciones import reservaciones_html
from fastapi_modulo.modulos.multitienda.vistas.videos import videos_html
from fastapi_modulo.modulos.multitienda.vistas.proveedores import proveedores_html
from fastapi_modulo.modulos.multitienda.vistas.ia import ia_html
from fastapi_modulo.modulos.multitienda.vistas.institucion_financiera import institucion_financiera_html
from fastapi_modulo.modulos.multitienda.vistas.apartados import apartados_html
from fastapi_modulo.modulos.multitienda.vistas.subastas import subastas_html
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.membresia import Membresia, _ensure_membresia_table, _seed_membresias
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol, Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import decrypt_sensitive
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import build_backend_context
from fastapi_modulo.modulos_sipet.web.servicios.template_service import BACKEND_BASE_TEMPLATE, get_templates

router = APIRouter()
marketplace_app = build_marketplace_backend_app()
ensure_multitienda_access_roles()

_STYLE_RE = re.compile(r"<style>(.*?)</style>", re.IGNORECASE | re.DOTALL)
_MAIN_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.IGNORECASE | re.DOTALL)
_SCRIPT_RE = re.compile(r"(<script\b.*?</script>)", re.IGNORECASE | re.DOTALL)

_MODULE_SECTIONS = [
    {"id": "inicio", "label": "Inicio", "icon": "fa-solid fa-house", "route": "/multitienda/inicio"},
    {"id": "videos", "label": "Videos", "icon": "fa-solid fa-video", "route": "/multitienda/videos"},
    {"id": "productos", "label": "Productos", "icon": "fa-solid fa-box", "route": "/multitienda/productos"},
    {"id": "referidos", "label": "Referidos", "icon": "fa-solid fa-user-group", "route": "/multitienda/referidos"},
    {"id": "reservaciones", "label": "Reservaciones", "icon": "fa-solid fa-calendar-check", "route": "/multitienda/reservaciones"},
    {"id": "cupones", "label": "Cupones", "icon": "fa-solid fa-ticket", "route": "/multitienda/cupones"},
    {"id": "whatsapp", "label": "WhatsApp Business", "icon": "fa-brands fa-whatsapp", "route": "/multitienda/whatsapp"},
    {"id": "empleados", "label": "Empleados", "icon": "fa-solid fa-id-badge", "route": "/multitienda/empleados"},
    {"id": "seguidores", "label": "Seguidores", "icon": "fa-solid fa-user-group", "route": "/multitienda/seguidores"},
    {"id": "proveedores", "label": "Proveedores", "icon": "fa-solid fa-handshake", "route": "/multitienda/proveedores"},
    {"id": "ia", "label": "IA", "icon": "fa-solid fa-robot", "route": "/multitienda/ia"},
    {"id": "institucion_financiera", "label": "Institución financiera", "icon": "fa-solid fa-building-columns", "route": "/multitienda/institucion_financiera"},
    {"id": "apartados", "label": "Apartados", "icon": "fa-solid fa-box-archive", "route": "/multitienda/apartados"},
    {"id": "subastas", "label": "Subastas", "icon": "fa-solid fa-gavel", "route": "/multitienda/subastas"},
    {"id": "configuracion", "label": "Configuración", "icon": "fa-solid fa-gear", "route": "/multitienda/configuracion"},
    {"id": "gestion", "label": "Administración de tiendas", "icon": "fa-solid fa-store", "route": "/multitienda/administracion_tiendas"},
]
_MODULE_NAVBAR_BOOTSTRAP = """
<script>
(function () {
    const menuName = 'Multitienda';
    try {
        window.localStorage.setItem('sipet_active_main_menu_name', menuName);
    } catch (error) {}
})();
</script>
"""
_MODULE_LAYOUT_OVERRIDES = """
<style>
.navbar-section-menu {
    display: none !important;
}

html.ui-sidebar-modern .main-content {
    padding-right: 24px !important;
}

html.ui-sidebar-modern .content-shell,
html.ui-sidebar-modern .content-section,
.multitienda-official-view,
.multitienda-official-view .page {
    width: 100% !important;
    max-width: 100% !important;
}

.multitienda-official-view {
    padding: 8px 0 28px;
}

.multitienda-shell {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    gap: 24px;
    align-items: start;
    min-height: calc(100vh - 132px);
}

.multitienda-shell__sidebar {
    position: sticky;
    top: 20px;
    display: grid;
    gap: 18px;
    padding: 24px 18px 20px;
    border-radius: 28px;
    background:
        linear-gradient(180deg, color-mix(in srgb, var(--sidebar-bottom, #0f172a) 92%, #0b1120 8%) 0%, color-mix(in srgb, var(--sidebar-top, #142132) 96%, #0b1120 4%) 100%);
    color: #ecf5ff;
    box-shadow: 0 30px 70px rgba(15, 23, 42, 0.22);
}

.multitienda-shell__brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.multitienda-shell__brand-mark {
    width: 52px;
    height: 52px;
    border-radius: 18px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #25b7d3 0%, #2f8fdf 100%);
    color: #ffffff;
    font-size: 1.25rem;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18);
}

.multitienda-shell__brand-copy {
    min-width: 0;
    display: grid;
    gap: 2px;
}

.multitienda-shell__brand-copy strong {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.multitienda-shell__brand-copy span {
    color: rgba(236, 245, 255, 0.74);
    font-size: 0.82rem;
}

.multitienda-shell__nav {
    display: grid;
    gap: 8px;
}

.multitienda-shell__nav-label {
    margin: 0 0 4px;
    color: rgba(236, 245, 255, 0.58);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.multitienda-shell__nav-link {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 50px;
    padding: 0 14px;
    border-radius: 16px;
    color: rgba(236, 245, 255, 0.86);
    text-decoration: none;
    transition: transform 0.16s ease, background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.multitienda-shell__nav-link:hover {
    transform: translateX(2px);
    background: rgba(255, 255, 255, 0.08);
}

.multitienda-shell__nav-link.is-active {
    background: linear-gradient(135deg, rgba(37, 183, 211, 0.24) 0%, rgba(47, 143, 223, 0.26) 100%);
    color: #ffffff;
    box-shadow: inset 0 0 0 1px rgba(107, 203, 255, 0.2);
}

.multitienda-shell__nav-icon {
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: rgba(255, 255, 255, 0.08);
    color: inherit;
    flex-shrink: 0;
}

.multitienda-shell__nav-copy {
    display: grid;
    gap: 2px;
}

.multitienda-shell__nav-copy strong {
    font-size: 1rem;
    font-weight: 700;
}

.multitienda-shell__nav-copy span {
    font-size: 0.79rem;
    color: rgba(236, 245, 255, 0.62);
}

.multitienda-shell__content {
    display: grid;
    gap: 20px;
    min-width: 0;
}

.multitienda-shell__hero {
    border-radius: 32px;
    padding: 28px 30px;
    background:
        radial-gradient(circle at top right, rgba(37, 183, 211, 0.18), transparent 34%),
        linear-gradient(160deg, color-mix(in srgb, var(--content-bg, #ffffff) 92%, #ecfeff 8%) 0%, color-mix(in srgb, var(--content-bg, #ffffff) 96%, #f8fafc 4%) 100%);
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 56%, #ffffff 44%);
    box-shadow: 0 22px 58px rgba(15, 23, 42, 0.08);
}

.multitienda-shell__hero[hidden] {
    display: none !important;
}

.multitienda-shell__hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.8fr);
    gap: 18px;
    align-items: start;
}

.multitienda-shell__hero-copy {
    display: grid;
    gap: 10px;
}

.multitienda-shell__eyebrow {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.06);
    color: color-mix(in srgb, var(--body-text, #0f172a) 72%, #ffffff 28%);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.multitienda-shell__hero-copy h1 {
    margin: 0;
    font-size: clamp(1.8rem, 3vw, 2.45rem);
    line-height: 1.05;
    letter-spacing: -0.03em;
    color: var(--body-text, #0f172a);
}

.multitienda-shell__hero-copy p {
    margin: 0;
    max-width: 60ch;
    color: color-mix(in srgb, var(--body-text, #0f172a) 68%, #ffffff 32%);
    line-height: 1.6;
}

.multitienda-shell__hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 4px;
}

.multitienda-shell__meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 38px;
    padding: 0 14px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--content-bg, #ffffff) 86%, #e2e8f0 14%);
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 54%, #ffffff 46%);
    color: color-mix(in srgb, var(--body-text, #0f172a) 74%, #ffffff 26%);
    font-size: 0.88rem;
    font-weight: 600;
}

.multitienda-shell__stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.multitienda-shell__stat {
    min-height: 122px;
    padding: 18px;
    border-radius: 22px;
    background: color-mix(in srgb, var(--content-bg, #ffffff) 92%, #f0f9ff 8%);
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 52%, #ffffff 48%);
    display: grid;
    gap: 8px;
}

.multitienda-shell__stat-label {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: color-mix(in srgb, var(--body-text, #0f172a) 58%, #ffffff 42%);
}

.multitienda-shell__stat-value {
    font-size: clamp(1.5rem, 2vw, 2rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--body-text, #0f172a);
}

.multitienda-shell__stat-note {
    font-size: 0.86rem;
    color: color-mix(in srgb, var(--body-text, #0f172a) 64%, #ffffff 36%);
}

.multitienda-shell__body {
    min-width: 0;
    border-radius: 28px;
    background: color-mix(in srgb, var(--content-bg, #ffffff) 98%, #eef2ff 2%);
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 58%, #ffffff 42%);
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
    padding: 24px;
}

.multitienda-shell__panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}

.multitienda-shell__panel-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.multitienda-shell__toggle {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 40px;
    padding: 0 14px;
    border-radius: 999px;
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 58%, #ffffff 42%);
    background: color-mix(in srgb, var(--content-bg, #ffffff) 90%, #f8fafc 10%);
    color: var(--body-text, #0f172a);
    font-size: 0.84rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}

.multitienda-shell__toggle:hover {
    background: color-mix(in srgb, var(--content-bg, #ffffff) 80%, #e2e8f0 20%);
    transform: translateY(-1px);
}

.multitienda-shell__panel-title {
    display: grid;
    gap: 4px;
}

.multitienda-shell__panel-title h2 {
    margin: 0;
    font-size: 1.18rem;
    color: var(--body-text, #0f172a);
}

.multitienda-shell__panel-title p {
    margin: 0;
    font-size: 0.9rem;
    color: color-mix(in srgb, var(--body-text, #0f172a) 66%, #ffffff 34%);
}

.multitienda-shell__module-body {
    min-width: 0;
}

.multitienda-official-view .page {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 16px !important;
}

.multitienda-official-view .title,
.multitienda-official-view .subtitle {
    text-align: left;
}

.multitienda-official-view .section {
    overflow: hidden;
}

.multitienda-official-view .notebook {
    background: var(--content-bg, #ffffff);
    border: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 64%, #ffffff 36%);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 12px 26px color-mix(in srgb, var(--sidebar-bottom, #0f172a) 8%, transparent);
}

.multitienda-official-view .notebook-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    border-bottom: 1px solid color-mix(in srgb, var(--field-border, #cbd5e1) 56%, #ffffff 44%);
    background: color-mix(in srgb, var(--content-bg, #ffffff) 88%, var(--page-bg, #f4f6fb) 12%);
}

.multitienda-official-view .notebook-tab {
    padding: 12px 22px;
    font-size: 0.9rem;
    font-weight: 600;
    color: color-mix(in srgb, var(--body-text, #0f172a) 72%, #ffffff 28%);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}

.multitienda-official-view .notebook-tab:hover {
    color: var(--body-text, #0f172a);
}

.multitienda-official-view .notebook-tab.active {
    color: var(--button-bg, #0f172a);
    border-bottom-color: var(--button-bg, #0f172a);
    background: var(--content-bg, #ffffff);
}

.multitienda-official-view .notebook-panel {
    padding: 24px;
}

.multitienda-official-view .notebook-panel[hidden] {
    display: none !important;
}

.multitienda-official-view .notebook-panel .section {
    margin-bottom: 0;
}

.multitienda-official-view .section-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1.35fr) minmax(280px, 360px) !important;
    gap: 24px !important;
    align-items: start !important;
}

.multitienda-official-view .field-input,
.multitienda-official-view .field-select,
.multitienda-official-view .avan-input,
.multitienda-official-view input,
.multitienda-official-view select,
.multitienda-official-view textarea {
    max-width: 100%;
    width: 100%;
    min-height: 42px;
    border-radius: 12px;
    border: 1px solid var(--field-border, #cbd5e1);
    background: var(--field-color, #ffffff);
    color: var(--field-text, #0f172a);
    box-shadow: none;
    transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.multitienda-official-view textarea {
    min-height: 110px;
    padding: 12px 14px;
    resize: vertical;
}

.multitienda-official-view input:not([type="checkbox"]):not([type="radio"]):not([type="color"]):not([type="file"]),
.multitienda-official-view select {
    padding: 0 14px;
}

.multitienda-official-view .field-input:focus,
.multitienda-official-view .field-select:focus,
.multitienda-official-view .avan-input:focus,
.multitienda-official-view input:focus,
.multitienda-official-view select:focus,
.multitienda-official-view textarea:focus {
    outline: 0;
    border-color: var(--field-focus, var(--button-bg, #0f172a));
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--field-focus, #0f172a) 16%, transparent);
}

.multitienda-official-view input::placeholder,
.multitienda-official-view textarea::placeholder {
    color: color-mix(in srgb, var(--field-text, #0f172a) 48%, #ffffff 52%);
}

.multitienda-official-view input[type="checkbox"],
.multitienda-official-view input[type="radio"] {
    accent-color: var(--button-bg, #0f172a);
}

.multitienda-official-view .section,
.multitienda-official-view .section-card,
.multitienda-official-view .logo-box,
.multitienda-official-view .photo-box,
.multitienda-official-view table {
    color: var(--body-text, #0f172a);
}

.multitienda-official-view table {
    background: var(--content-bg, #ffffff);
}

.multitienda-official-view th,
.multitienda-official-view td {
    border-color: color-mix(in srgb, var(--field-border, #cbd5e1) 58%, #ffffff 42%);
}

.multitienda-official-view .photo-box,
.multitienda-official-view .logo-box {
    background: color-mix(in srgb, var(--field-color, #ffffff) 92%, var(--page-bg, #f4f6fb) 8%);
    border: 1px dashed color-mix(in srgb, var(--field-border, #cbd5e1) 76%, #ffffff 24%);
}

.multitienda-official-view .logo-box,
.multitienda-official-view .photo-box {
    max-width: 100%;
}

@media (max-width: 1180px) {
    .multitienda-shell {
        grid-template-columns: 1fr;
    }

    .multitienda-shell__sidebar {
        position: static;
    }

    .multitienda-shell__hero-grid {
        grid-template-columns: 1fr;
    }

    .multitienda-official-view .section-grid {
        grid-template-columns: 1fr !important;
    }
}

@media (max-width: 760px) {
    html.ui-sidebar-modern .main-content {
        padding-right: 12px !important;
    }

    .multitienda-shell__sidebar,
    .multitienda-shell__hero,
    .multitienda-shell__body {
        border-radius: 22px;
    }

    .multitienda-shell__hero,
    .multitienda-shell__body {
        padding: 18px;
    }

    .multitienda-shell__stats {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def _resolve_store_permissions(db, scope: dict) -> dict:
    """Returns store-level feature flags extracted from store_theme."""
    try:
        if scope.get("store_id"):
            row = db.execute(
                text("SELECT store_theme FROM vendors WHERE id = :id LIMIT 1"),
                {"id": int(scope["store_id"])},
            ).mappings().first()
        elif scope.get("user_id"):
            row = db.execute(
                text("SELECT store_theme FROM vendors WHERE vendor_id = :uid LIMIT 1"),
                {"uid": int(scope["user_id"])},
            ).mappings().first()
        else:
            return {}
        return _decode_store_theme(row["store_theme"]) if row else {}
    except Exception:
        return {}


def _visible_module_sections(role_name: str | None, store_permissions: dict | None = None) -> list[dict[str, str]]:
    normalized_role = normalize_role_name(role_name)
    is_superadmin = normalized_role in {"superadministrador", "superadmin"}
    perms = store_permissions or {}
    sections = []
    for section in _MODULE_SECTIONS:
        if section["id"] == "gestion" and not is_superadmin:
            continue
        if section["id"] == "videos" and not is_superadmin and not perms.get("can_upload_videos"):
            continue
        if section["id"] == "referidos" and not is_superadmin and not perms.get("referrals"):
            continue
        if section["id"] == "reservaciones" and not is_superadmin and not perms.get("appointments"):
            continue
        if section["id"] == "cupones" and not is_superadmin and not perms.get("coupons"):
            continue
        if section["id"] == "whatsapp" and not is_superadmin and not perms.get("whatsapp"):
            continue
        if section["id"] == "empleados" and not is_superadmin and int(perms.get("max_internal_users") or 0) <= 0:
            continue
        if section["id"] == "seguidores" and not is_superadmin and int(perms.get("max_portal_users") or 0) <= 0:
            continue
        if section["id"] == "proveedores" and not is_superadmin and not perms.get("can_use_providers"):
            continue
        if section["id"] == "ia" and not is_superadmin and not perms.get("can_use_ai"):
            continue
        if section["id"] == "institucion_financiera" and not is_superadmin and not perms.get("can_use_financial"):
            continue
        if section["id"] == "apartados" and not is_superadmin and not perms.get("can_use_layaway"):
            continue
        if section["id"] == "subastas" and not is_superadmin and not perms.get("can_use_auctions"):
            continue
        sections.append(section)
    return sections


def _can_access_module_section(role_name: str | None, section_id: str, store_permissions: dict | None = None) -> bool:
    return any(section["id"] == section_id for section in _visible_module_sections(role_name, store_permissions))


def _build_module_sidebar_markup(sections: list[dict[str, str]], current_section: str) -> str:
    nav_items = []
    for section in sections:
        is_active = section["id"] == current_section
        nav_items.append(
            '<a class="multitienda-shell__nav-link{active}" href="{route}">'
            '<span class="multitienda-shell__nav-icon"><i class="{icon}" aria-hidden="true"></i></span>'
            '<span class="multitienda-shell__nav-copy"><strong>{label}</strong><span>{hint}</span></span>'
            "</a>".format(
                active=" is-active" if is_active else "",
                route=escape(section["route"]),
                icon=escape(section["icon"]),
                label=escape(section["label"]),
                hint=escape(
                    "Tablero y resumen del marketplace"
                    if section["id"] == "inicio"
                    else (
                        "Sube y gestiona videos de tu tienda"
                        if section["id"] == "videos"
                        else (
                            "Gestión del programa de referidos"
                            if section["id"] == "referidos"
                            else (
                                "Agenda y control de reservaciones"
                                if section["id"] == "reservaciones"
                                else (
                                    "Códigos de descuento y promociones"
                                    if section["id"] == "cupones"
                                    else (
                                        "Mensajería y campañas WhatsApp"
                                        if section["id"] == "whatsapp"
                                        else (
                                            "Equipo interno de la tienda"
                                            if section["id"] == "empleados"
                                            else (
                                                "Clientes y socios de la tienda"
                                                if section["id"] == "seguidores"
                                                else (
                                                    "Red de contactos y campañas"
                                                    if section["id"] == "proveedores"
                                                    else (
                                                        "Asistentes de IA para tu negocio"
                                                        if section["id"] == "ia"
                                                        else (
                                                            "Comisiones y créditos colocados"
                                                            if section["id"] == "institucion_financiera"
                                                            else (
                                                                "Reserva de productos con abonos"
                                                                if section["id"] == "apartados"
                                                                else (
                                                                    "Pujas y adjudicación en tiempo real"
                                                                    if section["id"] == "subastas"
                                                                    else (
                                                                        "Panel principal del módulo"
                                                                        if section["id"] == "configuracion"
                                                                        else ("Catálogo y ficha de producto" if section["id"] == "productos" else "Alta y control de tiendas")
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ),
            )
        )
    return (
        '<aside class="multitienda-shell__sidebar">'
        '<div class="multitienda-shell__brand">'
        '<div class="multitienda-shell__brand-mark"><i class="fa-solid fa-store" aria-hidden="true"></i></div>'
        '<div class="multitienda-shell__brand-copy"><strong>Multitienda</strong><span>Operación del marketplace</span></div>'
        "</div>"
        '<div class="multitienda-shell__nav">'
        '<p class="multitienda-shell__nav-label">Navegación</p>'
        + "".join(nav_items)
        + "</div>"
        "</aside>"
    )


def _build_marketplace_workspace_script() -> str:
    return """
<script>
(function () {
    var root = document.querySelector('.multitienda-shell');
    if (!root) return;
    var heroSection = root.querySelector('.multitienda-shell__hero');
    var heroToggleBtn = root.querySelector('[data-multitienda-hero-toggle="1"]');
    var storesCountEl = root.querySelector('[data-multitienda-stat="stores"]');
    var productsCountEl = root.querySelector('[data-multitienda-stat="products"]');
    var membershipEl = root.querySelector('[data-multitienda-stat="membership"]');
    var inventoryEl = root.querySelector('[data-multitienda-stat="inventory"]');
    var storeNameEls = root.querySelectorAll('[data-multitienda-store-name]');
    var storeSubtitleEls = root.querySelectorAll('[data-multitienda-store-subtitle]');
    var accessMomentEl = root.querySelector('[data-multitienda-access-moment]');

    function setText(nodeList, value) {
        (nodeList || []).forEach(function (node) { node.textContent = value; });
    }

    function applyHeroVisibility(hidden) {
        if (!heroSection || !heroToggleBtn) return;
        heroSection.hidden = !!hidden;
        heroToggleBtn.setAttribute('aria-expanded', hidden ? 'false' : 'true');
        heroToggleBtn.innerHTML = hidden
            ? '<i class="fa-solid fa-eye" aria-hidden="true"></i><span>Mostrar resumen</span>'
            : '<i class="fa-solid fa-eye-slash" aria-hidden="true"></i><span>Ocultar resumen</span>';
    }

    function countLocalProducts() {
        try {
            var raw = window.localStorage.getItem('multitienda_productos');
            var parsed = JSON.parse(raw || '[]');
            return Array.isArray(parsed) ? parsed.length : 0;
        } catch (error) {
            return 0;
        }
    }

    if (productsCountEl) {
        productsCountEl.textContent = String(countLocalProducts());
    }

    try {
        applyHeroVisibility(window.localStorage.getItem('multitienda_hero_hidden') === '1');
    } catch (error) {
        applyHeroVisibility(false);
    }

    if (heroToggleBtn) {
        heroToggleBtn.addEventListener('click', function () {
            var nextHidden = !(heroSection && heroSection.hidden);
            applyHeroVisibility(nextHidden);
            try {
                window.localStorage.setItem('multitienda_hero_hidden', nextHidden ? '1' : '0');
            } catch (error) {}
        });
    }

    if (accessMomentEl) {
        try {
            accessMomentEl.textContent = new Intl.DateTimeFormat('es-MX', {
                dateStyle: 'medium',
                timeStyle: 'short'
            }).format(new Date());
        } catch (error) {
            accessMomentEl.textContent = new Date().toLocaleString();
        }
    }

    fetch('/multitienda/api/stores', { headers: { Accept: 'application/json' } })
        .then(function (response) { return response.ok ? response.json() : null; })
        .then(function (payload) {
            var stores = payload && Array.isArray(payload.data) ? payload.data : [];
            if (storesCountEl) storesCountEl.textContent = String(stores.length);
            if (!stores.length) {
                setText(storeNameEls, 'Sin tienda asignada');
                setText(storeSubtitleEls, 'Asigna una tienda para activar la operación del marketplace.');
                if (membershipEl) membershipEl.textContent = 'Sin membresía';
                if (inventoryEl) inventoryEl.textContent = 'Pendiente';
                return;
            }
            var store = stores[0] || {};
            setText(storeNameEls, String(store.name || 'Mi tienda'));
            setText(
                storeSubtitleEls,
                store.slug
                    ? 'Slug público: ' + String(store.slug)
                    : 'Configura la identidad comercial y la operación de tu tienda.'
            );
            if (membershipEl) membershipEl.textContent = String(store.membership || 'Sin membresía');
            if (inventoryEl) inventoryEl.textContent = store.inventoryEnabled ? 'Activo' : 'Desactivado';
        })
        .catch(function () {
            if (storesCountEl) storesCountEl.textContent = '0';
        });
})();
</script>
"""


def _build_marketplace_shell_content(
    document_html: str,
    section_id: str,
    *,
    sections: list[dict[str, str]],
    viewer_name: str,
) -> str:
    prefixed = _prefix_root_relative_urls(document_html, "/multitienda")
    styles = "\n".join(match.group(0) for match in _STYLE_RE.finditer(prefixed))
    main_match = _MAIN_RE.search(prefixed)
    main_markup = main_match.group(1).strip() if main_match else prefixed
    section_meta = next((item for item in sections if item["id"] == section_id), None)
    section_label = section_meta["label"] if section_meta else "Multitienda"
    show_hero = section_id == "inicio"

    filtered_scripts: list[str] = []
    for match in _SCRIPT_RE.finditer(prefixed):
        script_markup = match.group(1)
        if "/static/js/backend-navbar.js" in script_markup:
            continue
        if "/static/js/backend-sidebar-core.js" in script_markup:
            continue
        filtered_scripts.append(script_markup)

    hero_markup = ""
    panel_actions_markup = ""
    if show_hero:
        hero_markup = (
            '<section class="multitienda-shell__hero">'
            + '<div class="multitienda-shell__hero-grid">'
            + '<div class="multitienda-shell__hero-copy">'
            + '<span class="multitienda-shell__eyebrow"><i class="fa-solid fa-chart-line" aria-hidden="true"></i> Dashboard de tienda</span>'
            + '<h1><span data-multitienda-store-name>Mi tienda</span></h1>'
            + '<p>Administra productos, identidad comercial y configuración operativa desde una sola vista. La navegación lateral reemplaza el submenú superior para mantener el módulo autónomo.</p>'
            + '<div class="multitienda-shell__hero-meta">'
            + '<span class="multitienda-shell__meta-pill"><i class="fa-regular fa-user" aria-hidden="true"></i> '
            + escape(viewer_name or "Usuario")
            + "</span>"
            + '<span class="multitienda-shell__meta-pill"><i class="fa-regular fa-clock" aria-hidden="true"></i> <span data-multitienda-access-moment>Ahora</span></span>'
            + '<span class="multitienda-shell__meta-pill"><i class="fa-solid fa-layer-group" aria-hidden="true"></i> '
            + escape(section_label)
            + "</span>"
            + "</div>"
            + '<p data-multitienda-store-subtitle>Configura la identidad comercial y la operación de tu tienda.</p>'
            + "</div>"
            + '<div class="multitienda-shell__stats">'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Tiendas visibles</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="stores">0</strong><span class="multitienda-shell__stat-note">Alcance del usuario actual.</span></article>'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Productos locales</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="products">0</strong><span class="multitienda-shell__stat-note">Catálogo del módulo en este navegador.</span></article>'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Membresía</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="membership">Sin membresía</strong><span class="multitienda-shell__stat-note">Configuración comercial cargada desde la tienda.</span></article>'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Inventario</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="inventory">Pendiente</strong><span class="multitienda-shell__stat-note">Estado de la operación interna.</span></article>'
            + "</div>"
            + "</div>"
            + "</section>"
        )
        panel_actions_markup = (
            '<div class="multitienda-shell__panel-actions">'
            + '<button type="button" class="multitienda-shell__toggle" data-multitienda-hero-toggle="1" aria-expanded="true">'
            + '<i class="fa-solid fa-eye-slash" aria-hidden="true"></i><span>Ocultar resumen</span>'
            + "</button>"
            + "</div>"
        )

    return (
        '<div class="multitienda-official-view">'
        + _MODULE_NAVBAR_BOOTSTRAP
        + _MODULE_LAYOUT_OVERRIDES
        + styles
        + '<section class="multitienda-shell">'
        + _build_module_sidebar_markup(sections, section_id)
        + '<div class="multitienda-shell__content">'
        + hero_markup
        + '<section class="multitienda-shell__body">'
        + '<div class="multitienda-shell__panel-head">'
        + '<div class="multitienda-shell__panel-title"><h2>'
        + escape(section_label)
        + '</h2><p>Vista operativa del módulo con navegación propia y alcance por rol.</p></div>'
        + panel_actions_markup
        + "</div>"
        + '<div class="multitienda-shell__module-body"><main class="page">'
        + main_markup
        + "</main></div>"
        + "</section>"
        + "</div>"
        + "</section>"
        + "".join(filtered_scripts)
        + _build_marketplace_workspace_script()
        + "</div>"
    )


def _cached_management_shell_content() -> str:
    return _build_marketplace_shell_content(
        gestion_html(),
        "gestion",
        sections=list(_MODULE_SECTIONS),
        viewer_name="Demo",
    )


def _render_official_shell(
    request: Request,
    section_id: str,
    document_html: str,
) -> HTMLResponse:
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role = str(scope.get("role") or getattr(request.state, "user_role", ""))
    visible_sections = _visible_module_sections(role, store_perms)
    context = build_backend_context(
        request,
        title="Multitienda",
        subtitle="Marketplace integrado al backend de SIPET.",
        description="Marketplace multitienda con navegación oficial de SIPET.",
        content=_build_marketplace_shell_content(
            document_html,
            section_id,
            sections=visible_sections,
            viewer_name=_current_username(request),
        ),
        hide_floating_actions=True,
        show_page_header=False,
        page_title="Multitienda",
        page_description="Marketplace en SIPET",
        section_title="Multitienda",
        section_label="Marketplace",
        module_name="Multitienda",
        module_description="Marketplace en SIPET",
        module_icon="fa-solid fa-store",
        current_module="multitienda",
        current_section=section_id,
        module_sections=visible_sections,
    )
    return get_templates(request).TemplateResponse(BACKEND_BASE_TEMPLATE, context)


def _render_public_document(document_html: str) -> HTMLResponse:
    return HTMLResponse(content=_prefix_root_relative_urls(document_html, "/multitienda"))


def _db_session_for_request(request: Request):
    return core_db.get_session_factory_for_host(core_db.get_request_host())()


def _current_username(request: Request) -> str:
    return str(
        getattr(request.state, "user_name", None)
        or getattr(request.state, "username", None)
        or request.cookies.get("user_name")
        or request.cookies.get("username")
        or request.cookies.get("usuario")
        or ""
    ).strip()


def _current_user_record(request: Request, db):
    username = _current_username(request)
    if not username:
        return None
    normalized_username = username.lower()
    roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
    for user in db.query(Usuario).all():
        decrypted_username = (decrypt_sensitive(user.usuario) or "").strip().lower()
        decrypted_email = (decrypt_sensitive(user.correo) or "").strip().lower()
        if normalized_username not in {decrypted_username, decrypted_email}:
            continue
        role_name = roles_by_id.get(user.rol_id) or normalize_role_name(getattr(user, "role", "") or "usuario")
        return user, role_name
    return None


def _resolve_store_scope(request: Request, db) -> dict[str, object]:
    resolved = _current_user_record(request, db)
    if not resolved:
        return {"role": "usuario", "user_id": None, "store_id": None, "store_slug": "", "restricted": False}
    user, role_name = resolved
    restricted = role_name in {"administrador_tienda", "vendedor_tienda"}
    store_id = None
    store_slug = ""
    if restricted:
        store_row = db.execute(
            text(
                """
                SELECT id, store_slug
                FROM vendors
                WHERE vendor_id = :vendor_id
                LIMIT 1
                """
            ),
            {"vendor_id": int(user.id)},
        ).mappings().first()
        store_id = int(store_row["id"]) if store_row and store_row.get("id") is not None else None
        store_slug = str(store_row.get("store_slug") or "") if store_row else ""
    return {
        "role": role_name,
        "user_id": int(user.id),
        "store_id": store_id,
        "store_slug": store_slug,
        "restricted": restricted,
    }


def _ensure_vendor_table() -> None:
    db = SessionLocal()
    try:
        dialect_name = db.bind.dialect.name
        now_sql = "CURRENT_TIMESTAMP"
        bool_type = "BOOLEAN"
        text_type = "TEXT"
        id_type = "INTEGER PRIMARY KEY"
        if dialect_name == "postgresql":
            bool_type = "BOOLEAN"
            text_type = "JSONB"
            id_type = "INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY"
        db.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS vendors (
                    id {id_type},
                    vendor_id INTEGER UNIQUE,
                    store_name VARCHAR(100) NOT NULL,
                    store_slug VARCHAR(255) NOT NULL UNIQUE,
                    description VARCHAR(255) DEFAULT '',
                    logo VARCHAR(255),
                    banner VARCHAR(255),
                    phone VARCHAR(20),
                    address VARCHAR(255),
                    country VARCHAR(100),
                    store_theme {text_type},
                    commission_rate NUMERIC(5, 2) DEFAULT 10.00,
                    is_featured {bool_type} DEFAULT FALSE,
                    status VARCHAR(32) DEFAULT 'pending',
                    rating NUMERIC(3, 2) DEFAULT 0.00,
                    total_sales NUMERIC(12, 2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT {now_sql},
                    updated_at TIMESTAMP DEFAULT {now_sql},
                    is_active {bool_type} DEFAULT TRUE
                )
                """
            )
        )
        if dialect_name == "postgresql":
            column_info = db.execute(
                text(
                    """
                    SELECT column_default, is_identity
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'vendors'
                      AND column_name = 'id'
                    """
                )
            ).mappings().first()
            has_identity = bool(column_info and str(column_info.get("is_identity") or "").upper() == "YES")
            has_default = bool(column_info and column_info.get("column_default"))
            if not has_identity and not has_default:
                try:
                    db.execute(text("ALTER TABLE vendors ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY"))
                except Exception:
                    db.execute(text("CREATE SEQUENCE IF NOT EXISTS vendors_id_seq"))
                    db.execute(text("ALTER SEQUENCE vendors_id_seq OWNED BY vendors.id"))
                    db.execute(text("ALTER TABLE vendors ALTER COLUMN id SET DEFAULT nextval('vendors_id_seq')"))
                    db.execute(
                        text(
                            """
                            SELECT setval(
                                'vendors_id_seq',
                                GREATEST(COALESCE((SELECT MAX(id) FROM vendors), 0) + 1, 1),
                                false
                            )
                            """
                        )
                    )
        db.commit()
    finally:
        db.close()


def _decode_store_theme(raw_value) -> dict:
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


@router.get("/multitienda/api/business-types", response_class=JSONResponse)
def multitienda_business_types_proxy():
    return list_business_types()


@router.post("/multitienda/api/business-types", response_class=JSONResponse)
async def multitienda_create_business_type_proxy(request: Request):
    return await create_business_type(request)


@router.get("/multitienda/api/store-admin-users", response_class=JSONResponse)
def multitienda_store_admin_users(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
        rows = []
        for user in db.query(Usuario).order_by(Usuario.full_name.asc()).all():
            role_name = roles_by_id.get(user.rol_id) or normalize_role_name(getattr(user, "role", "") or "usuario")
            if role_name != "administrador_tienda":
                continue
            if scope["restricted"] and int(user.id) != int(scope["user_id"] or 0):
                continue
            rows.append(
                {
                    "id": user.id,
                    "usuario": (decrypt_sensitive(user.usuario) or "").strip(),
                    "nombre": (user.full_name or "").strip(),
                    "rol": role_name,
                }
            )
        return {"success": True, "data": rows}
    finally:
        db.close()


@router.get("/multitienda/api/memberships", response_class=JSONResponse)
def multitienda_memberships():
    _ensure_membresia_table()
    db = SessionLocal()
    try:
        _seed_membresias(db)
        memberships = db.query(Membresia).order_by(Membresia.id.asc()).all()
        return {
            "success": True,
            "data": [
                {
                    "id": item.id,
                    "nombre": item.nombre or "",
                    "tipo": item.tipo or "",
                    "descripcion": item.descripcion or "",
                }
                for item in memberships
            ],
        }
    finally:
        db.close()


@router.get("/multitienda/api/stores", response_class=JSONResponse)
def multitienda_list_stores(request: Request):
    _ensure_vendor_table()
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        where_clause = ""
        params: dict[str, object] = {}
        if scope["restricted"]:
            if not scope["user_id"]:
                return {"success": True, "data": []}
            where_clause = "WHERE v.vendor_id = :vendor_id"
            params["vendor_id"] = int(scope["user_id"])
        rows = db.execute(
            text(
                """
                SELECT
                    v.id,
                    v.vendor_id,
                    v.store_name,
                    v.store_slug,
                    v.store_theme,
                    v.is_featured,
                    v.is_active,
                    u.full_name,
                    u.username AS encrypted_username
                FROM vendors v
                LEFT JOIN users u ON u.id = v.vendor_id
                """
                + where_clause
                + """
                ORDER BY lower(v.store_name) ASC, v.id ASC
                """
            ),
            params,
        ).mappings().all()
        data = []
        for row in rows:
            theme = _decode_store_theme(row["store_theme"])
            data.append(
                {
                    "id": row["id"],
                    "name": row["store_name"] or "",
                    "slug": row["store_slug"] or "",
                    "adminId": str(row["vendor_id"] or ""),
                    "adminLabel": (
                        (row["full_name"] or "").strip()
                        or (decrypt_sensitive(row["encrypted_username"]) or "").strip()
                    ),
                    "typeCode": str(theme.get("store_type") or ""),
                    "typeLabel": str(theme.get("store_type") or ""),
                    "membership": str(theme.get("membership") or ""),
                    "isActive": bool(row["is_active"]),
                    "isFeatured": bool(row["is_featured"]),
                    "inventoryEnabled": bool(theme.get("inventory_enabled", False)),
                    "canUploadVideos": bool(theme.get("can_upload_videos", False)),
                    "validity": str(theme.get("validity") or ""),
                    "referrals": str(theme.get("referrals") or ""),
                    "appointments": str(theme.get("appointments") or ""),
                    "coupons": str(theme.get("coupons") or ""),
                    "whatsapp": str(theme.get("whatsapp") or ""),
                    "maxInternalUsers": int(theme.get("max_internal_users") or 0),
                    "maxPortalUsers": int(theme.get("max_portal_users") or 0),
                }
            )
        return {"success": True, "data": data}
    finally:
        db.close()


@router.post("/multitienda/api/stores", response_class=JSONResponse)
async def multitienda_save_store(request: Request):
    _ensure_vendor_table()
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
    finally:
        db.close()
    try:
        if not scope["restricted"]:
            return await save_store_settings(request)

        if not scope["store_id"] or not scope["user_id"]:
            raise HTTPException(status_code=403, detail="El usuario no tiene una tienda asignada.")

        payload = await request.json()
        payload["is_edit"] = True
        payload["store_id"] = int(scope["store_id"])
        payload["admin_user_id"] = int(scope["user_id"])
        return await save_store_settings(request, payload_override=payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar la tienda: {exc}") from exc


@router.get("/multitienda/inicio", include_in_schema=False, response_class=HTMLResponse)
def multitienda_inicio_entrypoint(request: Request):
    return _render_official_shell(request, "inicio", inicio_html())


@router.get("/multitienda", include_in_schema=False, response_class=HTMLResponse)
def multitienda_entrypoint(request: Request):
    return _render_official_shell(request, "inicio", inicio_html())


@router.get("/multitienda/", include_in_schema=False, response_class=HTMLResponse)
def multitienda_entrypoint_slash(request: Request):
    return _render_official_shell(request, "inicio", inicio_html())


@router.get("/multitienda/videos", include_in_schema=False, response_class=HTMLResponse)
def multitienda_videos_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "videos", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "videos", videos_html())


@router.get("/multitienda/referidos", include_in_schema=False, response_class=HTMLResponse)
def multitienda_referidos_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "referidos", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    store_slug = str(scope.get("store_slug") or "").strip()
    target = "/referidos"
    if store_slug:
        target = f"/referidos?business_slug={store_slug}"
    return RedirectResponse(url=target, status_code=307)


@router.get("/multitienda/reservaciones", include_in_schema=False, response_class=HTMLResponse)
def multitienda_reservaciones_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "reservaciones", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "reservaciones", reservaciones_html())


@router.get("/multitienda/cupones", include_in_schema=False, response_class=HTMLResponse)
def multitienda_cupones_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "cupones", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "cupones", cupones_html())


@router.get("/multitienda/whatsapp", include_in_schema=False, response_class=HTMLResponse)
def multitienda_whatsapp_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "whatsapp", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "whatsapp", whatsapp_html())


@router.get("/multitienda/empleados", include_in_schema=False, response_class=HTMLResponse)
def multitienda_empleados_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "empleados", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    max_users = int(store_perms.get("max_internal_users") or 0)
    return _render_official_shell(request, "empleados", empleados_html(max_users=max_users))


@router.get("/multitienda/seguidores", include_in_schema=False, response_class=HTMLResponse)
def multitienda_seguidores_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "seguidores", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    max_users = int(store_perms.get("max_portal_users") or 0)
    return _render_official_shell(request, "seguidores", seguidores_html(max_users=max_users))


@router.get("/multitienda/proveedores", include_in_schema=False, response_class=HTMLResponse)
def multitienda_proveedores_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "proveedores", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "proveedores", proveedores_html())


@router.get("/multitienda/ia", include_in_schema=False, response_class=HTMLResponse)
def multitienda_ia_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "ia", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "ia", ia_html())


@router.get("/multitienda/institucion_financiera", include_in_schema=False, response_class=HTMLResponse)
def multitienda_institucion_financiera_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "institucion_financiera", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "institucion_financiera", institucion_financiera_html())


@router.get("/multitienda/apartados", include_in_schema=False, response_class=HTMLResponse)
def multitienda_apartados_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "apartados", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "apartados", apartados_html())


@router.get("/multitienda/subastas", include_in_schema=False, response_class=HTMLResponse)
def multitienda_subastas_entrypoint(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        store_perms = _resolve_store_permissions(db, scope)
    finally:
        db.close()
    role_name = str(scope.get("role") or getattr(request.state, "user_role", ""))
    if not _can_access_module_section(role_name, "subastas", store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    return _render_official_shell(request, "subastas", subastas_html())


@router.get("/multitienda/administracion_tiendas", include_in_schema=False, response_class=HTMLResponse)
def multitienda_gestion_entrypoint(request: Request):
    role_name = str(getattr(request.state, "user_role", "") or "").strip()
    if not _can_access_module_section(role_name, "gestion"):
        return RedirectResponse(url="/multitienda/configuracion", status_code=307)
    return _render_official_shell(request, "gestion", gestion_html())


@router.get("/multitienda/configuracion", include_in_schema=False, response_class=HTMLResponse)
def multitienda_config_entrypoint(request: Request):
    return _render_official_shell(request, "configuracion", configuracion_html())


@router.get("/configuracion", include_in_schema=False)
@router.get("/configuracion/", include_in_schema=False)
def multitienda_config_legacy_redirect():
    return RedirectResponse(url="/multitienda/configuracion", status_code=307)


@router.get("/multitienda/productos", include_in_schema=False, response_class=HTMLResponse)
def multitienda_productos_entrypoint(request: Request):
    return _render_official_shell(request, "productos", productos_html())


@router.get("/multitienda/tienda", include_in_schema=False, response_class=HTMLResponse)
def multitienda_tienda_entrypoint(request: Request):
    return _render_official_shell(request, "tienda", tienda_html())


@router.get("/multitienda/tiendas", include_in_schema=False, response_class=HTMLResponse)
def multitienda_tiendas_entrypoint(request: Request):
    return _render_official_shell(request, "tienda", tienda_html())


@router.get("/tiendas", include_in_schema=False, response_class=HTMLResponse)
def public_tiendas_entrypoint():
    return _render_public_document(tienda_html())


@router.get("/tiendas/", include_in_schema=False, response_class=HTMLResponse)
def public_tiendas_entrypoint_slash():
    return _render_public_document(tienda_html())


@router.get("/multitienda/public/tiendas", include_in_schema=False, response_class=HTMLResponse)
def public_multitienda_tiendas_entrypoint():
    return _render_public_document(tienda_html())


router.mount("/multitienda", marketplace_app)

__all__ = ["router"]
