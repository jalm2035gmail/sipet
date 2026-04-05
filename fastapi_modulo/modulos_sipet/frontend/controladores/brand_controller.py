"""
controladores/brand_controller.py
─────────────────────────────────────────────────────────────────────────────
Configuración de marca del módulo frontend (colores, logo, fuentes).

Rutas:
  GET  /api/frontend/brand
  POST /api/frontend/brand
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    get_brand as store_get_brand,
    save_brand as store_save_brand,
)
from fastapi_modulo.modulos_sipet.frontend.servicios import cache_service
from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access
from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import _load_login_identity

router = APIRouter(prefix="/api/frontend", tags=["Brand"])

_FRONTEND_BUILDER_SCREEN = "frontend.builder"


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

    _UPLOADS   = os.path.join("fastapi_modulo", "modulos", "personalizacion", "uploads")
    candidates = sorted(
        _glob.glob(os.path.join(_UPLOADS, "logo_empresa.*")),
        key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
        reverse=True,
    )
    if candidates:
        fname = os.path.basename(candidates[0])
        v     = int(os.path.getmtime(candidates[0])) if os.path.exists(candidates[0]) else 0
        return f"/personalizar/uploads/{fname}?v={v}"
    return ""


@router.get("/brand")
def api_brand_get(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    brand = store_get_brand()
    brand["identidad_logo_url"] = _resolve_identidad_logo_url()
    return {"success": True, "data": brand}


@router.post("/brand")
async def api_brand_save(request: Request):
    require_write(request)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "JSON inválido"}, status_code=400)
    brand = store_save_brand({k: v for k, v in body.items() if isinstance(v, str)})
    cache_service.clear_all()
    return {"success": True, "data": brand}
