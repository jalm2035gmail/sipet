from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi_modulo.modulos.web.servicios.module_tools import (
    read_text_file,
    render_backend_page_html,
    render_no_access_page,
    require_app_access,
    text_asset_response,
)

from fastapi_modulo.modulos.auditoria.modelos.aud_models import (
    AuditoriaCreate,
    AuditoriaUpdate,
    HallazgoCreate,
    HallazgoUpdate,
    RecomendacionCreate,
    RecomendacionUpdate,
    SeguimientoCreate,
)
from fastapi_modulo.modulos.auditoria.modelos.aud_store import (
    create_auditoria,
    create_hallazgo,
    create_recomendacion,
    create_seguimiento,
    delete_auditoria,
    delete_hallazgo,
    delete_recomendacion,
    delete_seguimiento,
    get_aud_resumen,
    get_auditoria,
    get_hallazgo,
    get_recomendacion,
    list_auditorias,
    list_hallazgos,
    list_recomendaciones,
    list_seguimiento,
    update_auditoria,
    update_hallazgo,
    update_recomendacion,
)

_MODULE_DIR = Path(__file__).resolve().parents[1]
_VIEWS_DIR = _MODULE_DIR / "vistas"
_STATIC_CSS_DIR = _MODULE_DIR / "static" / "css"
_STATIC_JS_DIR = _MODULE_DIR / "static" / "js"
_STATIC_DESCRIPTION_DIR = _MODULE_DIR / "static" / "description"
_AUDITORIA_APP_NAME = "Auditoria"


def _require_auditoria_access(request: Request) -> None:
    require_app_access(request, "Auditoria", "Acceso restringido al módulo Auditoría")


router = APIRouter(dependencies=[Depends(_require_auditoria_access)])


def _get_auditoria_access_level(request: Request) -> str:
    try:
        from fastapi_modulo.main import (
            SessionLocal,
            Usuario,
            _get_user_app_access,
            _sensitive_lookup_hash,
            is_admin_or_superadmin,
            is_app_access_enabled,
        )
    except ImportError:
        from fastapi_modulo.main import _get_user_app_access, is_admin_or_superadmin

        if is_admin_or_superadmin(request):
            return "full_access"
        if "Auditoria" in _get_user_app_access(request):
            return "full_access"
        return ""
    import json as _json

    if is_admin_or_superadmin(request):
        return "full_access"
    if not is_app_access_enabled(_AUDITORIA_APP_NAME):
        return ""
    try:
        username = getattr(request.state, "user_name", None) or ""
        if not username:
            return ""
        lookup_hash = _sensitive_lookup_hash(username)
        db = SessionLocal()
        try:
            user = db.query(Usuario).filter(Usuario.usuario_hash == lookup_hash).first()
            if not user:
                return ""
            user_id = str(user.id)
        finally:
            db.close()

        app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
        sipet_data_dir = (os.environ.get("SIPET_DATA_DIR") or os.path.expanduser("~/.sipet/data")).strip()
        runtime_dir = (os.environ.get("RUNTIME_STORE_DIR") or os.path.join(sipet_data_dir, "runtime_store", app_env)).strip()
        meta_path = os.environ.get("COLAB_META_PATH") or os.path.join(runtime_dir, "colaboradores_meta.json")
        if not os.path.exists(meta_path):
            return ""
        raw = _json.loads(Path(meta_path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return ""
        entry = raw.get(user_id, {})
        if not isinstance(entry, dict):
            return ""
        app_access_levels = entry.get("app_access_levels", {})
        if isinstance(app_access_levels, dict):
            levels = app_access_levels.get(_AUDITORIA_APP_NAME, {})
            if isinstance(levels, dict):
                for level_key in ("full_access", "read_only", "department_only", "user_only", "special_permissions"):
                    if bool(levels.get(level_key, False)):
                        return level_key
        direct_access = entry.get("app_access", [])
        if isinstance(direct_access, list):
            for item in direct_access:
                if str(item).strip().lower() == _AUDITORIA_APP_NAME.lower():
                    return "full_access"
        return ""
    except Exception:
        return ""


def _auditoria_permissions(request: Request) -> Dict[str, bool]:
    level = _get_auditoria_access_level(request)
    permissions = {
        "view_auditorias": False,
        "create_auditorias": False,
        "edit_auditorias": False,
        "delete_auditorias": False,
        "register_hallazgos": False,
        "register_seguimiento": False,
        "close_recomendaciones": False,
    }
    if level == "full_access":
        return {key: True for key in permissions}
    if level in {"read_only", "department_only", "user_only", "special_permissions"}:
        permissions["view_auditorias"] = True
    if level == "special_permissions":
        permissions["register_hallazgos"] = True
        permissions["register_seguimiento"] = True
        permissions["close_recomendaciones"] = True
    return permissions


def _require_auditoria_permission(request: Request, permission: str) -> None:
    permissions = _auditoria_permissions(request)
    if not permissions.get(permission, False):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para realizar esta acción en Auditoría.",
        )


def _render_no_access_auditoria_page(
    request: Request,
    *,
    title: str,
    description: str,
) -> HTMLResponse:
    return render_no_access_page(
        request,
        title=title,
        description=description,
    )


# ── Vista HTML ────────────────────────────────────────────────────────────────

@router.get("/auditoria", response_class=HTMLResponse)
def auditoria_page(request: Request):
    html_path = _VIEWS_DIR / "auditoria.html"
    menus_path = _VIEWS_DIR / "auditoria_menus.html"
    content = read_text_file(html_path, "<p>No se pudo cargar la vista de auditoria.</p>")
    menus_content = read_text_file(menus_path, "")
    content = content.replace("<!-- AUDITORIA_MODULE_MENUS -->", menus_content)
    return render_backend_page_html(
        request,
        title="Auditoría",
        description="Gestión de auditorías, hallazgos, recomendaciones y seguimiento.",
        content=content,
        show_page_header=False,
    )


# ── JS asset ──────────────────────────────────────────────────────────────────

@router.get("/api/auditoria/assets/auditoria.css")
def auditoria_css():
    return text_asset_response(
        _STATIC_CSS_DIR / "auditoria.css",
        media_type="text/css",
        fallback="/* auditoria css no disponible */",
    )


@router.get("/api/auditoria/assets/auditoria.js")
def auditoria_js():
    return text_asset_response(
        _STATIC_JS_DIR / "auditoria.js",
        media_type="application/javascript",
        fallback="console.error('Auditoria JS no disponible');",
    )


@router.get("/api/auditoria/assets/auditoria.svg")
def auditoria_svg():
    return text_asset_response(
        _STATIC_DESCRIPTION_DIR / "auditoria.svg",
        media_type="image/svg+xml",
        fallback="<svg xmlns='http://www.w3.org/2000/svg'></svg>",
    )


@router.get("/auditoria/auditorias", response_class=HTMLResponse)
def auditoria_auditorias_page(request: Request):
    return _render_no_access_auditoria_page(
        request,
        title="Auditorías",
        description="Auditorías del módulo de auditoría.",
    )


@router.get("/auditoria/hallazgos", response_class=HTMLResponse)
def auditoria_hallazgos_page(request: Request):
    return _render_no_access_auditoria_page(
        request,
        title="Hallazgos",
        description="Hallazgos del módulo de auditoría.",
    )


@router.get("/auditoria/recomendaciones", response_class=HTMLResponse)
def auditoria_recomendaciones_page(request: Request):
    return _render_no_access_auditoria_page(
        request,
        title="Recomendaciones",
        description="Recomendaciones del módulo de auditoría.",
    )


@router.get("/auditoria/seguimiento", response_class=HTMLResponse)
def auditoria_seguimiento_page(request: Request):
    return _render_no_access_auditoria_page(
        request,
        title="Seguimiento",
        description="Seguimiento del módulo de auditoría.",
    )


# ── Resumen ───────────────────────────────────────────────────────────────────

@router.get("/api/auditoria/resumen")
def api_resumen(request: Request):
    _require_auditoria_permission(request, "view_auditorias")
    return JSONResponse(get_aud_resumen())


@router.get("/api/auditoria/permissions")
def api_auditoria_permissions(request: Request):
    return _auditoria_permissions(request)


# ── Auditorías ────────────────────────────────────────────────────────────────

@router.get("/api/auditoria/auditorias")
def api_list_auditorias(request: Request, estado: str = "", tipo: str = ""):
    _require_auditoria_permission(request, "view_auditorias")
    return JSONResponse(list_auditorias(estado or None, tipo or None))


@router.get("/api/auditoria/auditorias/{auditoria_id}")
def api_get_auditoria(request: Request, auditoria_id: int):
    _require_auditoria_permission(request, "view_auditorias")
    obj = get_auditoria(auditoria_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return JSONResponse(obj)


@router.post("/api/auditoria/auditorias")
def api_create_auditoria(request: Request, body: AuditoriaCreate):
    _require_auditoria_permission(request, "create_auditorias")
    try:
        return JSONResponse(create_auditoria(body.model_dump()), status_code=201)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe una auditoría con ese código")


@router.put("/api/auditoria/auditorias/{auditoria_id}")
def api_update_auditoria(request: Request, auditoria_id: int, body: AuditoriaUpdate):
    _require_auditoria_permission(request, "edit_auditorias")
    obj = update_auditoria(auditoria_id, body.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return JSONResponse(obj)


@router.delete("/api/auditoria/auditorias/{auditoria_id}")
def api_delete_auditoria(request: Request, auditoria_id: int):
    _require_auditoria_permission(request, "delete_auditorias")
    if not delete_auditoria(auditoria_id):
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return JSONResponse({"ok": True})


# ── Hallazgos ─────────────────────────────────────────────────────────────────

@router.get("/api/auditoria/hallazgos")
def api_list_hallazgos(request: Request, auditoria_id: int = 0, nivel_riesgo: str = "", estado: str = ""):
    _require_auditoria_permission(request, "view_auditorias")
    return JSONResponse(list_hallazgos(
        auditoria_id or None,
        nivel_riesgo or None,
        estado or None,
    ))


@router.get("/api/auditoria/hallazgos/{hallazgo_id}")
def api_get_hallazgo(request: Request, hallazgo_id: int):
    _require_auditoria_permission(request, "view_auditorias")
    obj = get_hallazgo(hallazgo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return JSONResponse(obj)


@router.post("/api/auditoria/hallazgos")
def api_create_hallazgo(request: Request, body: HallazgoCreate):
    _require_auditoria_permission(request, "register_hallazgos")
    return JSONResponse(create_hallazgo(body.model_dump()), status_code=201)


@router.put("/api/auditoria/hallazgos/{hallazgo_id}")
def api_update_hallazgo(request: Request, hallazgo_id: int, body: HallazgoUpdate):
    _require_auditoria_permission(request, "register_hallazgos")
    obj = update_hallazgo(hallazgo_id, body.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return JSONResponse(obj)


@router.delete("/api/auditoria/hallazgos/{hallazgo_id}")
def api_delete_hallazgo(request: Request, hallazgo_id: int):
    _require_auditoria_permission(request, "delete_auditorias")
    if not delete_hallazgo(hallazgo_id):
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return JSONResponse({"ok": True})


# ── Recomendaciones ───────────────────────────────────────────────────────────

@router.get("/api/auditoria/recomendaciones")
def api_list_recomendaciones(request: Request, hallazgo_id: int = 0, estado: str = "", auditoria_id: int = 0):
    _require_auditoria_permission(request, "view_auditorias")
    return JSONResponse(list_recomendaciones(
        hallazgo_id or None,
        estado or None,
        auditoria_id or None,
    ))


@router.get("/api/auditoria/recomendaciones/{rec_id}")
def api_get_recomendacion(request: Request, rec_id: int):
    _require_auditoria_permission(request, "view_auditorias")
    obj = get_recomendacion(rec_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return JSONResponse(obj)


@router.post("/api/auditoria/recomendaciones")
def api_create_recomendacion(request: Request, body: RecomendacionCreate):
    _require_auditoria_permission(request, "register_hallazgos")
    return JSONResponse(create_recomendacion(body.model_dump()), status_code=201)


@router.put("/api/auditoria/recomendaciones/{rec_id}")
def api_update_recomendacion(request: Request, rec_id: int, body: RecomendacionUpdate):
    _require_auditoria_permission(request, "close_recomendaciones")
    obj = update_recomendacion(rec_id, body.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return JSONResponse(obj)


@router.delete("/api/auditoria/recomendaciones/{rec_id}")
def api_delete_recomendacion(request: Request, rec_id: int):
    _require_auditoria_permission(request, "delete_auditorias")
    if not delete_recomendacion(rec_id):
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return JSONResponse({"ok": True})


# ── Seguimiento ───────────────────────────────────────────────────────────────

@router.get("/api/auditoria/seguimiento")
def api_list_seguimiento(request: Request, recomendacion_id: int = 0):
    _require_auditoria_permission(request, "view_auditorias")
    return JSONResponse(list_seguimiento(recomendacion_id or None))


@router.post("/api/auditoria/seguimiento")
def api_create_seguimiento(request: Request, body: SeguimientoCreate):
    _require_auditoria_permission(request, "register_seguimiento")
    data = body.model_dump()
    if data.get("fecha") is None:
        from datetime import date
        data["fecha"] = date.today()
    return JSONResponse(create_seguimiento(data), status_code=201)


@router.delete("/api/auditoria/seguimiento/{seg_id}")
def api_delete_seguimiento(request: Request, seg_id: int):
    _require_auditoria_permission(request, "delete_auditorias")
    if not delete_seguimiento(seg_id):
        raise HTTPException(status_code=404, detail="Entrada de seguimiento no encontrada")
    return JSONResponse({"ok": True})
