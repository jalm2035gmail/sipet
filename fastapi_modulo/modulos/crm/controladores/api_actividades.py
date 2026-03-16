from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import ActividadCreate, ActividadReprogramar, ActividadUpdate
from fastapi_modulo.modulos.crm.servicios.actividad_service import (
    completar_actividad,
    create_actividad,
    delete_actividad,
    list_actividades_vencidas,
    list_actividades_by_tenant,
    reprogramar_actividad,
    update_actividad,
)

router = APIRouter()


@router.get("/api/crm/actividades")
def api_list_actividades(request: Request, contacto_id: int = 0, oportunidad_id: int = 0, completada: str = ""):
    completada_bool = None
    if completada == "true":
        completada_bool = True
    elif completada == "false":
        completada_bool = False
    return JSONResponse(
        list_actividades_by_tenant(
            getattr(request.state, "tenant_id", None),
            contacto_id or None,
            oportunidad_id or None,
            completada_bool,
        )
    )


@router.post("/api/crm/actividades")
def api_create_actividad(body: ActividadCreate, request: Request):
    try:
        return JSONResponse(
            create_actividad(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/crm/actividades/{actividad_id}")
def api_update_actividad(actividad_id: int, body: ActividadUpdate, request: Request):
    try:
        result = update_actividad(
            actividad_id,
            body.model_dump(exclude_unset=True),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)


@router.delete("/api/crm/actividades/{actividad_id}")
def api_delete_actividad(actividad_id: int, request: Request):
    if not delete_actividad(actividad_id, getattr(request.state, "tenant_id", None)):
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse({"ok": True})


@router.get("/api/crm/actividades/vencidas")
def api_list_actividades_vencidas(request: Request):
    return JSONResponse(list_actividades_vencidas(getattr(request.state, "tenant_id", None)))


@router.post("/api/crm/actividades/{actividad_id}/completar")
def api_completar_actividad(actividad_id: int, request: Request):
    result = completar_actividad(
        actividad_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/actividades/{actividad_id}/reprogramar")
def api_reprogramar_actividad(actividad_id: int, body: ActividadReprogramar, request: Request):
    result = reprogramar_actividad(
        actividad_id,
        body.fecha,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)
