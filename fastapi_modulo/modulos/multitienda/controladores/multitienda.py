from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from html import escape
from pathlib import Path
import hashlib
import json
import logging
import re
_log = logging.getLogger("multitienda.config")

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import bindparam, text

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.module_registry import is_module_enabled, list_modules_payload
from fastapi_modulo.modulos.multitienda.__manifest__ import MANIFEST
from fastapi_modulo.modulos.multitienda.controladores.marketplace_backend import (
    build_marketplace_backend_app,
    SessionLocal,
    bootstrap_business_types_schema,
    create_business_type,
    list_business_types,
    save_store_settings,
)
from fastapi_modulo.modulos.multitienda.controladores.routers.admin_api import create_admin_api_router
from fastapi_modulo.modulos.multitienda.controladores.routers.multitienda_employees import create_employees_router
from fastapi_modulo.modulos.multitienda.controladores.routers.multitienda_pages import create_pages_router
from fastapi_modulo.modulos.multitienda.controladores.routers.multitienda_products import create_products_router
from fastapi_modulo.modulos.multitienda.controladores.routers.multitienda_public import create_public_router
from fastapi_modulo.modulos.multitienda.controladores.routers.multitienda_store_admin import create_store_admin_router
from fastapi_modulo.modulos.multitienda.controladores.services.scope_service import (
    coerce_theme_bool as _coerce_theme_bool,
    current_user_record as _current_user_record_impl,
    resolve_store_permissions as _resolve_store_permissions_impl,
    resolve_store_scope as _resolve_store_scope_impl,
)
from fastapi_modulo.modulos.multitienda.controladores.services.roles_service import get_roles_map
from fastapi_modulo.modulos.multitienda.controladores.services.section_service import (
    can_access_module_section as _can_access_module_section_impl,
    can_access_store_config as _can_access_store_config_impl,
    get_optional_section_integration as _get_optional_section_integration_impl,
    optional_section_available as _optional_section_available_impl,
    resolve_integrated_module_context as _resolve_integrated_module_context_impl,
    resolve_integrated_section_target as _resolve_integrated_section_target_impl,
    resolve_enabled_module_route as _resolve_enabled_module_route_impl,
    visible_module_sections as _visible_module_sections_impl,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics import service as analytics_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import service as employee_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import service as layaway_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products import service as product_service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import bootstrap_user_support_tables
from fastapi_modulo.modulos.multitienda.servicios.access_roles import ensure_multitienda_access_roles
from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import ensure_store_tables
from fastapi_modulo.modulos.multitienda.servicios.theme_utils import decode_theme as _decode_store_theme
from fastapi_modulo.modulos.multitienda.vistas.utils import _prefix_root_relative_urls
from fastapi_modulo.modulos.multitienda.vistas.configuracion import configuracion_html
from fastapi_modulo.modulos.multitienda.vistas.gestion import gestion_html
from fastapi_modulo.modulos.multitienda.vistas.inicio import inicio_html
from fastapi_modulo.modulos.multitienda.vistas.productos import productos_html
from fastapi_modulo.modulos.multitienda.vistas.tienda import tienda_html
from fastapi_modulo.modulos.multitienda.vistas.carrito import carrito_html
from fastapi_modulo.modulos.multitienda.vistas.cupones import cupones_html
from fastapi_modulo.modulos.multitienda.vistas.empleados import empleados_html
from fastapi_modulo.modulos.multitienda.vistas.seguidores import seguidores_html
from fastapi_modulo.modulos.multitienda.vistas.whatsapp import whatsapp_html
from fastapi_modulo.modulos.multitienda.vistas.videos import videos_html
from fastapi_modulo.modulos.multitienda.vistas.proveedores import proveedores_html
from fastapi_modulo.modulos.multitienda.vistas.ia import ia_html
from fastapi_modulo.modulos.multitienda.vistas.apartados import apartados_html
from fastapi_modulo.modulos.multitienda.vistas.fidelizacion import fidelizacion_html
from fastapi_modulo.modulos.multitienda.vistas.sidebar import build_sidebar_markup as render_sidebar_markup, load_sidebar_css
from fastapi_modulo.modulos.personalizacion.controladores.personalizar import resolve_logo_empresa_url
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.membresia import Membresia, _ensure_membresia_table, _seed_membresias
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol, Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import decrypt_sensitive, find_user_by_login
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import (
    build_backend_context,
    get_login_identity_context,
    resolve_sidebar_logo_url,
)
from fastapi_modulo.modulos_sipet.web.servicios.template_service import (
    BACKEND_BASE_TEMPLATE,
    get_templates,
    render_not_found_template,
)

router = APIRouter()
marketplace_app = build_marketplace_backend_app()


def bootstrap_multitienda() -> None:
    ensure_store_tables()
    _ensure_vendor_table()
    db = SessionLocal()
    try:
        _ensure_product_tables(db.bind)
        layaway_service.bootstrap_layaway_schema(db)
    finally:
        db.close()
    bootstrap_business_types_schema()
    _ensure_membresia_table()
    bootstrap_user_support_tables()
    ensure_multitienda_access_roles()

_STYLE_RE = re.compile(r"<style>(.*?)</style>", re.IGNORECASE | re.DOTALL)
_LINK_CSS_RE = re.compile(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*/?>', re.IGNORECASE)
_MAIN_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.IGNORECASE | re.DOTALL)
_SCRIPT_RE = re.compile(r"(<script\b.*?</script>)", re.IGNORECASE | re.DOTALL)
_OPTIONAL_SECTION_INTEGRATIONS = {
    str(item.get("section_id") or "").strip(): item
    for item in (MANIFEST.get("integration_points") or [])
    if str(item.get("section_id") or "").strip()
}

_MODULE_SECTIONS = [
    {"id": "inicio", "label": "Inicio", "icon": "fa-solid fa-house", "route": "/multitienda/inicio"},
    {"id": "videos", "label": "Videos", "icon": "fa-solid fa-video", "route": "/multitienda/videos"},
    {"id": "productos", "label": "Productos", "icon": "fa-solid fa-box", "route": "/multitienda/productos"},
    {"id": "referidos", "label": "Referidos", "icon": "fa-solid fa-user-group", "route": "/multitienda/referidos"},
    {"id": "notificaciones_pwa", "label": "Notificaciones PWA", "icon": "fa-solid fa-mobile-screen-button", "route": "/multitienda/notificaciones-pwa"},
    {"id": "reservaciones", "label": "Reservaciones", "icon": "fa-solid fa-calendar-check", "route": "/multitienda/reservaciones"},
    {"id": "cupones", "label": "Cupones", "icon": "fa-solid fa-ticket", "route": "/multitienda/cupones"},
    {"id": "fidelizacion", "label": "Fidelización", "icon": "fa-solid fa-star", "route": "/multitienda/fidelizacion"},
    {"id": "whatsapp", "label": "WhatsApp Business", "icon": "fa-brands fa-whatsapp", "route": "/multitienda/whatsapp"},
    {"id": "empleados", "label": "Empleados", "icon": "fa-solid fa-id-badge", "route": "/multitienda/empleados"},
    {"id": "seguidores", "label": "Seguidores", "icon": "fa-solid fa-user-group", "route": "/multitienda/seguidores"},
    {"id": "proveedores", "label": "Proveedores", "icon": "fa-solid fa-handshake", "route": "/multitienda/proveedores"},
    {"id": "ia", "label": "IA", "icon": "fa-solid fa-robot", "route": "/multitienda/ia"},
    {"id": "institucion_financiera", "label": "Institución financiera", "icon": "fa-solid fa-building-columns", "route": "/multitienda/institucion_financiera"},
    {"id": "apartados", "label": "Apartados", "icon": "fa-solid fa-box-archive", "route": "/multitienda/apartados"},
    {"id": "crm", "label": "CRM", "icon": "fa-solid fa-users-rectangle", "route": "/multitienda/crm"},
    {"id": "subastas", "label": "Subastas", "icon": "fa-solid fa-gavel", "route": "/multitienda/subastas"},
    {"id": "configuracion", "label": "Configuración", "icon": "fa-solid fa-gear", "route": "/multitienda/configuracion"},
    {"id": "gestion", "label": "Administración de tiendas", "icon": "fa-solid fa-store", "route": "/multitienda/administracion_tiendas"},
    {"id": "repartidores", "label": "Repartidores", "icon": "fa-solid fa-motorcycle", "route": "/multitienda/repartidores"},
]

_PUBLIC_LANDING_RESERVED = {
    "tiendas",
    "destacados",
    "destaacados",
    "carrito",
    "multitienda",
    "configuracion",
    "api",
    "static",
    "templates",
    "icon",
}
_SECTION_HINTS = {
    "inicio": "Resumen del marketplace",
    "videos": "Contenido de tienda",
    "productos": "Catalogo y fichas",
    "referidos": "Programa de crecimiento",
    "notificaciones_pwa": "Mensajes a clientes de la tienda",
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
    "crm": "Relación con clientes",
    "subastas": "Pujas y adjudicacion",
    "configuracion": "Ajustes de tienda",
    "gestion": "Operacion del marketplace",
    "repartidores": "Logistica y entregas",
}
_SECTION_GROUPS = [
    ("General", {"inicio", "configuracion", "gestion"}),
    ("Contenido", {"videos", "productos"}),
    ("Comercial", {"referidos", "notificaciones_pwa", "cupones", "fidelizacion", "whatsapp", "seguidores", "proveedores", "crm", "subastas"}),
    ("Operacion", {"reservaciones", "empleados", "apartados", "repartidores", "institucion_financiera", "ia"}),
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
_SIDEBAR_STYLE_TAG = f"<style>\n{load_sidebar_css()}\n</style>"
_SHELL_CSS_PATH = Path(__file__).resolve().parent.parent / 'static' / 'css' / 'multitienda-shell.css'
_MODULE_LAYOUT_OVERRIDES = f'<style>\n{_SHELL_CSS_PATH.read_text(encoding="utf-8")}\n</style>'
_MULTITIENDA_FAVICON_TAGS = (
    '<link rel="icon" type="image/png" href="/multitienda/multitienda/static/imagenes/logo_vale.png" />'
    '<link rel="shortcut icon" type="image/png" href="/multitienda/multitienda/static/imagenes/logo_vale.png" />'
)


def _resolve_store_permissions(db, scope: dict) -> dict:
    return _resolve_store_permissions_impl(db, scope, _decode_store_theme)


def _get_optional_section_integration(section_id: str) -> dict:
    return _get_optional_section_integration_impl(section_id, _OPTIONAL_SECTION_INTEGRATIONS)


def _resolve_enabled_module_route(module_key: str) -> str:
    return _resolve_enabled_module_route_impl(module_key, is_module_enabled, list_modules_payload)


def _optional_section_available(section_id: str) -> bool:
    return _optional_section_available_impl(
        section_id,
        _OPTIONAL_SECTION_INTEGRATIONS,
        is_module_enabled,
        list_modules_payload,
    )


def _resolve_integrated_section_target(section_id: str, scope: dict | None = None) -> str:
    return _resolve_integrated_section_target_impl(
        section_id,
        _OPTIONAL_SECTION_INTEGRATIONS,
        is_module_enabled,
        list_modules_payload,
        scope,
    )


def _resolve_integrated_module_context(section_id: str, scope: dict | None = None) -> dict[str, str | bool]:
    return _resolve_integrated_module_context_impl(
        section_id,
        _OPTIONAL_SECTION_INTEGRATIONS,
        is_module_enabled,
        list_modules_payload,
        scope,
    )


def _can_access_store_config(role_name: str | None) -> bool:
    return _can_access_store_config_impl(role_name)


def _visible_module_sections(role_name: str | None, store_permissions: dict | None = None) -> list[dict[str, str]]:
    return _visible_module_sections_impl(
        role_name,
        _MODULE_SECTIONS,
        _OPTIONAL_SECTION_INTEGRATIONS,
        is_module_enabled,
        list_modules_payload,
        store_permissions,
    )


def _can_access_module_section(role_name: str | None, section_id: str, store_permissions: dict | None = None) -> bool:
    return _can_access_module_section_impl(
        role_name,
        section_id,
        _MODULE_SECTIONS,
        _OPTIONAL_SECTION_INTEGRATIONS,
        is_module_enabled,
        list_modules_payload,
        store_permissions,
    )


def _build_marketplace_workspace_script() -> str:
    return """
<script>
(function () {
    var root = document.querySelector('.multitienda-shell');
    if (!root) return;
    var sidebar = root.querySelector('.sidebar-dark');
    var heroSection = root.querySelector('.multitienda-shell__hero');
    var heroToggleBtn = root.querySelector('[data-multitienda-hero-toggle="1"]');
    var sidebarToggleBtn = root.querySelector('[data-multitienda-sidebar-toggle="1"]');
    var storesCountEl = root.querySelector('[data-multitienda-stat="stores"]');
    var productsCountEl = root.querySelector('[data-multitienda-stat="products"]');
    var membershipEl = root.querySelector('[data-multitienda-stat="membership"]');
    var inventoryEl = root.querySelector('[data-multitienda-stat="inventory"]');
    var storeNameEls = root.querySelectorAll('[data-multitienda-store-name]');
    var storeSubtitleEls = root.querySelectorAll('[data-multitienda-store-subtitle]');
    var sidebarStoreEls = root.querySelectorAll('[data-multitienda-sidebar-store]');
    var sidebarStoreMetaEls = root.querySelectorAll('[data-multitienda-sidebar-store-meta]');
    var accessMomentEl = root.querySelector('[data-multitienda-access-moment]');
    var collapsibles = root.querySelectorAll('[data-sb-collapsible]');

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

    function applySidebarCollapsed(collapsed) {
        root.classList.toggle('is-sidebar-collapsed', !!collapsed);
        if (sidebar) {
            sidebar.classList.toggle('is-collapsed', !!collapsed);
        }
        if (!sidebarToggleBtn) return;
        sidebarToggleBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
        sidebarToggleBtn.innerHTML = collapsed
            ? '<i class="fa-solid fa-chevron-left" aria-hidden="true"></i>'
            : '<i class="fa-solid fa-chevron-right" aria-hidden="true"></i>';
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

    try {
        applySidebarCollapsed(window.localStorage.getItem('multitienda_sidebar_collapsed') === '1');
    } catch (error) {
        applySidebarCollapsed(false);
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

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function () {
            var nextCollapsed = !(sidebar && sidebar.classList.contains('is-collapsed'));
            applySidebarCollapsed(nextCollapsed);
            try {
                window.localStorage.setItem('multitienda_sidebar_collapsed', nextCollapsed ? '1' : '0');
            } catch (error) {}
        });
    }

    collapsibles.forEach(function (item) {
        var toggle = item.querySelector('[data-sb-collapsible-toggle]');
        if (!toggle) return;
        toggle.addEventListener('click', function () {
            var open = item.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    });

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
            if (!stores.length) {
                var hasInitialStore = false;
                (storeNameEls || []).forEach(function (node) {
                    if (String(node.textContent || '').trim() && String(node.textContent || '').trim() !== 'Nombre de la tienda') {
                        hasInitialStore = true;
                    }
                });
                if (storesCountEl) storesCountEl.textContent = hasInitialStore ? '1' : '0';
                if (!hasInitialStore) {
                    setText(storeNameEls, 'Sin tienda asignada');
                    setText(storeSubtitleEls, 'Asigna una tienda para activar la operación del marketplace.');
                    setText(sidebarStoreEls, 'Sin tienda');
                    if (membershipEl) membershipEl.textContent = 'Sin membresía';
                    if (inventoryEl) inventoryEl.textContent = 'Pendiente';
                }
                return;
            }
            if (storesCountEl) storesCountEl.textContent = String(stores.length);
            var store = stores[0] || {};
            setText(storeNameEls, String(store.name || 'Nombre de la tienda'));
            setText(sidebarStoreEls, String(store.name || 'Mi tienda'));
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


@lru_cache(maxsize=64)
def _parsed_marketplace_document(document_html: str) -> tuple[str, str, tuple[str, ...]]:
    prefixed = _prefix_root_relative_urls(document_html, "/multitienda")
    link_styles = "\n".join(m.group(0) for m in _LINK_CSS_RE.finditer(prefixed))
    inline_styles = "\n".join(
        f"<style>{m.group(1)}</style>" for m in _STYLE_RE.finditer(prefixed)
    )
    styles = "\n".join(filter(None, [link_styles, inline_styles]))
    main_match = _MAIN_RE.search(prefixed)
    main_markup = main_match.group(1).strip() if main_match else prefixed

    filtered_scripts: list[str] = []
    for match in _SCRIPT_RE.finditer(prefixed):
        script_markup = match.group(1)
        if "/static/js/backend-navbar.js" in script_markup:
            continue
        if "/static/js/backend-sidebar-core.js" in script_markup:
            continue
        filtered_scripts.append(script_markup)

    return styles, main_markup, tuple(filtered_scripts)


def _section_label(section_id: str) -> str:
    section_meta = next((item for item in _MODULE_SECTIONS if item["id"] == section_id), None)
    return section_meta["label"] if section_meta else "Multitienda"


def _shell_variant(section_id: str) -> str:
    return "hero" if section_id == "inicio" else "standard"


@lru_cache(maxsize=128)
def _cached_marketplace_shell_template(
    section_id: str,
    document_hash: str,
    shell_variant: str,
    styles: str,
    main_markup: str,
    scripts_markup: str,
) -> str:
    del document_hash
    del shell_variant
    section_label = _section_label(section_id)
    return (
        '<div class="multitienda-official-view">'
        + _MODULE_NAVBAR_BOOTSTRAP
        + _MODULE_LAYOUT_OVERRIDES
        + _SIDEBAR_STYLE_TAG
        + styles
        + '<section class="multitienda-shell">'
        + "__SIDEBAR__"
        + '<div class="multitienda-shell__content">'
        + "__HERO__"
        + '<section class="multitienda-shell__body">'
        + '<div class="multitienda-shell__panel-head">'
        + '<div class="multitienda-shell__panel-title"><h2>'
        + escape(section_label)
        + "</h2></div>"
        + "__PANEL_ACTIONS__"
        + "</div>"
        + '<div class="multitienda-shell__module-body"><main class="page">'
        + main_markup
        + "</main></div>"
        + "</section>"
        + "</div>"
        + "</section>"
        + scripts_markup
        + _build_marketplace_workspace_script()
        + "</div>"
    )


def _build_marketplace_shell_content(
    document_html: str,
    section_id: str,
    *,
    sections: list[dict[str, str]],
    viewer_name: str,
    initial_store_name: str = "",
    initial_store_subtitle: str = "",
    initial_membership: str = "",
    initial_inventory: str = "",
) -> str:
    styles, main_markup, filtered_scripts = _parsed_marketplace_document(document_html)
    section_label = _section_label(section_id)
    show_hero = section_id == "inicio"

    hero_markup = ""
    panel_actions_markup = ""
    if show_hero:
        hero_markup = (
            '<section class="multitienda-shell__hero">'
            + '<div class="multitienda-shell__hero-grid">'
            + '<div class="multitienda-shell__hero-copy">'
            + '<span class="multitienda-shell__eyebrow"><i class="fa-solid fa-chart-line" aria-hidden="true"></i> Tablero de control</span>'
            + '<h1><span class="multitienda-shell__store-name" data-multitienda-store-name>'
            + escape(initial_store_name or "Nombre de la tienda")
            + "</span></h1>"
            + '<div class="multitienda-shell__hero-meta">'
            + '<span class="multitienda-shell__meta-pill"><i class="fa-regular fa-user" aria-hidden="true"></i> '
            + escape(viewer_name or "Usuario")
            + "</span>"
            + '<span class="multitienda-shell__meta-pill"><i class="fa-regular fa-clock" aria-hidden="true"></i> <span data-multitienda-access-moment>Ahora</span></span>'
            + '<span class="multitienda-shell__meta-pill"><i class="fa-solid fa-layer-group" aria-hidden="true"></i> '
            + escape(section_label)
            + "</span>"
            + "</div>"
            + '<p data-multitienda-store-subtitle>'
            + escape(initial_store_subtitle or "Configura la identidad comercial y la operación de tu tienda.")
            + "</p>"
            + "</div>"
            + '<div class="multitienda-shell__stats">'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Tiendas visibles</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="stores">0</strong></article>'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Productos locales</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="products">0</strong></article>'
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Membresía</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="membership">'
            + escape(initial_membership or "Sin membresía")
            + "</strong></article>"
            + '<article class="multitienda-shell__stat"><span class="multitienda-shell__stat-label">Inventario</span><strong class="multitienda-shell__stat-value" data-multitienda-stat="inventory">'
            + escape(initial_inventory or "Pendiente")
            + "</strong></article>"
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

    document_hash = hashlib.sha1(document_html.encode("utf-8")).hexdigest()
    shell_template = _cached_marketplace_shell_template(
        section_id,
        document_hash,
        _shell_variant(section_id),
        styles,
        main_markup,
        "".join(filtered_scripts),
    )
    return (
        shell_template
        .replace("__SIDEBAR__", render_sidebar_markup(sections, section_id, viewer_name, initial_store_name), 1)
        .replace("__HERO__", hero_markup, 1)
        .replace("__PANEL_ACTIONS__", panel_actions_markup, 1)
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
    with _request_db_context(request, include_permissions=True) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        store_perms = ctx["store_permissions"]
        store_summaries = _resolve_store_summaries(request, db, scope)
    role = str(scope.get("role") or getattr(request.state, "user_role", ""))
    # If domain-DB lookup failed (no user_id), fall back to the session role
    # so a superadmin/admin who exists in SIPET's auth but lacks a vendor entry
    # still gets the correct sidebar and can access admin-only sections.
    if scope.get("user_id") is None:
        session_role = str(getattr(request.state, "user_role", "") or "")
        if session_role:
            role = session_role
    visible_sections = _visible_module_sections(role, store_perms)
    initial_store = store_summaries[0] if store_summaries else {}
    initial_store_name = str(initial_store.get("name") or "").strip()
    initial_store_slug = str(initial_store.get("slug") or "").strip()
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
            initial_store_name=initial_store_name,
            initial_store_subtitle=(
                f"Slug público: {initial_store_slug}"
                if initial_store_slug
                else "Configura la identidad comercial y la operación de tu tienda."
            ),
            initial_membership=str(initial_store.get("membership") or ""),
            initial_inventory="Activo" if bool(initial_store.get("inventoryEnabled", False)) else "Desactivado",
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
    content = _prefix_root_relative_urls(document_html, "/multitienda")
    if "</head>" in content and "/multitienda/multitienda/static/imagenes/logo_vale.png" not in content:
        content = content.replace("</head>", f"{_MULTITIENDA_FAVICON_TAGS}</head>", 1)
    return HTMLResponse(content=content)


def _render_section_or_redirect(
    request: Request,
    section_id: str,
    *,
    html_factory=None,
    context_html_factory=None,
    integrated: bool = False,
):
    context = _resolve_request_context(request, include_permissions=True)
    scope = context["scope"]
    store_perms = context["store_permissions"]
    role_name = context["role_name"]
    if not _can_access_module_section(role_name, section_id, store_perms):
        return RedirectResponse(url="/multitienda/inicio", status_code=307)
    if integrated:
        target = _resolve_integrated_section_target(section_id, scope)
        if not target:
            return RedirectResponse(url="/multitienda/inicio", status_code=307)
        return RedirectResponse(url=target, status_code=307)
    if context_html_factory is not None:
        return _render_official_shell(request, section_id, context_html_factory(context))
    if html_factory is not None:
        return _render_official_shell(request, section_id, html_factory())
    raise ValueError(f"html_factory is required for non-integrated section '{section_id}'")


def _financial_module_context(section_context: dict[str, object]) -> dict[str, str | bool]:
    role_name = str(section_context["role_name"])
    store_permissions = section_context["store_permissions"]
    if not _can_access_module_section(role_name, "institucion_financiera", store_permissions):
        return {"enabled": False, "target_route": "", "api_base": ""}
    return _resolve_integrated_module_context("institucion_financiera", section_context["scope"])


def _seguidores_section_html(section_context: dict[str, object]) -> str:
    financial_context = _financial_module_context(section_context)
    return seguidores_html(
        max_users=int(section_context["store_permissions"].get("max_portal_users") or 0),
        intelicoop_enabled=bool(financial_context.get("enabled")),
        intelicoop_route=str(financial_context.get("target_route") or ""),
        intelicoop_api_base=str(financial_context.get("api_base") or ""),
    )


def _proveedores_section_html(section_context: dict[str, object]) -> str:
    financial_context = _financial_module_context(section_context)
    return proveedores_html(
        intelicoop_enabled=bool(financial_context.get("enabled")),
        intelicoop_route=str(financial_context.get("target_route") or ""),
        intelicoop_api_base=str(financial_context.get("api_base") or ""),
    )


def _empleados_section_html(section_context: dict[str, object]) -> str:
    return empleados_html(
        max_users=int(section_context["store_permissions"].get("max_internal_users") or 0)
    )


_SECTION_HANDLERS = {
    "videos": {"mode": "render", "html_factory": videos_html},
    "referidos": {"mode": "integrated"},
    "notificaciones_pwa": {"mode": "integrated"},
    "reservaciones": {"mode": "integrated"},
    "cupones": {"mode": "render", "html_factory": cupones_html},
    "fidelizacion": {"mode": "render", "html_factory": fidelizacion_html},
    "whatsapp": {"mode": "render", "html_factory": whatsapp_html},
    "empleados": {"mode": "render_with_context", "context_html_factory": _empleados_section_html},
    "seguidores": {"mode": "render_with_context", "context_html_factory": _seguidores_section_html},
    "proveedores": {"mode": "render_with_context", "context_html_factory": _proveedores_section_html},
    "ia": {"mode": "render", "html_factory": ia_html},
    "institucion_financiera": {"mode": "integrated"},
    "apartados": {"mode": "render", "html_factory": apartados_html},
    "subastas": {"mode": "integrated"},
    "crm": {"mode": "integrated"},
    "gestion": {"mode": "official", "html_factory": gestion_html, "denied_redirect": "/multitienda/configuracion"},
    "repartidores": {"mode": "integrated", "denied_redirect": "/multitienda/inicio"},
}


def _dispatch_section_entrypoint(request: Request, section_id: str):
    config = _SECTION_HANDLERS[section_id]
    denied_redirect = str(config.get("denied_redirect") or "/multitienda/inicio")
    mode = str(config["mode"])

    if mode == "render":
        return _render_section_or_redirect(
            request,
            section_id,
            html_factory=config["html_factory"],
        )
    if mode == "render_with_context":
        return _render_section_or_redirect(
            request,
            section_id,
            context_html_factory=config["context_html_factory"],
        )
    if mode == "integrated":
        return _render_section_or_redirect(request, section_id, integrated=True)
    if mode == "official":
        role_name = str(getattr(request.state, "user_role", "") or "").strip()
        if not _can_access_module_section(role_name, section_id):
            return RedirectResponse(url=denied_redirect, status_code=307)
        return _render_official_shell(request, section_id, config["html_factory"]())
    raise ValueError(f"Modo de seccion no soportado: {mode}")


def _db_session_for_request(request: Request):
    from fastapi_modulo.core.database_router import normalize_host
    host = normalize_host(
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.hostname
        or ""
    )
    return core_db.get_session_factory_for_host(host or core_db.get_request_host())()


def _public_store_exists(request: Request, store_slug: str) -> bool:
    db = _db_session_for_request(request)
    try:
        row = db.execute(
            text(
                """
                SELECT id
                FROM vendors
                WHERE LOWER(store_slug) = :slug
                  AND is_active = TRUE
                LIMIT 1
                """
            ),
            {"slug": str(store_slug or "").strip().lower()},
        ).mappings().first()
        return bool(row)
    finally:
        db.close()


def _public_store_product_exists(request: Request, store_slug: str, product_slug: str) -> bool:
    db = _db_session_for_request(request)
    try:
        row = db.execute(
            text(
                """
                SELECT p.id
                FROM products p
                JOIN vendors v ON v.id = p.vendor_id
                WHERE LOWER(v.store_slug) = :store_slug
                  AND v.is_active = TRUE
                  AND LOWER(p.slug) = :product_slug
                  AND p.is_active = TRUE
                  AND LOWER(COALESCE(p.status, '')) = 'published'
                LIMIT 1
                """
            ),
            {
                "store_slug": str(store_slug or "").strip().lower(),
                "product_slug": str(product_slug or "").strip().lower(),
            },
        ).mappings().first()
        return bool(row)
    finally:
        db.close()


def _load_public_store_info(request: Request, store_slug: str) -> dict:
    db = _db_session_for_request(request)
    try:
        row = db.execute(
            text(
                """
                SELECT id, store_name, store_slug, logo, banner, store_theme
                FROM vendors
                WHERE LOWER(store_slug) = :slug
                  AND is_active = TRUE
                LIMIT 1
                """
            ),
            {"slug": str(store_slug or "").strip().lower()},
        ).mappings().first()
        if not row:
            return {"success": False, "data": {}}
        theme = _decode_store_theme(row.get("store_theme"))
        config = _extract_store_config(theme)
        landing_banner = (
            str(config.get("landing_banner") or "").strip()
            or str(row.get("banner") or "").strip()
        )
        logo = (
            str(config.get("site_logo") or "").strip()
            or str(row.get("logo") or "").strip()
        )
        return {
            "success": True,
            "data": {
                "id": int(row.get("id") or 0),
                "store_name": str(row.get("store_name") or ""),
                "store_slug": str(row.get("store_slug") or ""),
                "logo": logo,
                "landing_banner": landing_banner,
                "email": str(config.get("email") or ""),
                "phone": str(config.get("phone") or ""),
                "slogan": str(config.get("slogan") or ""),
                "website": str(config.get("website") or ""),
                "street": str(config.get("street") or ""),
                "between_streets": str(config.get("between_streets") or ""),
                "neighborhood": str(config.get("neighborhood") or ""),
                "postal_code": str(config.get("postal_code") or ""),
                "locality": str(config.get("locality") or ""),
                "municipality": str(config.get("municipality") or ""),
                "state": str(config.get("state") or ""),
                "country": str(config.get("country") or ""),
                "latitude": str(config.get("latitude") or ""),
                "longitude": str(config.get("longitude") or ""),
                "mission": str(config.get("mission") or ""),
                "vision": str(config.get("vision") or ""),
                "partner_benefits": str(config.get("partner_benefits") or ""),
                "consumer_rights": str(config.get("consumer_rights") or ""),
                "data_privacy": str(config.get("data_privacy") or ""),
                "additional_conditions": str(config.get("additional_conditions") or ""),
                "hide_email": bool(config.get("hide_email")),
                "hide_phone": bool(config.get("hide_phone")),
                "hide_website": bool(config.get("hide_website")),
                "hide_address": bool(config.get("hide_address")),
                "hide_map": bool(config.get("hide_map")),
                "hide_partner_benefits": bool(config.get("hide_partner_benefits")),
                "hide_about": bool(config.get("hide_about")),
                "hide_policies": bool(config.get("hide_policies")),
                "hide_product_prices": bool(config.get("hide_product_prices")),
                "hide_cart_buttons": bool(config.get("hide_cart_buttons")),
            },
        }
    finally:
        db.close()


def _load_public_products(request: Request, mode: str, store_id_value: str) -> list[dict]:
    store_id = int(store_id_value) if str(store_id_value or "").isdigit() else None
    db = _db_session_for_request(request)
    try:
        return product_service.list_public_catalog(
            db,
            store_id,
            featured_only=str(mode or "").strip().lower() == "featured",
        )
    finally:
        db.close()


def _current_username(request: Request) -> str:
    return str(
        getattr(request.state, "user_name", None)
        or getattr(request.state, "username", None)
        or request.cookies.get("user_name")
        or request.cookies.get("username")
        or request.cookies.get("usuario")
        or ""
    ).strip()


def _resolve_request_context(request: Request, *, include_permissions: bool = False) -> dict[str, object]:
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        context = {
            "scope": scope,
            "role_name": str(scope.get("role") or getattr(request.state, "user_role", "")),
        }
        if include_permissions:
            context["store_permissions"] = _resolve_store_permissions(db, scope)
        return context
    finally:
        db.close()


@contextmanager
def _request_db_context(request: Request, *, include_permissions: bool = False):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        context = {
            "db": db,
            "scope": scope,
            "role_name": str(scope.get("role") or getattr(request.state, "user_role", "")),
        }
        if include_permissions:
            context["store_permissions"] = _resolve_store_permissions(db, scope)
        yield context
    except Exception:
        _log.exception(
            "Error en _request_db_context para %s %s; se realizara rollback.",
            request.method,
            request.url.path,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _resolve_store_scope(request: Request, db) -> dict[str, object]:
    return _resolve_store_scope_impl(
        request,
        db,
        lambda current_request, current_db: _current_user_record_impl(current_request, current_db, _current_username),
    )


def _list_store_rows(db, where_clause: str = "", params: dict[str, object] | None = None) -> list[dict]:
    return db.execute(
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
        params or {},
    ).mappings().all()


def _load_business_type_names(db) -> dict[str, str]:
    def _fetch_names(source_db) -> dict[str, str]:
        rows = source_db.execute(
            text(
                """
                SELECT code, name
                FROM store_business_types
                ORDER BY name ASC
                """
            )
        ).mappings().all()
        return {
            str(row.get("code") or "").strip(): str(row.get("name") or "").strip()
            for row in rows
            if str(row.get("code") or "").strip()
        }

    try:
        names = _fetch_names(db)
        if names:
            return names
    except Exception:
        _log.exception("Error cargando tipos de negocio desde la sesion principal.")
    fallback_db = SessionLocal()
    try:
        return _fetch_names(fallback_db)
    except Exception:
        _log.exception("Error cargando tipos de negocio desde la sesion fallback.")
        return {}
    finally:
        fallback_db.close()


def _serialize_store_summary(row: dict) -> dict[str, object]:
    return _serialize_store_summary_with_types(row, {})


def _serialize_store_summary_with_types(row: dict, business_type_names: dict[str, str]) -> dict[str, object]:
    theme = _decode_store_theme(row.get("store_theme"))
    type_code = str(theme.get("store_type") or "").strip()
    stored_type_name = str(theme.get("store_type_name") or "").strip()
    return {
        "id": row.get("id"),
        "name": row.get("store_name") or "",
        "slug": row.get("store_slug") or "",
        "adminId": str(row.get("vendor_id") or ""),
        "adminLabel": (
            str(row.get("full_name") or "").strip()
            or str(decrypt_sensitive(row.get("encrypted_username")) or "").strip()
        ),
        "typeCode": type_code,
        "typeLabel": stored_type_name or business_type_names.get(type_code) or type_code,
        "membership": str(theme.get("membership") or ""),
        "isActive": bool(row.get("is_active")),
        "isFeatured": bool(row.get("is_featured")),
        "inventoryEnabled": bool(theme.get("inventory_enabled", False)),
        "canUploadVideos": _coerce_theme_bool(theme.get("can_upload_videos", False)),
        "validity": str(theme.get("validity") or ""),
        "referrals": _coerce_theme_bool(theme.get("referrals")),
        "fidelizacion": _coerce_theme_bool(theme.get("fidelizacion")),
        "pwaNotifications": _coerce_theme_bool(theme.get("pwa_notifications")),
        "appointments": _coerce_theme_bool(theme.get("appointments")),
        "coupons": _coerce_theme_bool(theme.get("coupons")),
        "whatsapp": _coerce_theme_bool(theme.get("whatsapp")),
        "maxInternalUsers": int(theme.get("max_internal_users") or 0),
        "maxPortalUsers": int(theme.get("max_portal_users") or 0),
    }


def _resolve_store_summaries(request: Request, db, scope: dict[str, object] | None = None) -> list[dict[str, object]]:
    effective_scope = scope or _resolve_store_scope(request, db)
    business_type_names = _load_business_type_names(db)
    where_clause = ""
    params: dict[str, object] = {}
    if effective_scope["restricted"]:
        if effective_scope["store_id"]:
            where_clause = "WHERE v.id = :store_id"
            params["store_id"] = int(effective_scope["store_id"])
        elif effective_scope["user_id"]:
            where_clause = "WHERE v.vendor_id = :vendor_id"
            params["vendor_id"] = int(effective_scope["user_id"])
        else:
            return []
    rows = _list_store_rows(db, where_clause, params)
    if effective_scope["restricted"] and not rows:
        user_id = effective_scope.get("user_id")
        if user_id:
            rows = _list_store_rows(
                db,
                "WHERE v.id IN (SELECT se.vendor_id FROM store_employees se WHERE se.user_id = :user_id)",
                {"user_id": int(user_id)},
            )
    return [_serialize_store_summary_with_types(row, business_type_names) for row in rows]


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
                    _log.exception("No se pudo agregar IDENTITY a vendors.id; se intentara fallback con secuencia.")
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


def _ensure_product_tables(bind) -> None:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore  # noqa: F401
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product, ProductImage  # noqa: F401

    table_names = [Product.__tablename__, ProductImage.__tablename__]
    tables = [Base.metadata.tables[name] for name in table_names if name in Base.metadata.tables]
    if tables:
        Base.metadata.create_all(bind=bind, tables=tables, checkfirst=True)

def _allowed_store_config_keys() -> set[str]:
    return {
        "site_logo",
        "landing_banner",
        "landing_banner_mobile",
        "landing_banner_list",
        "website",
        "phone",
        "email",
        "street",
        "between_streets",
        "neighborhood",
        "postal_code",
        "locality",
        "municipality",
        "state",
        "country",
        "latitude",
        "longitude",
        "schedule_monday_open",
        "schedule_monday_close",
        "schedule_monday_break",
        "schedule_tuesday_open",
        "schedule_tuesday_close",
        "schedule_tuesday_break",
        "schedule_wednesday_open",
        "schedule_wednesday_close",
        "schedule_wednesday_break",
        "schedule_thursday_open",
        "schedule_thursday_close",
        "schedule_thursday_break",
        "schedule_friday_open",
        "schedule_friday_close",
        "schedule_friday_break",
        "schedule_saturday_open",
        "schedule_saturday_close",
        "schedule_saturday_break",
        "schedule_sunday_open",
        "schedule_sunday_close",
        "schedule_sunday_break",
        "slogan",
        "mission",
        "vision",
        "partner_benefits",
        "legal_name",
        "tax_id",
        "tax_regime",
        "tax_postal_code",
        "billing_email",
        "fiscal_street",
        "fiscal_exterior_number",
        "fiscal_interior_number",
        "fiscal_neighborhood",
        "fiscal_municipality",
        "fiscal_state",
        "consumer_rights",
        "data_privacy",
        "additional_conditions",
        "hide_email",
        "hide_phone",
        "hide_website",
        "hide_address",
        "hide_map",
        "hide_partner_benefits",
        "hide_about",
        "hide_policies",
        "hide_go_to_store_button",
        "hide_product_prices",
        "hide_terms",
        "hide_cart_buttons",
        "hide_cart_terms_checkbox",
    }


def _extract_store_config(theme: dict | None) -> dict[str, object]:
    nested = (theme or {}).get("configuracion")
    return dict(nested) if isinstance(nested, dict) else {}


def _build_store_config_payload(row: dict | None) -> dict[str, object]:
    if not row:
        return {}
    theme = _decode_store_theme(row.get("store_theme"))
    config = _extract_store_config(theme)
    if str(config.get("site_logo") or "").strip() == "" and str(row.get("logo") or "").strip():
        config["site_logo"] = str(row.get("logo") or "").strip()
    if str(config.get("landing_banner") or "").strip() == "" and str(row.get("banner") or "").strip():
        config["landing_banner"] = str(row.get("banner") or "").strip()
    if str(row.get("phone") or "").strip() and not str(config.get("phone") or "").strip():
        config["phone"] = str(row.get("phone") or "").strip()
    if str(row.get("address") or "").strip() and not str(config.get("street") or "").strip():
        config["street"] = str(row.get("address") or "").strip()
    if str(row.get("country") or "").strip() and not str(config.get("country") or "").strip():
        config["country"] = str(row.get("country") or "").strip()
    return config


def _extract_catalog_products(theme: dict | None) -> list[dict[str, object]]:
    raw_products = (theme or {}).get("catalog_products")
    if not isinstance(raw_products, list):
        return []
    return [dict(item) for item in raw_products if isinstance(item, dict)]


def _is_catalog_product_public(product: dict | None) -> bool:
    item = product or {}
    return bool(item.get("publicado")) or bool(item.get("ecomPublicado"))


def _slugify_catalog_product(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "producto"


def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _fits_vendor_asset_column(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return True
    if raw.startswith("data:"):
        return False
    return len(raw) <= 255


def _normalize_catalog_gallery(product: dict[str, object]) -> list[str]:
    return [
        img for img in (product.get("galleryImages") or [])
        if isinstance(img, str) and img and not img.startswith("data:") and len(img) <= 255
    ]


def _sync_primary_product_image(db, product_id: int, product_name: str, primary_image: str) -> None:
    image_row = db.execute(
        text(
            """
            SELECT id, image, alt_text
            FROM product_images
            WHERE product_id = :product_id
              AND is_primary = TRUE
            ORDER BY id ASC
            LIMIT 1
            """
        ),
        {"product_id": product_id},
    ).mappings().first()
    if primary_image:
        if image_row:
            if (
                str(image_row.get("image") or "") != primary_image
                or str(image_row.get("alt_text") or "") != product_name
            ):
                db.execute(
                    text(
                        """
                        UPDATE product_images
                        SET image = :image,
                            alt_text = :alt_text,
                            "order" = 0
                        WHERE id = :image_id
                        """
                    ),
                    {
                        "image_id": int(image_row["id"]),
                        "image": primary_image,
                        "alt_text": product_name,
                    },
                )
        else:
            db.execute(
                text(
                    """
                    INSERT INTO product_images (product_id, image, alt_text, is_primary, "order")
                    VALUES (:product_id, :image, :alt_text, 1, 0)
                    """
                ),
                {
                    "product_id": product_id,
                    "image": primary_image,
                    "alt_text": product_name,
                },
            )
    elif image_row:
        db.execute(
            text("DELETE FROM product_images WHERE id = :image_id"),
            {"image_id": int(image_row["id"])},
        )


def _sync_gallery_product_images(db, product_id: int, product_name: str, gallery: list[str]) -> None:
    existing_rows = db.execute(
        text(
            """
            SELECT id, image, alt_text, "order"
            FROM product_images
            WHERE product_id = :product_id
              AND is_primary = 0
            ORDER BY "order" ASC, id ASC
            """
        ),
        {"product_id": product_id},
    ).mappings().all()
    existing_urls = [str(row.get("image") or "") for row in existing_rows]
    if existing_urls == gallery and all(str(row.get("alt_text") or "") == product_name for row in existing_rows):
        return
    existing_by_url: dict[str, list[dict[str, object]]] = {}
    for row in existing_rows:
        existing_by_url.setdefault(str(row.get("image") or ""), []).append(dict(row))
    retained_ids: set[int] = set()
    for gal_order, gal_url in enumerate(gallery):
        desired_order = gal_order + 1
        candidates = existing_by_url.get(gal_url) or []
        reusable = None
        while candidates:
            candidate = candidates.pop(0)
            candidate_id = int(candidate["id"])
            if candidate_id not in retained_ids:
                reusable = candidate
                retained_ids.add(candidate_id)
                break
        if reusable:
            if (
                int(reusable.get("order") or 0) != desired_order
                or str(reusable.get("alt_text") or "") != product_name
            ):
                db.execute(
                    text(
                        """
                        UPDATE product_images
                        SET alt_text = :alt_text,
                            "order" = :ord
                        WHERE id = :image_id
                        """
                    ),
                    {
                        "image_id": int(reusable["id"]),
                        "alt_text": product_name,
                        "ord": desired_order,
                    },
                )
            continue
        db.execute(
            text(
                """
                INSERT INTO product_images (product_id, image, alt_text, is_primary, "order")
                VALUES (:product_id, :image, :alt_text, 0, :ord)
                """
            ),
            {"product_id": product_id, "image": gal_url, "alt_text": product_name, "ord": desired_order},
        )
    stale_ids = [int(row["id"]) for row in existing_rows if int(row["id"]) not in retained_ids]
    if stale_ids:
        db.execute(
            text("DELETE FROM product_images WHERE id IN :image_ids").bindparams(bindparam("image_ids", expanding=True)),
            {"image_ids": stale_ids},
        )


def _sync_catalog_products_to_marketplace(db, store_id: int, previous_products: list[dict[str, object]], catalog_products: list[dict[str, object]]) -> list[dict[str, object]]:
    previous_db_ids = {
        int(item.get("db_product_id"))
        for item in previous_products
        if str(item.get("db_product_id") or "").isdigit()
    }
    current_db_ids: set[int] = set()
    synced_products: list[dict[str, object]] = []

    for index, raw_product in enumerate(catalog_products):
        product = dict(raw_product)
        product_name = str(product.get("nombre") or "").strip()
        if not product_name:
            continue
        is_public = _is_catalog_product_public(product)

        mapped_product_id = int(product["db_product_id"]) if str(product.get("db_product_id") or "").isdigit() else None
        base_slug = _slugify_catalog_product(product_name)
        slug = base_slug
        suffix = 2
        while True:
            slug_row = db.execute(
                text(
                    """
                    SELECT id
                    FROM products
                    WHERE slug = :slug
                      AND (:product_id IS NULL OR id <> :product_id)
                    LIMIT 1
                    """
                ),
                {"slug": slug, "product_id": mapped_product_id},
            ).mappings().first()
            if not slug_row:
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        payload = {
            "vendor_id": store_id,
            "name": product_name,
            "description": str(product.get("descCorta") or product.get("descLarga") or product.get("descripcion") or ""),
            "price": _safe_float(product.get("precio")),
            "stock_quantity": _safe_int(product.get("stock")),
            "slug": slug,
            "is_active": is_public,
            "status": "published" if is_public else "draft",
            "type": "simple",
        }

        if mapped_product_id:
            existing_row = db.execute(
                text(
                    """
                    SELECT id, name, description, price, stock_quantity, slug, is_active, status, type
                    FROM products
                    WHERE id = :product_id
                      AND vendor_id = :vendor_id
                    LIMIT 1
                    """
                ),
                {"product_id": mapped_product_id, "vendor_id": store_id},
            ).mappings().first()
            if existing_row:
                changed = (
                    str(existing_row.get("name") or "") != str(payload["name"])
                    or str(existing_row.get("description") or "") != str(payload["description"])
                    or float(existing_row.get("price") or 0) != float(payload["price"])
                    or int(existing_row.get("stock_quantity") or 0) != int(payload["stock_quantity"])
                    or str(existing_row.get("slug") or "") != str(payload["slug"])
                    or bool(existing_row.get("is_active")) != bool(payload["is_active"])
                    or str(existing_row.get("status") or "") != str(payload["status"])
                    or str(existing_row.get("type") or "") != str(payload["type"])
                )
                if changed:
                    updated_row = db.execute(
                        text(
                            """
                            UPDATE products
                            SET name = :name,
                                description = :description,
                                price = :price,
                                stock_quantity = :stock_quantity,
                                slug = :slug,
                                is_active = :is_active,
                                status = :status,
                                type = :type,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :product_id
                              AND vendor_id = :vendor_id
                            RETURNING id
                            """
                        ),
                        {**payload, "product_id": mapped_product_id},
                    ).mappings().first()
                    if not updated_row:
                        mapped_product_id = None
            else:
                mapped_product_id = None

        if mapped_product_id is None:
            created_row = db.execute(
                text(
                    """
                    INSERT INTO products (
                        vendor_id, name, description, price, stock_quantity, slug,
                        is_active, status, type, created_at, updated_at
                    ) VALUES (
                        :vendor_id, :name, :description, :price, :stock_quantity, :slug,
                        :is_active, :status, :type, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                    """
                ),
                payload,
            ).mappings().first()
            mapped_product_id = int(created_row["id"])

        current_db_ids.add(mapped_product_id)
        product["db_product_id"] = mapped_product_id
        product["slug"] = slug
        product["publicado"] = is_public

        primary_image = str(product.get("imagen") or "").strip()
        if primary_image.startswith("data:") or len(primary_image) > 255:
            primary_image = ""
        _sync_primary_product_image(db, mapped_product_id, product_name, primary_image)
        _sync_gallery_product_images(db, mapped_product_id, product_name, _normalize_catalog_gallery(product))

        synced_products.append(product)

    for removed_product_id in previous_db_ids - current_db_ids:
        db.execute(text("DELETE FROM product_images WHERE product_id = :product_id"), {"product_id": removed_product_id})
        db.execute(
            text("DELETE FROM products WHERE id = :product_id AND vendor_id = :vendor_id"),
            {"product_id": removed_product_id, "vendor_id": store_id},
        )

    return synced_products


def multitienda_business_types_proxy():
    return list_business_types()


async def multitienda_create_business_type_proxy(request: Request):
    return await create_business_type(request)


def multitienda_store_admin_users(request: Request):
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        roles_by_id = get_roles_map(db)
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


def multitienda_memberships():
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


def multitienda_list_stores(request: Request):
    db = _db_session_for_request(request)
    try:
        scope = _resolve_store_scope(request, db)
        return {"success": True, "data": _resolve_store_summaries(request, db, scope)}
    finally:
        db.close()


async def multitienda_save_store(request: Request):
    scope = _resolve_request_context(request)["scope"]
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
        _log.exception("No se pudo guardar la tienda para scope=%s", scope)
        raise HTTPException(status_code=500, detail="No se pudo guardar la tienda.") from exc


def multitienda_config_entrypoint(request: Request):
    effective_store_id = None
    redirect_to_canonical = False
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        if not _can_access_store_config(scope.get("role") or getattr(request.state, "user_role", "")):
            return RedirectResponse(url="/multitienda/inicio", status_code=307)
        store_summaries = _resolve_store_summaries(request, db, scope)
        requested_store_id = str(request.query_params.get("store_id") or "").strip()
        config_row = None
        if scope.get("store_id"):
            effective_store_id = int(scope["store_id"])
        elif requested_store_id.isdigit():
            effective_store_id = int(requested_store_id)
        elif store_summaries:
            first_id = store_summaries[0].get("id")
            effective_store_id = int(first_id) if str(first_id or "").isdigit() else None
            redirect_to_canonical = effective_store_id is not None
        if effective_store_id:
            config_row = db.execute(
                text(
                    """
                    SELECT id, logo, banner, address, country, store_theme
                    , phone
                    FROM vendors
                    WHERE id = :store_id
                    LIMIT 1
                    """
                ),
                {"store_id": effective_store_id},
            ).mappings().first()
    if redirect_to_canonical and effective_store_id:
        return RedirectResponse(url=f"/multitienda/configuracion?store_id={effective_store_id}", status_code=307)
    initial_store = store_summaries[0] if store_summaries else {}
    if effective_store_id:
        matching_store = next((item for item in store_summaries if int(item.get("id") or 0) == int(effective_store_id)), None)
        if matching_store:
            initial_store = matching_store
    initial_config_json = json.dumps(_build_store_config_payload(config_row), ensure_ascii=True).replace("</", "<\\/")
    login_identity = get_login_identity_context(request)
    default_logo_url = str(
        resolve_logo_empresa_url()
        or login_identity.get("company_logo_url")
        or login_identity.get("login_logo_url")
        or resolve_sidebar_logo_url(login_identity)
        or "/multitienda/static/imagenes/logo_vale.png"
    ).strip()
    return _render_official_shell(
        request,
        "configuracion",
        configuracion_html(
            initial_store_id=str(effective_store_id or ""),
            initial_store_name=str(initial_store.get("name") or ""),
            initial_store_type=str(initial_store.get("typeLabel") or initial_store.get("typeCode") or ""),
            initial_store_admin=str(initial_store.get("adminLabel") or ""),
            default_logo_url=default_logo_url,
            initial_config_json=initial_config_json,
        ),
    )
# ─── API CRUD — store_tables ──────────────────────────────────────────────────
# Helpers compartidos

def _require_store_id(request: Request) -> int:
    """Devuelve el store_id del vendedor autenticado o lanza 401/403."""
    scope = _resolve_request_context(request)["scope"]
    if not scope["user_id"]:
        raise HTTPException(status_code=401, detail="No autenticado.")
    if scope["store_id"] is None:
        # superadmin puede pasar store_id por query param
        qp = request.query_params.get("store_id")
        if qp and qp.isdigit():
            return int(qp)
        raise HTTPException(status_code=403, detail="No tienes una tienda asignada.")
    return int(scope["store_id"])


def _resolve_store_id_from_scope(request: Request, scope: dict[str, object]) -> int:
    store_id = scope.get("store_id")
    if store_id is None:
        qp = request.query_params.get("store_id")
        store_id = int(qp) if (qp and qp.isdigit()) else None
    if store_id is None:
        raise HTTPException(status_code=403, detail="No tienes una tienda asignada.")
    return int(store_id)


async def _json_body(request: Request) -> dict:
    try:
        return await request.json()
    except Exception:
        _log.exception("No se pudo decodificar JSON en %s %s", request.method, request.url.path)
        return {}


router.include_router(create_admin_api_router(_require_store_id, _json_body))


# ── Inicio Stats ─────────────────────────────────────────────────────────────

def api_inicio_stats(request: Request):
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        store_id = _resolve_store_id_from_scope(request, scope)
        return {"success": True, "data": analytics_service.get_cached_store_stats(db, store_id)}


async def api_update_store_configuration(request: Request):
    payload = await _json_body(request)
    raw_config = payload.get("config") if isinstance(payload.get("config"), dict) else payload
    _MULTITIENDA_PREFIX = "/multitienda"
    filtered_config: dict[str, object] = {}
    for key, value in (raw_config or {}).items():
        normalized_key = str(key or "").strip()
        if normalized_key not in _allowed_store_config_keys():
            continue
        if isinstance(value, bool):
            filtered_config[normalized_key] = value
        else:
            str_value = str(value or "")
            # Strip erroneous /multitienda prefix that _prefix_root_relative_urls may have injected
            if str_value.startswith(_MULTITIENDA_PREFIX + "/"):
                str_value = str_value[len(_MULTITIENDA_PREFIX):]
            filtered_config[normalized_key] = str_value

    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        if not _can_access_store_config(scope.get("role") or getattr(request.state, "user_role", "")):
            raise HTTPException(status_code=403, detail="Solo el administrador de la tienda puede ver y editar esta información.")
        store_id = _resolve_store_id_from_scope(request, scope)
        _log.warning("[PUT configuracion] store_id=%r role=%r payload_keys=%r filtered_keys=%r",
                     store_id, scope.get("role"), list((raw_config or {}).keys())[:5], list(filtered_config.keys())[:5])
        row = db.execute(
            text(
                """
                SELECT id, logo, banner, address, country, phone, store_theme
                FROM vendors
                WHERE id = :store_id
                LIMIT 1
                """
            ),
            {"store_id": store_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Tienda no encontrada.")
        theme = _decode_store_theme(row.get("store_theme"))
        theme["configuracion"] = {**_extract_store_config(theme), **filtered_config}
        db.execute(
            text(
                """
                UPDATE vendors
                SET logo = :logo,
                    banner = :banner,
                    phone = :phone,
                    address = :address,
                    country = :country,
                    store_theme = :store_theme,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :store_id
                """
            ),
            {
                "store_id": store_id,
                "logo": (
                    str(filtered_config.get("site_logo") or row.get("logo") or "")
                    if _fits_vendor_asset_column(filtered_config.get("site_logo") or row.get("logo"))
                    else str(row.get("logo") or "")
                ),
                "banner": (
                    str(filtered_config.get("landing_banner") or row.get("banner") or "")
                    if _fits_vendor_asset_column(filtered_config.get("landing_banner") or row.get("banner"))
                    else str(row.get("banner") or "")
                ),
                "phone": str(filtered_config.get("phone") or row.get("phone") or ""),
                "address": str(filtered_config.get("street") or row.get("address") or ""),
                "country": str(filtered_config.get("country") or row.get("country") or ""),
                "store_theme": json.dumps(theme, ensure_ascii=True),
            },
        )
        db.commit()
        result_data = _build_store_config_payload({"logo": filtered_config.get("site_logo") or row.get("logo"), "banner": filtered_config.get("landing_banner") or row.get("banner"), "phone": filtered_config.get("phone") or row.get("phone"), "address": filtered_config.get("street") or row.get("address"), "country": filtered_config.get("country") or row.get("country"), "store_theme": json.dumps(theme, ensure_ascii=True)})
        _log.warning("[PUT configuracion] committed ok store_id=%r result_data_keys=%r", store_id, list(result_data.keys())[:5])
        return {"success": True, "data": result_data}


def api_get_store_configuration(request: Request):
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        if not _can_access_store_config(scope.get("role") or getattr(request.state, "user_role", "")):
            raise HTTPException(status_code=403, detail="Solo el administrador de la tienda puede ver esta información.")
        store_id = _resolve_store_id_from_scope(request, scope)
        row = db.execute(
            text(
                """
                SELECT id, logo, banner, address, country, phone, store_theme
                FROM vendors
                WHERE id = :store_id
                LIMIT 1
                """
            ),
            {"store_id": store_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Tienda no encontrada.")
        return {"success": True, "data": _build_store_config_payload(row)}


# ── Productos privados (tienda) ──────────────────────────────────────────────

def api_list_store_products(request: Request):
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        store_id = _resolve_store_id_from_scope(request, scope)
        row = db.execute(
            text(
                """
                SELECT store_theme
                FROM vendors
                WHERE id = :store_id
                LIMIT 1
                """
            ),
            {"store_id": store_id},
        ).mappings().first()
        theme = _decode_store_theme(row.get("store_theme")) if row else {}
        return {"success": True, "data": _extract_catalog_products(theme)}


async def api_replace_store_products(request: Request):
    payload = await _json_body(request)
    incoming_products = payload.get("products") if isinstance(payload.get("products"), list) else payload
    if not isinstance(incoming_products, list):
        raise HTTPException(status_code=400, detail="Se esperaba una lista de productos.")

    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        store_id = _resolve_store_id_from_scope(request, scope)
        row = db.execute(
            text(
                """
                SELECT store_theme
                FROM vendors
                WHERE id = :store_id
                LIMIT 1
                """
            ),
            {"store_id": store_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Tienda no encontrada.")
        theme = _decode_store_theme(row.get("store_theme"))
        previous_products = _extract_catalog_products(theme)
        normalized_products = [dict(item) for item in incoming_products if isinstance(item, dict)]
        try:
            synced_products = _sync_catalog_products_to_marketplace(db, store_id, previous_products, normalized_products)
        except Exception:
            _log.exception("No se pudieron sincronizar los productos de la tienda %s con las tablas del marketplace.", store_id)
            # Fallback: conserva el catalogo dentro de store_theme para no bloquear la gestion del modulo.
            synced_products = normalized_products
        theme["catalog_products"] = synced_products
        db.execute(
            text(
                """
                UPDATE vendors
                SET store_theme = :store_theme,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :store_id
                """
            ),
            {"store_id": store_id, "store_theme": json.dumps(theme, ensure_ascii=True)},
        )
        db.commit()
        return {"success": True, "data": synced_products}


# ── Empleados ─────────────────────────────────────────────────────────────────

def api_list_employees(request: Request):
    with _request_db_context(request) as ctx:
        db = ctx["db"]
        scope = ctx["scope"]
        if not scope.get("user_id"):
            raise HTTPException(status_code=401, detail="No autenticado.")
        store_id = _resolve_store_id_from_scope(request, scope)
        return {"success": True, "data": employee_service.list_admin_rows(db, store_id)}


async def api_create_employee(request: Request):
    try:
        with _request_db_context(request, include_permissions=True) as ctx:
            db = ctx["db"]
            scope = ctx["scope"]
            store_perms = ctx["store_permissions"]
            if not scope.get("user_id"):
                raise HTTPException(status_code=401, detail="No autenticado.")
            store_id = _resolve_store_id_from_scope(request, scope)
            max_users = int(store_perms.get("max_internal_users") or 0)
            data = await _json_body(request)
            try:
                employee = employee_service.create_admin_employee(db, store_id, data, max_users=max_users)
            except ValueError as exc:
                code = str(exc)
                if code == "LIMIT_REACHED":
                    raise HTTPException(status_code=422, detail="LIMIT_REACHED")
                if code == "USERNAME_REQUIRED":
                    raise HTTPException(status_code=400, detail="El usuario es obligatorio.")
                if code == "PASSWORD_REQUIRED":
                    raise HTTPException(status_code=400, detail="La contraseña es obligatoria.")
                if code == "USERNAME_TAKEN":
                    raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso.")
                raise
            db.commit()
            return {"success": True, "data": employee}
    except HTTPException:
        raise
    except Exception:
        _log.exception("Error creando empleado")
        raise HTTPException(status_code=500, detail="Error interno al crear el empleado.")


async def api_update_employee(employee_id: int, request: Request):
    try:
        with _request_db_context(request) as ctx:
            db = ctx["db"]
            scope = ctx["scope"]
            store_id = _resolve_store_id_from_scope(request, scope)
            data = await _json_body(request)
            ok = employee_service.update_admin_employee(db, store_id, employee_id, data)
            if not ok:
                raise HTTPException(status_code=404, detail="Empleado no encontrado.")
            db.commit()
            return {"success": True}
    except HTTPException:
        raise
    except Exception:
        _log.exception("Error actualizando empleado")
        raise HTTPException(status_code=500, detail="Error interno al actualizar el empleado.")


def api_delete_employee(employee_id: int, request: Request):
    try:
        with _request_db_context(request) as ctx:
            db = ctx["db"]
            scope = ctx["scope"]
            store_id = _resolve_store_id_from_scope(request, scope)
            ok = employee_service.delete_admin_employee(db, store_id, employee_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Empleado no encontrado.")
            db.commit()
            return {"success": True}
    except HTTPException:
        raise
    except Exception:
        _log.exception("Error eliminando empleado")
        raise HTTPException(status_code=500, detail="Error interno al eliminar el empleado.")


async def api_change_employee_password(employee_id: int, request: Request):
    try:
        with _request_db_context(request) as ctx:
            db = ctx["db"]
            scope = ctx["scope"]
            store_id = _resolve_store_id_from_scope(request, scope)
            data = await _json_body(request)
            pwd = str(data.get("password") or "").strip()
            if not pwd:
                raise HTTPException(status_code=400, detail="La contraseña no puede estar vacía.")

            ok = employee_service.set_password_for_vendor_employee(db, store_id, employee_id, pwd)
            if not ok:
                raise HTTPException(status_code=404, detail="Empleado no encontrado.")
            db.commit()
            return {"success": True}
    except HTTPException:
        raise
    except Exception:
        _log.exception("Error cambiando contrasena de empleado id=%s", employee_id)
        raise HTTPException(status_code=500, detail="Error interno al cambiar la contraseña.")


router.include_router(
    create_store_admin_router(
        list_business_types=multitienda_business_types_proxy,
        create_business_type=multitienda_create_business_type_proxy,
        store_admin_users=multitienda_store_admin_users,
        memberships=multitienda_memberships,
        list_stores=multitienda_list_stores,
        save_store=multitienda_save_store,
        inicio_stats=api_inicio_stats,
        get_store_configuration=api_get_store_configuration,
        update_store_configuration=api_update_store_configuration,
    )
)
router.include_router(
    create_pages_router(
        render_official_shell=_render_official_shell,
        dispatch_section_entrypoint=_dispatch_section_entrypoint,
        inicio_html=inicio_html,
        configuracion_entrypoint=multitienda_config_entrypoint,
        productos_html=productos_html,
        tienda_html=tienda_html,
    )
)
router.include_router(
    create_products_router(
        list_store_products=api_list_store_products,
        replace_store_products=api_replace_store_products,
    )
)
router.include_router(
    create_employees_router(
        list_employees=api_list_employees,
        create_employee=api_create_employee,
        update_employee=api_update_employee,
        delete_employee=api_delete_employee,
        change_employee_password=api_change_employee_password,
    )
)
# Non-catch-all public routes (/tiendas, /carrito, /multitienda/api/..., etc.)
# The catch-all routes (/{store_slug}, /{store_slug}/{product_slug}) are registered
# in the 'late' phase via multitienda_catchall_late.py to avoid intercepting
# routes from other modules (e.g. /web/{slug} from the frontend module).
router.include_router(
    create_public_router(
        render_public_document=_render_public_document,
        public_store_exists=_public_store_exists,
        public_store_product_exists=_public_store_product_exists,
        render_not_found_template=render_not_found_template,
        tienda_html=tienda_html,
        carrito_html=carrito_html,
        public_landing_reserved=_PUBLIC_LANDING_RESERVED,
        load_public_store_info=_load_public_store_info,
        load_public_products=_load_public_products,
        require_store_id=_require_store_id,
    )
)


__all__ = ["bootstrap_multitienda", "router"]
