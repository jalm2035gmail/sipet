from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.servicios.notification_service import (
    ejecutar_ciclo_notificaciones,
    list_notificaciones,
    marcar_leida,
    marcar_todas_leidas,
)

router = APIRouter()


@router.get("/api/crm/notificaciones")
def api_list_notificaciones(
    request: Request,
    usuario: str = "",
    solo_no_leidas: bool = False,
    skip: int = 0,
    limit: int = 50,
):
    if not usuario:
        usuario = getattr(request.state, "user_name", "") or ""
    return JSONResponse(
        list_notificaciones(
            getattr(request.state, "tenant_id", None),
            usuario,
            solo_no_leidas=solo_no_leidas,
            skip=skip,
            limit=limit,
        )
    )


@router.patch("/api/crm/notificaciones/{notif_id}/leer")
def api_marcar_leida(notif_id: int, request: Request, usuario: str = ""):
    if not usuario:
        usuario = getattr(request.state, "user_name", "") or ""
    result = marcar_leida(getattr(request.state, "tenant_id", None), notif_id, usuario)
    if not result:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return JSONResponse(result)


@router.patch("/api/crm/notificaciones/leer-todas")
def api_marcar_todas_leidas(request: Request, usuario: str = ""):
    if not usuario:
        usuario = getattr(request.state, "user_name", "") or ""
    count = marcar_todas_leidas(getattr(request.state, "tenant_id", None), usuario)
    return JSONResponse({"ok": True, "marcadas": count})


@router.post("/api/crm/notificaciones/ciclo")
def api_ciclo_notificaciones(request: Request):
    result = ejecutar_ciclo_notificaciones(getattr(request.state, "tenant_id", None))
    return JSONResponse(result)
