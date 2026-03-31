from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos.multitienda.__manifest__ import MANIFEST
from fastapi_modulo.modulos.multitienda.controladores.multitienda import (
    _MODULE_SECTIONS,
    _build_marketplace_shell_content,
    _cached_management_shell_content,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.core import db as marketplace_db


MODULE_ROOT = Path(__file__).resolve().parents[1]


def test_multitienda_uses_sipet_core_db() -> None:
    db_source = (MODULE_ROOT / "marketplace" / "backend" / "core" / "db.py").read_text(encoding="utf-8")

    assert "create_engine" not in db_source
    assert "sessionmaker" not in db_source
    assert marketplace_db.SessionLocal is not None
    assert marketplace_db.engine is not None


def test_multitienda_manifest_declares_module_assets() -> None:
    assets = MANIFEST.get("assets") or {}
    declared_css = set(assets.get("css") or [])
    declared_js = set(assets.get("js") or [])

    css_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.css")
        if "tests" not in path.parts
    }
    js_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.js")
        if "tests" not in path.parts
    }

    assert css_files.issubset(declared_css)
    assert js_files.issubset(declared_js)


def test_multitienda_manifest_declares_runtime_dependencies() -> None:
    depends = set(MANIFEST.get("depends") or [])

    assert "web" in depends
    assert "identidad_institucional" in depends
    assert "aplicaciones" in depends
    assert "referidos" not in depends


def test_multitienda_removes_orphan_backend_logic() -> None:
    orphan_paths = [
        "marketplace/backend/apps/analytics/api.py",
        "marketplace/backend/apps/catalog/routes_filters.py",
        "marketplace/backend/apps/catalog/routes_full.py",
        "marketplace/backend/apps/catalog/routes_public.py",
        "marketplace/backend/apps/commissions/utils.py",
        "marketplace/backend/apps/domains/api.py",
        "marketplace/backend/apps/domains/middleware.py",
        "marketplace/backend/apps/domains/storefront_api.py",
        "marketplace/backend/apps/messaging/api.py",
        "marketplace/backend/apps/orders/routes_checkout.py",
        "marketplace/backend/apps/products/routes_vendor.py",
        "marketplace/backend/apps/products/routes_vendor_attributes.py",
        "marketplace/backend/apps/products/routes_vendor_dashboard.py",
        "marketplace/backend/apps/products/routes_vendor_images.py",
        "marketplace/backend/apps/products/routes_vendor_variants.py",
        "marketplace/backend/apps/vendors/api.py",
        "marketplace/backend/apps/vendors/models_api.py",
        "marketplace/backend/apps/vendors/routes_multitenant.py",
        "marketplace/backend/apps/vendors/schemas_api.py",
        "marketplace/backend/apps/vendors/utils.py",
    ]

    for relative_path in orphan_paths:
        assert not (MODULE_ROOT / relative_path).exists(), relative_path


def test_multitienda_management_section_uses_updated_label_and_cached_notebook_shell() -> None:
    assert _MODULE_SECTIONS[-1] == {
        "id": "gestion",
        "label": "Administración de tiendas",
        "icon": "fa-solid fa-store",
        "route": "/multitienda/administracion_tiendas",
    }

    content = _cached_management_shell_content()

    assert "Administrar tiendas" in content
    assert "multitienda-shell__sidebar" in content
    assert "multitienda-shell__hero" in content
    assert 'fetch(\'/multitienda/api/stores\'' in content
    assert ".multitienda-official-view .notebook-tab.active" in content
    assert '<button class="notebook-tab active"' in content
    assert "/multitienda/api/business-types" in content
    assert "/multitienda/api/memberships" in content
    assert "/multitienda/api/usuarios" not in content
    assert "/multitienda/multitienda/api/business-types" not in content
    assert "/multitienda/multitienda/api/memberships" not in content
    assert "__USERS_PATH__" not in content
    assert "showStoreErrorDialog" in content
    assert "copyStoreErrorText" in content
    assert "store_id: editIndex >= 0 && stores[editIndex] ? stores[editIndex].id : \"\"" in content
    assert 'fetch("/api/usuarios"' in content
    assert "adminSelect.disabled = false;" in content


def test_multitienda_dashboard_summary_is_only_rendered_on_inicio() -> None:
    inicio_content = _build_marketplace_shell_content(
        "<main><section>inicio</section></main>",
        "inicio",
        sections=list(_MODULE_SECTIONS),
        viewer_name="Demo",
    )
    productos_content = _build_marketplace_shell_content(
        "<main><section>productos</section></main>",
        "productos",
        sections=list(_MODULE_SECTIONS),
        viewer_name="Demo",
    )

    assert "Dashboard de tienda" in inicio_content
    assert "Dashboard de tienda" not in productos_content
    assert '<section class="multitienda-shell__hero">' not in productos_content


def test_multitienda_main_is_thin_bootstrap() -> None:
    controller_source = (MODULE_ROOT / "controladores" / "marketplace_backend.py").read_text(encoding="utf-8")
    entrypoint_source = (MODULE_ROOT / "controladores" / "multitienda.py").read_text(encoding="utf-8")
    manifest_backend = (((MANIFEST.get("structure") or {}).get("backend")) or [])
    manifest_router = (((MANIFEST.get("structure") or {}).get("router")) or [])

    assert "controladores/marketplace_backend.py" in manifest_router
    assert "marketplace/backend/main.py" not in manifest_backend
    assert not (MODULE_ROOT / "marketplace" / "backend" / "main.py").exists()
    assert "@marketplace_router.post" in controller_source
    assert "INSERT INTO vendors" in controller_source
    assert "store_business_types" in controller_source
    assert "store_id_raw" in controller_source
    assert "GENERATED BY DEFAULT AS IDENTITY" in entrypoint_source
    assert "referidos_html()" not in entrypoint_source
