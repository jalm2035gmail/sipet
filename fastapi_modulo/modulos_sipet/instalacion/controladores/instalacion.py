from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from fastapi_modulo.modulos_sipet.instalacion.servicios.installer_service import get_installation_status

router = APIRouter()


@router.get("/instalacion")
def instalacion_redirect(request: Request):
    del request
    return RedirectResponse(url="/base_datos/inicializar", status_code=303)


@router.get("/api/instalacion/status")
def instalacion_status():
    return JSONResponse({"success": True, "status": get_installation_status()})
