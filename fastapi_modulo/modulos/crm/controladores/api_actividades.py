from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import (
    ActividadCancelarRequest,
    ActividadCompletarRequest,
    ActividadCreate,
    ActividadReprogramar,
    ActividadUpdate,
)
from fastapi_modulo.modulos.crm.servicios.actividad_service import (
    archivar_actividad,
    cancelar_actividad,
    completar_actividad,
    create_actividad,
    delete_actividad,
    list_actividades_vencidas,
    list_actividades_by_tenant,
    reprogramar_actividad,
    update_actividad,
)
from fastapi_modulo.modulos.crm.servicios.automation_service import (
    ejecutar_ciclo_automatizacion,
    verificar_sla_actividades,
)

router = APIRouter()


@router.get("/api/crm/actividades")
def api_list_actividades(request: Request, contacto_id: int = 0, oportunidad_id: int = 0, completada: str = "", q: str = "", responsable: str = "", skip: int = 0, limit: int = 100):
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
            q or None,
            responsable or None,
            skip,
            limit,
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


@router.get("/api/crm/actividades/sla/alertas")
def api_sla_alertas(request: Request):
    """Devuelve actividades que han superado su ventana de SLA."""
    return JSONResponse(verificar_sla_actividades(getattr(request.state, "tenant_id", None)))


@router.post("/api/crm/actividades/{actividad_id}/completar")
def api_completar_actividad(actividad_id: int, body: ActividadCompletarRequest, request: Request):
    result = completar_actividad(
        actividad_id,
        body.tipo_resultado,
        getattr(request.state, "tenant_id", None),
        siguiente_accion=body.siguiente_accion,
        comentario=body.comentario,
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/actividades/{actividad_id}/cancelar")
def api_cancelar_actividad(actividad_id: int, body: ActividadCancelarRequest, request: Request):
    result = cancelar_actividad(
        actividad_id,
        body.motivo,
        getattr(request.state, "tenant_id", None),
        siguiente_accion=body.siguiente_accion,
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/actividades/reprogramar/{actividad_id}")
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


@router.post("/api/crm/actividades/automatizacion/ejecutar")
def api_ejecutar_automatizacion(request: Request):
    """Ejecuta el ciclo completo de automatización: marca vencidas y retorna alertas SLA."""
    result = ejecutar_ciclo_automatizacion(
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", "sistema"),
    )
    return JSONResponse(result)


@router.patch("/api/crm/actividades/{actividad_id}/archivar")
def api_archivar_actividad(actividad_id: int, request: Request):
    result = archivar_actividad(
        actividad_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return JSONResponse(result)

