"""
controladores/frontend.py
─────────────────────────────────────────────────────────────────────────────
Constructor de páginas frontend + rutas públicas del sitio.

Mejoras aplicadas:
  • Caché de páginas con Redis (reemplaza dict in-memory)
  • Schemas Pydantic para validación automática en endpoints
  • Renderizado de páginas públicas con Jinja2
  • Sub-routers por dominio (pages, gallery, brand, contact, tasas, public)
  • Lógica de negocio extraída a funciones helper aisladas
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid as _uuid
from functools import lru_cache
from importlib import import_module
from typing import Any, Dict, List, Optional

import redis
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.module_registry import is_module_enabled
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    create_contact as store_create_contact,
    delete_page as store_delete_page,
    get_page as store_get_page,
    get_page_by_slug as store_get_page_by_slug,
    get_brand as store_get_brand,
    list_contacts as store_list_contacts,
    list_pages as store_list_pages,
    list_tasas as store_list_tasas,
    list_versions as store_list_versions,
    mark_contact_read as store_mark_contact_read,
    publish_page as store_publish_page,
    restore_version as store_restore_version,
    save_brand as store_save_brand,
    save_tasas as store_save_tasas,
    upsert_page as store_upsert_page,
)
from fastapi_modulo.modulos_sipet.frontend.servicios.render_service import render_page as render_public_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_user_app_access_level,
    get_user_backend_roles,
    get_user_screen_access_levels,
    normalize_role_name,
    require_app_access,
    require_screen_access,
)
from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import _load_login_identity
from fastapi_modulo.modulos_sipet.web.servicios.session_service import AUTH_COOKIE_NAME, read_session_cookie
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import get_login_identity_context
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context

logger = logging.getLogger(__name__)

# ── Router principal (agrupa todos los sub-routers) ───────────────────────────
router = APIRouter()

# ── Constantes de rutas ───────────────────────────────────────────────────────
_BUILDER_TEMPLATE = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "vistas", "frontend.html")
_GALLERY_DIR      = os.path.join("static", "gallery")

_GALLERY_MAX_MB   = 5

_FRONTEND_APP_NAME       = "Frontend"
_FRONTEND_BUILDER_SCREEN = "frontend.builder"

_RESERVED_SLUGS = {"", "descripcion", "funcionalidades", "login", "404", "passkey"}
_ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class PagePayload(BaseModel):
    """Schema para crear/actualizar una página desde el builder."""
    id: Optional[str] = None
    action: str = "upsert"
    title: str = Field(default="Sin título", min_length=1, max_length=255)
    slug: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|published)$")
    is_home: bool = False
    gjs_html: str = ""
    gjs_css: str = ""
    blocks: List[Any] = []
    meta: Dict[str, Any] = {}

    @field_validator("slug", mode="before")
    @classmethod
    def build_slug(cls, v: Any, info: Any) -> str:
        raw = str(v or info.data.get("title") or "pagina").strip().lower()
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in raw).strip("-")
        return slug or "pagina"

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: Any) -> str:
        return str(v or "Sin título").strip()


class ContactPayload(BaseModel):
    """Schema para el formulario de contacto público."""
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)
    message: str = Field(..., min_length=1, max_length=5000)

    @field_validator("name", "message", mode="before")
    @classmethod
    def strip_text_fields(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any) -> str:
        email = str(value or "").strip()
        if not _EMAIL_PATTERN.match(email):
            raise ValueError("Correo electrónico inválido")
        return email


class TasaItem(BaseModel):
    """Schema para un ítem de tasa de interés."""
    id: str
    label: str
    rate: str
    color: str = "#3b82f6"
    unit: str = "% anual"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — SERVICIO DE CACHÉ REDIS
# ══════════════════════════════════════════════════════════════════════════════

_CACHE_TTL = int(os.environ.get("PAGE_CACHE_TTL", "300"))   # segundos, default 5 min
_CACHE_PREFIX = "frontend:page:"


@lru_cache(maxsize=1)
def _get_redis() -> Optional[redis.Redis]:
    """
    Devuelve una instancia de Redis reutilizable.
    Retorna None si Redis no está configurado, permitiendo degradación
    silenciosa al comportamiento sin caché.
    """
    url = os.environ.get("REDIS_URL", "")
    if not url:
        logger.warning("REDIS_URL no configurado — caché de páginas desactivado.")
        return None
    try:
        client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception as exc:
        logger.warning("No se pudo conectar a Redis: %s — caché desactivado.", exc)
        return None


def _cache_get(key: str) -> Optional[str]:
    """Lee una clave del caché. Devuelve None si no existe o si Redis no está disponible."""
    r = _get_redis()
    if r is None:
        return None
    try:
        return r.get(f"{_CACHE_PREFIX}{key}")
    except Exception as exc:
        logger.debug("Redis GET falló: %s", exc)
        return None


def _cache_set(key: str, value: str) -> None:
    """Escribe en caché con TTL configurado."""
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(f"{_CACHE_PREFIX}{key}", _CACHE_TTL, value)
    except Exception as exc:
        logger.debug("Redis SET falló: %s", exc)


def _cache_delete(*keys: str) -> None:
    """Invalida una o varias claves del caché."""
    r = _get_redis()
    if r is None:
        return
    try:
        r.delete(*[f"{_CACHE_PREFIX}{k}" for k in keys])
    except Exception as exc:
        logger.debug("Redis DEL falló: %s", exc)


def _load_form_definition_model():
    for module_path in (
        "fastapi_modulo.modulos_sipet.plantillas.modelos.plantillas_db_models",
        "fastapi_modulo.modulos.plantillas.modelos.plantillas_db_models",
    ):
        try:
            module = import_module(module_path)
            return getattr(module, "FormDefinition", None)
        except Exception:
            continue
    return None


def clear_all_page_cache() -> None:
    """
    Borra todas las entradas del caché de páginas (ej. al cambiar brand colors).
    Usa SCAN para no bloquear Redis con KEYS *.
    """
    r = _get_redis()
    if r is None:
        return
    try:
        pattern = f"{_CACHE_PREFIX}*"
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor, match=pattern, count=200)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:
        logger.debug("Redis SCAN/DEL falló en clear_all: %s", exc)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — HELPERS DE ACCESO Y PERMISOS
# ══════════════════════════════════════════════════════════════════════════════

def _frontend_builder_access_level(request: Request) -> str:
    levels = get_user_screen_access_levels(request)
    for key in (_FRONTEND_BUILDER_SCREEN, _FRONTEND_APP_NAME, "__all__"):
        entry = levels.get(key) or {}
        if isinstance(entry, bool):
            return "full_access" if entry else "no_access"
        if not isinstance(entry, dict):
            continue
        for level_name in ("full_access", "special_permissions", "department_only", "user_only", "read_only"):
            if entry.get(level_name):
                return level_name
    return "no_access"


def _require_write(request: Request) -> None:
    """Eleva HTTPException 403 si el usuario no tiene permisos de escritura."""
    level = _frontend_builder_access_level(request)
    if level not in {"full_access", "special_permissions"}:
        raise HTTPException(status_code=403, detail="Sin permisos de edición en el constructor frontend.")


def _resolve_public_home_slug() -> str:
    pages = store_list_pages()
    home_page = next(
        (
            page for page in pages
            if bool(page.get("is_home")) and str(page.get("status") or "").strip() == "published" and str(page.get("slug") or "").strip()
        ),
        None,
    )
    if home_page:
        return str(home_page.get("slug") or "").strip() or "inicio"
    return "inicio"


def _is_public_frontend_page_path(path: str) -> bool:
    normalized = str(path or "").strip()
    if normalized in {"/web", "/web/"}:
        return True
    if normalized.startswith("/web/"):
        slug = (normalized[len("/web/"):] or "").strip().strip("/")
    elif normalized.startswith("/backend/"):
        slug = (normalized[len("/backend/"):] or "").strip().strip("/")
    else:
        return False
    if not slug or "/" in slug or slug in {"login", "404", "passkey"}:
        return False
    if slug in {"descripcion", "funcionalidades", "inicio"}:
        return True
    try:
        return bool(store_get_page_by_slug(slug, published_only=True))
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — SUB-ROUTER: BUILDER UI
# ══════════════════════════════════════════════════════════════════════════════

_builder_router = APIRouter(tags=["Builder"])


@_builder_router.get("/frontend/builder", response_class=HTMLResponse)
def frontend_builder(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    try:
        with open(_BUILDER_TEMPLATE, "r", encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    except OSError:
        return HTMLResponse("<h1>Template no encontrado</h1>", status_code=500)


@_builder_router.get("/api/backend/me")
def api_backend_me(request: Request):
    session_token = request.cookies.get(AUTH_COOKIE_NAME, "")
    session_data  = read_session_cookie(session_token) if session_token else None
    if not session_data:
        return {"authenticated": False, "is_superadmin": False, "backend_roles": [], "role": "", "username": ""}

    role       = normalize_role_name(session_data.get("role") or "")
    username   = (session_data.get("username") or "").strip()
    superadmin = role == "superadministrador"

    if not superadmin:
        request.state.user_name = username
        request.state.user_role = role
        backend_roles = get_user_backend_roles(request, username)
    else:
        backend_roles = ["editor", "designer"]

    app_level  = "full_access" if superadmin else get_user_app_access_level(request, _FRONTEND_APP_NAME)
    can_use_bar = superadmin or app_level != "no_access" or bool(backend_roles)

    bar_color = "#0f172a"
    try:
        colors = get_colores_context()
        if colors.get("sidebar-bottom"):
            bar_color = str(colors["sidebar-bottom"]).strip()
    except Exception:
        pass

    return {
        "authenticated":  can_use_bar,
        "is_superadmin":  superadmin,
        "backend_roles":  backend_roles,
        "role":           role,
        "username":       username,
        "builder_url":    "/frontend/builder",
        "bar_color":      bar_color,
    }


@_builder_router.get("/backend", response_class=HTMLResponse)
def backend(request: Request):
    del request
    return RedirectResponse(url="/web/inicio", status_code=307)


@_builder_router.get("/web", response_class=HTMLResponse)
def backend_alias_root(request: Request):
    del request
    return RedirectResponse(url="/web/inicio", status_code=307)


@_builder_router.get("/web/inicio", response_class=HTMLResponse)
def web_inicio(request: Request):
    target_slug = _resolve_public_home_slug()
    if target_slug != "inicio":
        return RedirectResponse(url=f"/web/{target_slug}", status_code=307)
    page = store_get_page_by_slug("inicio", published_only=True)
    if page:
        return render_public_page(page)
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/web_blank.html",
        {
            "request":                  request,
            "title":                    "SIPET",
            "app_favicon_url":          login_identity.get("login_favicon_url"),
            "company_logo_url":         login_identity.get("login_logo_url"),
            "login_company_short_name": login_identity.get("login_company_short_name"),
            "menu_position":            login_identity.get("menu_position"),
        },
    )


@_builder_router.get("/backend/descripcion", response_class=HTMLResponse)
def backend_descripcion(request: Request):
    del request
    return RedirectResponse(url="/web/descripcion", status_code=307)


@_builder_router.get("/web/descripcion", response_class=HTMLResponse)
def web_descripcion(request: Request):
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/web.html",
        {
            "request":         request,
            "title":           "SIPET",
            "app_favicon_url": login_identity.get("login_favicon_url"),
            "company_logo_url": login_identity.get("login_logo_url"),
            "menu_position":   login_identity.get("menu_position"),
        },
    )


@_builder_router.get("/backend/funcionalidades", response_class=HTMLResponse)
def backend_funcionalidades(request: Request):
    del request
    return RedirectResponse(url="/web/funcionalidades", status_code=307)


@_builder_router.get("/web/funcionalidades", response_class=HTMLResponse)
def web_funcionalidades(request: Request):
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/modulo_funcionalidades.html",
        {
            "request":         request,
            "title":           "Funcionalidades | SIPET",
            "app_favicon_url": login_identity.get("login_favicon_url"),
            "company_logo_url": login_identity.get("login_logo_url"),
            "menu_position":   login_identity.get("menu_position"),
        },
    )




# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — SUB-ROUTER: PÁGINAS (CRUD + PUBLICAR + VERSIONES)
# ══════════════════════════════════════════════════════════════════════════════

_pages_router = APIRouter(prefix="/api/frontend", tags=["Pages"])


@_pages_router.get("/pages")
def api_pages_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_pages()}


@_pages_router.get("/pages/{page_id}")
def api_page_get(request: Request, page_id: str):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    page = store_get_page(page_id)
    if not page:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    return {"success": True, "data": page}


@_pages_router.post("/pages")
async def api_pages_save(request: Request, payload: PagePayload):
    """
    Upsert o elimina una página del builder.
    Pydantic valida y sanitiza automáticamente el payload antes de llegar aquí.
    """
    _require_write(request)

    # ── Acción: eliminar ──────────────────────────────────────────────────────
    if payload.action == "delete":
        pid = str(payload.id or "")
        if not pid:
            return JSONResponse({"success": False, "error": "ID requerido para eliminar"}, status_code=400)
        return {"success": True, "data": store_delete_page(pid)}

    # ── Acción: upsert ────────────────────────────────────────────────────────
    pid   = str(payload.id or _uuid.uuid4())
    slug  = payload.slug or "pagina"

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

    page = {
        "id":       pid,
        "title":    payload.title,
        "slug":     slug,
        "status":   payload.status,
        "is_home":  payload.is_home,
        "gjs_html": payload.gjs_html,
        "gjs_css":  payload.gjs_css,
        "blocks":   payload.blocks,
        "meta":     payload.meta,
    }

    saved = store_upsert_page(page)
    _cache_delete(slug, f"backend:{slug}")
    return {"success": True, "data": saved["pages"], "page": saved["page"]}


@_pages_router.post("/pages/{page_id}/publish")
def api_page_publish(request: Request, page_id: str):
    """Publica una página e invalida su caché."""
    _require_write(request)
    page = store_publish_page(page_id)
    if not page:
        return JSONResponse({"success": False, "error": "No encontrado"}, status_code=404)
    slug = page.get("slug", "")
    _cache_delete(slug, f"backend:{slug}")
    return {"success": True, "page": page}


@_pages_router.get("/versions/{page_id}")
def api_versions_list(request: Request, page_id: str):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_versions(page_id)}


@_pages_router.post("/versions/{page_id}/restore/{version_idx}")
def api_version_restore(request: Request, page_id: str, version_idx: int):
    _require_write(request)
    versions = store_list_versions(page_id)
    if version_idx < 0 or version_idx >= len(versions):
        return JSONResponse({"success": False, "error": "Versión no encontrada"}, status_code=404)
    page = store_restore_version(page_id, version_idx)
    if not page:
        return JSONResponse({"success": False, "error": "Página no encontrada"}, status_code=404)
    slug = page.get("slug", "")
    _cache_delete(slug, f"backend:{slug}")
    return {"success": True, "page": page}


@_pages_router.get("/forms")
def api_list_forms(request: Request):
    """Lista formularios activos para el selector del builder."""
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    try:
        if not is_module_enabled("plantillas"):
            return {"success": True, "data": []}
        form_definition_model = _load_form_definition_model()
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


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — SUB-ROUTER: PÁGINAS PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

_public_router = APIRouter(tags=["Public Pages"])

_404_HTML = "<h1 style='font-family:sans-serif;padding:40px'>Página no encontrada</h1>"


@_public_router.get("/p/{slug}", response_class=HTMLResponse)
def public_page(slug: str):
    cached = _cache_get(slug)
    if cached:
        return HTMLResponse(cached)
    page = store_get_page_by_slug(slug, published_only=True)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    response = render_public_page(page)
    _cache_set(slug, response.body.decode("utf-8"))
    return response


@_public_router.get("/backend/{slug}", response_class=HTMLResponse)
def public_page_backend(slug: str):
    """Alias legacy: redirige páginas públicas de /backend/<slug> a /web/<slug>."""
    return RedirectResponse(url=f"/web/{slug}", status_code=307)


@_public_router.get("/web/{slug}", response_class=HTMLResponse)
def public_page_web_alias(slug: str):
    cache_key = f"web:{slug}"
    cached = _cache_get(cache_key)
    if cached:
        return HTMLResponse(cached)
    page = store_get_page_by_slug(slug, published_only=True)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    response = render_public_page(page)
    _cache_set(cache_key, response.body.decode("utf-8"))
    return response


@_public_router.get("/p-preview/{slug}", response_class=HTMLResponse)
def preview_page(slug: str):
    """Preview de borrador — sin caché, accesible desde el builder."""
    page = store_get_page_by_slug(slug, published_only=False)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    return render_public_page(page)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — SUB-ROUTER: TASAS DE INTERÉS
# ══════════════════════════════════════════════════════════════════════════════

_tasas_router = APIRouter(prefix="/api/frontend", tags=["Tasas"])


@_tasas_router.get("/tasas")
def api_tasas_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_tasas()}


@_tasas_router.post("/tasas")
async def api_tasas_save(request: Request, tasas: List[TasaItem]):
    """
    Guarda la lista de tasas.
    Pydantic valida que cada elemento tenga id, label y rate.
    """
    _require_write(request)
    data = [t.model_dump() for t in tasas]
    return {"success": True, "data": store_save_tasas(data)}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — SUB-ROUTER: FORMULARIO DE CONTACTO
# ══════════════════════════════════════════════════════════════════════════════

_contact_router = APIRouter(prefix="/api/frontend", tags=["Contact"])


@_contact_router.post("/contact")
async def api_contact_submit(payload: ContactPayload):
    """
    Recibe un mensaje de contacto del sitio público.
    Pydantic valida name, email (formato) y message automáticamente.
    No requiere autenticación — es un endpoint público.
    """
    store_create_contact(
        id=str(_uuid.uuid4()),
        name=payload.name,
        email=payload.email,
        message=payload.message,
    )
    return {"success": True, "message": "Mensaje recibido, gracias."}


@_contact_router.get("/contact")
def api_contact_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_contacts()}


@_contact_router.post("/contact/{contact_id}/read")
def api_contact_mark_read(request: Request, contact_id: str):
    _require_write(request)
    if not store_mark_contact_read(contact_id):
        return JSONResponse({"success": False, "error": "Mensaje no encontrado"}, status_code=404)
    return {"success": True}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10 — SUB-ROUTER: GALERÍA DE IMÁGENES
# ══════════════════════════════════════════════════════════════════════════════

_gallery_router = APIRouter(prefix="/api/frontend", tags=["Gallery"])


def _gallery_items() -> List[Dict]:
    os.makedirs(_GALLERY_DIR, exist_ok=True)
    return [
        {"filename": fname, "url": f"/static/gallery/{fname}"}
        for fname in sorted(os.listdir(_GALLERY_DIR))
        if os.path.splitext(fname)[1].lower() in _ALLOWED_IMAGE_EXTS
    ]


@_gallery_router.get("/gallery")
def api_gallery_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": _gallery_items()}


@_gallery_router.post("/gallery/upload")
async def api_gallery_upload(request: Request):
    _require_write(request)
    upload = None
    form_error = None
    form_debug: list[str] = []
    try:
        form = await request.form()
        for _, value in form.multi_items():
            form_debug.append(f"{type(value).__name__}:{getattr(value, 'filename', '') or getattr(value, '__class__', type(value)).__name__}")
            if getattr(value, "filename", None):
                upload = value
                break
    except Exception as exc:
        form_error = str(exc) or exc.__class__.__name__
        logger.exception("frontend gallery upload: failed to parse multipart form")
        upload = None
    if upload is None or not getattr(upload, "filename", None):
        error_message = "No se recibió ninguna imagen multipart en la solicitud."
        if form_error:
            error_message = f"{error_message} Detalle: {form_error}"
        content_type = request.headers.get("content-type") or "(sin content-type)"
        content_length = request.headers.get("content-length") or "(sin content-length)"
        debug_fields = ", ".join(form_debug) if form_debug else "(sin campos parseados)"
        error_message = (
            f"{error_message} Content-Type: {content_type}. "
            f"Content-Length: {content_length}. Campos: {debug_fields}."
        )
        return JSONResponse(
            {"success": False, "error": error_message},
            status_code=400,
        )
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        return JSONResponse(
            {"success": False, "error": f"Tipo no permitido. Usa: {', '.join(_ALLOWED_IMAGE_EXTS)}"},
            status_code=415,
        )
    data = await upload.read()
    if len(data) > _GALLERY_MAX_MB * 1024 * 1024:
        return JSONResponse(
            {"success": False, "error": f"Imagen demasiado grande (máx {_GALLERY_MAX_MB} MB)"},
            status_code=413,
        )
    # Optimizar con Pillow si está disponible
    try:
        from fastapi_modulo.core.image_utils import optimize_image
        data, ext = optimize_image(data, ext, profile="asset")
    except Exception:
        pass  # Si falla, guarda el original

    os.makedirs(_GALLERY_DIR, exist_ok=True)
    safe_name = f"{_uuid.uuid4().hex}{ext}"
    with open(os.path.join(_GALLERY_DIR, safe_name), "wb") as fh:
        fh.write(data)
    return {"success": True, "filename": safe_name, "url": f"/static/gallery/{safe_name}"}


@_gallery_router.delete("/gallery/{filename}")
def api_gallery_delete(request: Request, filename: str):
    _require_write(request)
    safe = os.path.basename(filename)   # CORREGIDO: era os.path.MAINname (bug)
    path = os.path.join(_GALLERY_DIR, safe)
    if os.path.isfile(path):
        os.remove(path)
        return {"success": True}
    return JSONResponse({"success": False, "error": "Archivo no encontrado"}, status_code=404)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 11 — SUB-ROUTER: BRAND (COLORES + LOGO)
# ══════════════════════════════════════════════════════════════════════════════

_brand_router = APIRouter(prefix="/api/frontend", tags=["Brand"])


def _resolve_identidad_logo_url() -> str:
    """
    Prioridad de logo:
      1) Logo subido en Identidad institucional
      2) Logo en Personalización
    """
    import glob as _glob
    from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import _build_login_asset_url

    try:
        data = _load_login_identity()
        logo_filename = str(data.get("logo_filename") or "").strip()
        if logo_filename and logo_filename != "icon.png":
            return _build_login_asset_url(logo_filename, "icon.png")
    except Exception:
        pass

    _UPLOADS = os.path.join("fastapi_modulo", "modulos", "personalizacion", "uploads")
    candidates = sorted(
        _glob.glob(os.path.join(_UPLOADS, "logo_empresa.*")),
        key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
        reverse=True,
    )
    if candidates:
        fname = os.path.basename(candidates[0])   # CORREGIDO: era os.path.MAINname (bug)
        v = int(os.path.getmtime(candidates[0])) if os.path.exists(candidates[0]) else 0
        return f"/personalizar/uploads/{fname}?v={v}"
    return ""


@_brand_router.get("/brand")
def api_brand_get(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    brand = store_get_brand()
    brand["identidad_logo_url"] = _resolve_identidad_logo_url()
    return {"success": True, "data": brand}


@_brand_router.post("/brand")
async def api_brand_save(request: Request):
    _require_write(request)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "JSON inválido"}, status_code=400)
    brand = store_save_brand({k: v for k, v in body.items() if isinstance(v, str)})
    clear_all_page_cache()
    return {"success": True, "data": brand}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 12 — REGISTRO DE TODOS LOS SUB-ROUTERS EN EL ROUTER PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

router.include_router(_builder_router)
router.include_router(_pages_router)
router.include_router(_public_router)
router.include_router(_tasas_router)
router.include_router(_contact_router)
router.include_router(_gallery_router)
router.include_router(_brand_router)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 12 — SCRIPT DE WIDGET DE FORMULARIO (inyectado en páginas públicas)
# ══════════════════════════════════════════════════════════════════════════════

_FORM_WIDGET_SCRIPT = """
<script>
(function(){
  'use strict';
  function _e(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function _field(f,slug){
    var id='sfw-'+slug+'-'+f.name;
    var b='width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;outline:none;';
    var fc='onFocus="this.style.borderColor=\'#3b82f6\'" onBlur="this.style.borderColor=\'#d1d5db\'";';
    if(f.type==='divider') return '<hr style="border:none;border-top:1px solid #e5e7eb;margin:4px 0;">';
    if(f.type==='header')  return '<h3 style="font-size:1.1rem;font-weight:700;color:#111827;">'+_e(f.label||'')+'</h3>';
    if(f.type==='paragraph') return '<p style="font-size:14px;color:#64748b;line-height:1.6;">'+_e(f.label||'')+'</p>';
    var w='<div style="display:flex;flex-direction:column;gap:5px;">';
    if(f.type!=='checkbox'){
      w+='<label for="'+_e(id)+'" style="font-size:13px;font-weight:600;color:#374151;">'+_e(f.label||f.name)+(f.required?' <span style="color:#ef4444">*</span>':'')+'</label>';
    }
    if(f.type==='textarea'){
      w+='<textarea id="'+_e(id)+'" name="'+_e(f.name)+'" rows="4" placeholder="'+_e(f.placeholder||'')+'" style="'+b+'resize:vertical;" '+fc+(f.required?' required':'')+'></textarea>';
    } else if(f.type==='select'){
      w+='<select id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
        +'<option value="">-- Seleccionar --</option>';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<option value="'+_e(v)+'">'+_e(l)+'</option>';});
      w+='</select>';
    } else if(f.type==='radio'){
      w+='<div style="display:flex;flex-direction:column;gap:8px;">';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="radio" name="'+_e(f.name)+'" value="'+_e(v)+'"'+(f.required?' required':'')+'>'+_e(l)+'</label>';});
      w+='</div>';
    } else if(f.type==='checkboxes'){
      w+='<div style="display:flex;flex-direction:column;gap:8px;">';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="checkbox" name="'+_e(f.name)+'" value="'+_e(v)+'">'+_e(l)+'</label>';});
      w+='</div>';
    } else if(f.type==='checkbox'){
      w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="checkbox" id="'+_e(id)+'" name="'+_e(f.name)+'" value="1"'+(f.required?' required':'')+'>'+_e(f.label||f.name)+'</label>';
    } else if(f.type==='date'){
      w+='<input type="date" id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    } else if(f.type==='time'){
      w+='<input type="time" id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    } else {
      var t=(f.type==='email'||f.type==='url'||f.type==='number'||f.type==='integer'||f.type==='decimal')? f.type.replace('integer','number').replace('decimal','number') : 'text';
      w+='<input type="'+t+'" id="'+_e(id)+'" name="'+_e(f.name)+'" placeholder="'+_e(f.placeholder||'')+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    }
    if(f.helpText) w+='<span style="font-size:11px;color:#64748b;">'+_e(f.helpText)+'</span>';
    w+='</div>';
    return w;
  }
  function _render(data,el){
    var cfg=data.config||{};
    var pc=cfg.primary_color||'#3b82f6';
    var lbl=cfg.submit_label||'Enviar';
    var ok=cfg.success_message||'¡Gracias! Tu respuesta fue enviada.';
    var h='<form data-slug="'+_e(data.slug)+'" novalidate style="display:flex;flex-direction:column;gap:18px;">';
    if(data.name) h+='<h2 style="font-size:1.4rem;font-weight:800;color:#111827;">'+_e(data.name)+'</h2>';
    if(data.description) h+='<p style="font-size:14px;color:#64748b;margin-top:-10px;line-height:1.6;">'+_e(data.description)+'</p>';
    (data.fields||[]).forEach(function(f){h+=_field(f,data.slug);});
    h+='<div style="display:flex;align-items:center;gap:12px;"><button type="submit" style="padding:12px 28px;background:'+_e(pc)+';color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;">'+_e(lbl)+'</button><span class="_sfw_msg" style="display:none;font-size:13px;"></span></div>';
    h+='</form>';
    el.innerHTML=h;
    el.querySelector('form').addEventListener('submit',function(ev){
      ev.preventDefault();
      var btn=this.querySelector('button[type=submit]'),msg=this.querySelector('._sfw_msg'),fd={};
      new FormData(this).forEach(function(v,k){fd[k]=v;});
      if(btn)btn.disabled=true;
      fetch('/api/forms/'+encodeURIComponent(data.slug)+'/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(fd),credentials:'include'})
        .then(function(r){return r.json();})
        .then(function(j){
          if(j.success){
            el.innerHTML='<div style="padding:24px;background:#ecfdf5;border-radius:10px;color:#065f46;font-weight:600;text-align:center;font-size:15px;">&#10003; '+_e(ok)+'</div>';
          } else {
            if(msg){msg.style.display='inline';msg.style.color='#b91c1c';msg.textContent=j.error||'Error al enviar';}
            if(btn)btn.disabled=false;
          }
        }).catch(function(){
          if(msg){msg.style.display='inline';msg.style.color='#b91c1c';msg.textContent='Error de conexión';}
          if(btn)btn.disabled=false;
        });
    });
  }
  function init(){
    document.querySelectorAll('.sipet-form-widget[data-slug]').forEach(function(el){
      var slug=el.dataset.slug;
      if(!slug){el.innerHTML='<p style="color:#94a3b8;padding:16px;font-style:italic;">Formulario sin configurar</p>';return;}
      el.innerHTML='<p style="color:#94a3b8;font-size:13px;padding:16px;text-align:center;">&#8987; Cargando formulario…</p>';
      fetch('/api/forms/'+encodeURIComponent(slug),{credentials:'include'})
        .then(function(r){return r.json();})
        .then(function(j){
          if(!j.success||!j.data){el.innerHTML='<p style="color:#ef4444;padding:16px;font-size:13px;">Formulario &ldquo;'+_e(slug)+'&rdquo; no encontrado</p>';return;}
          _render(j.data,el);
        }).catch(function(){el.innerHTML='<p style="color:#ef4444;padding:16px;font-size:13px;">Error al cargar formulario</p>';});
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
})();
</script>"""
