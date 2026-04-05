"""
controladores/pages_controller.py
─────────────────────────────────────────────────────────────────────────────
CRUD de páginas, publicación, versiones y formularios del builder frontend.

Rutas:
  GET    /api/frontend/pages
  GET    /api/frontend/pages/{page_id}
  POST   /api/frontend/pages
  POST   /api/frontend/pages/{page_id}/publish
  GET    /api/frontend/versions/{page_id}
  POST   /api/frontend/versions/{page_id}/restore/{version_idx}
  GET    /api/frontend/forms
"""

from __future__ import annotations

import logging
import uuid as _uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.module_registry import is_module_enabled
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_schemas import PagePayload
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    delete_page as store_delete_page,
    get_brand as store_get_brand,
    get_page as store_get_page,
    list_pages as store_list_pages,
    list_versions as store_list_versions,
    publish_page as store_publish_page,
    restore_version as store_restore_version,
    save_brand as store_save_brand,
    upsert_page as store_upsert_page,
)
from fastapi_modulo.modulos_sipet.frontend.servicios import cache_service
from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
from fastapi_modulo.modulos_sipet.frontend.servicios.layout_service import (
    extract_global_layout_segments,
    merge_global_layout,
)
from fastapi_modulo.modulos_sipet.frontend.servicios.page_service import load_form_definition_model
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/frontend", tags=["Pages"])

_FRONTEND_BUILDER_SCREEN = "frontend.builder"
_RESERVED_SLUGS = {"", "descripcion", "funcionalidades", "login", "404", "passkey"}


@router.get("/pages")
def api_pages_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    pages = store_list_pages()
    brand = store_get_brand()
    global_nav    = brand.get("global_nav_html") or ""
    global_footer = brand.get("global_footer_html") or ""
    data = []
    for page in pages:
        item = dict(page)
        item["gjs_html"] = merge_global_layout(item.get("gjs_html") or "", global_nav, global_footer)
        data.append(item)
    return {"success": True, "data": data}


@router.get("/pages/{page_id}")
def api_page_get(request: Request, page_id: str):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    page = store_get_page(page_id)
    if not page:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    brand = store_get_brand()
    page = dict(page)
    page["gjs_html"] = merge_global_layout(
        page.get("gjs_html") or "",
        brand.get("global_nav_html") or "",
        brand.get("global_footer_html") or "",
    )
    return {"success": True, "data": page}


@router.post("/pages")
async def api_pages_save(request: Request, payload: PagePayload):
    """
    Upsert o elimina una página del builder.
    Pydantic valida y sanitiza el payload antes de llegar aquí.
    """
    require_write(request)

    # ── Acción: eliminar ──────────────────────────────────────────────────────
    if payload.action == "delete":
        pid = str(payload.id or "")
        if not pid:
            return JSONResponse({"success": False, "error": "ID requerido para eliminar"}, status_code=400)
        return {"success": True, "data": store_delete_page(pid)}

    # ── Acción: upsert ────────────────────────────────────────────────────────
    pid  = str(payload.id or _uuid.uuid4())
    slug = payload.slug or "pagina"

    if slug in _RESERVED_SLUGS:
        return JSONResponse(
            {"success": False, "error": f'La ruta "/backend/{slug}" está reservada. Usa otro slug.'},
            status_code=400,
        )

    pages     = store_list_pages()
    duplicate = next((p for p in pages if p.get("slug") == slug and p.get("id") != pid), None)
    if duplicate:
        return JSONResponse(
            {"success": False, "error": f'Ya existe otra página con la ruta "/backend/{slug}".'},
            status_code=400,
        )

    body_html, global_nav, global_footer = extract_global_layout_segments(payload.gjs_html)
    if global_nav or global_footer:
        store_save_brand({
            "global_nav_html":    global_nav,
            "global_footer_html": global_footer,
        })

    page = {
        "id":       pid,
        "title":    payload.title,
        "slug":     slug,
        "status":   payload.status,
        "is_home":  payload.is_home,
        "gjs_html": body_html,
        "gjs_css":  payload.gjs_css,
        "blocks":   payload.blocks,
        "meta":     payload.meta.model_dump(exclude_none=True),
    }

    saved        = store_upsert_page(page)
    brand_layout = store_get_brand()

    pages_response = []
    for item in saved["pages"]:
        page_item = dict(item)
        page_item["gjs_html"] = merge_global_layout(
            page_item.get("gjs_html") or "",
            brand_layout.get("global_nav_html") or "",
            brand_layout.get("global_footer_html") or "",
        )
        pages_response.append(page_item)

    page_response = dict(saved["page"])
    page_response["gjs_html"] = merge_global_layout(
        page_response.get("gjs_html") or "",
        brand_layout.get("global_nav_html") or "",
        brand_layout.get("global_footer_html") or "",
    )
    cache_service.delete(slug, f"backend:{slug}")
    return {"success": True, "data": pages_response, "page": page_response}


@router.post("/pages/{page_id}/publish")
def api_page_publish(request: Request, page_id: str):
    """Publica una página e invalida su caché."""
    require_write(request)
    page = store_publish_page(page_id)
    if not page:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    slug = page.get("slug", "")
    cache_service.delete(slug, f"backend:{slug}")
    return {"success": True, "page": page}


@router.get("/versions/{page_id}")
def api_versions_list(request: Request, page_id: str):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_versions(page_id)}


@router.post("/versions/{page_id}/restore/{version_idx}")
def api_version_restore(request: Request, page_id: str, version_idx: int):
    require_write(request)
    versions = store_list_versions(page_id)
    if version_idx < 0 or version_idx >= len(versions):
        return JSONResponse({"success": False, "error": "Versión no encontrada"}, status_code=404)
    page = store_restore_version(page_id, version_idx)
    if not page:
        return JSONResponse({"success": False, "error": "Página no encontrada"}, status_code=404)
    slug = page.get("slug", "")
    cache_service.delete(slug, f"backend:{slug}")
    return {"success": True, "page": page}


@router.get("/forms")
def api_list_forms(request: Request):
    """Lista formularios activos para el selector del builder."""
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    try:
        if not is_module_enabled("plantillas"):
            return {"success": True, "data": []}
        form_definition_model = load_form_definition_model()
        if form_definition_model is None:
            return {"success": True, "data": []}
        db = core_db.get_session_factory_for_host(core_db.get_request_host())()
        try:
            forms = (
                db.query(form_definition_model)
                .filter(form_definition_model.is_active == True)  # noqa: E712
                .order_by(form_definition_model.name)
                .all()
            )
            return {"success": True, "data": [{"id": f.id, "name": f.name, "slug": f.slug} for f in forms]}
        finally:
            db.close()
    except Exception as exc:
        return JSONResponse({"success": False, "data": [], "error": str(exc)}, status_code=500)
