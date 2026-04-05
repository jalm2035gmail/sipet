from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import (
    OportunidadCerrarGanadaRequest,
    OportunidadCerrarPerdidaRequest,
    OportunidadCreate,
    OportunidadEtapaUpdate,
    OportunidadUpdate,
)
from fastapi_modulo.modulos.crm.servicios.oportunidad_service import (
    archivar_oportunidad,
    cambiar_etapa_oportunidad,
    calcular_probabilidad_sistema,
    create_oportunidad,
    delete_oportunidad,
    get_historial_oportunidad,
    list_oportunidades_by_tenant,
    list_oportunidades_sin_movimiento,
    marcar_oportunidad_ganada,
    marcar_oportunidad_perdida,
    update_oportunidad,
)
from fastapi_modulo.modulos.crm.servicios.pipeline_service import (
    get_aging_pipeline,
    get_forecast_ponderado,
    get_oportunidades_en_riesgo,
    get_pipeline_por_etapa,
    get_pipeline_por_ejecutivo,
    get_pipeline_por_sucursal,
)

router = APIRouter()


@router.get("/api/crm/oportunidades")
def api_list_oportunidades(request: Request, contacto_id: int = 0, etapa: str = "", q: str = "", responsable: str = "", sucursal: str = "", skip: int = 0, limit: int = 100):
    return JSONResponse(list_oportunidades_by_tenant(getattr(request.state, "tenant_id", None), contacto_id or None, etapa or None, q or None, responsable or None, sucursal or None, skip, limit))


@router.get("/api/crm/oportunidades/sin-movimiento")
def api_oportunidades_sin_movimiento(request: Request, dias: int = 7):
    return JSONResponse(list_oportunidades_sin_movimiento(getattr(request.state, "tenant_id", None), dias_minimos=max(1, dias)))


# ── Pipeline analytics ──────────────────────────────────────────────────────

@router.get("/api/crm/pipeline/por-etapa")
def api_pipeline_por_etapa(request: Request):
    return JSONResponse(get_pipeline_por_etapa(getattr(request.state, "tenant_id", None)))


@router.get("/api/crm/pipeline/por-ejecutivo")
def api_pipeline_por_ejecutivo(request: Request):
    return JSONResponse(get_pipeline_por_ejecutivo(getattr(request.state, "tenant_id", None)))


@router.get("/api/crm/pipeline/por-sucursal")
def api_pipeline_por_sucursal(request: Request):
    return JSONResponse(get_pipeline_por_sucursal(getattr(request.state, "tenant_id", None)))


@router.get("/api/crm/pipeline/forecast")
def api_pipeline_forecast(request: Request):
    return JSONResponse(get_forecast_ponderado(getattr(request.state, "tenant_id", None)))


@router.get("/api/crm/pipeline/aging")
def api_pipeline_aging(request: Request):
    return JSONResponse(get_aging_pipeline(getattr(request.state, "tenant_id", None)))


@router.get("/api/crm/pipeline/en-riesgo")
def api_pipeline_en_riesgo(request: Request, dias: int = 14):
    return JSONResponse(get_oportunidades_en_riesgo(getattr(request.state, "tenant_id", None), dias_inactividad=max(1, dias)))


@router.post("/api/crm/oportunidades")
def api_create_oportunidad(body: OportunidadCreate, request: Request):
    try:
        return JSONResponse(
            create_oportunidad(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/crm/oportunidades/{oportunidad_id}")
def api_update_oportunidad(oportunidad_id: int, body: OportunidadUpdate, request: Request):
    try:
        result = update_oportunidad(
            oportunidad_id,
            body.model_dump(exclude_unset=True),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.delete("/api/crm/oportunidades/{oportunidad_id}")
def api_delete_oportunidad(oportunidad_id: int, request: Request):
    if not delete_oportunidad(oportunidad_id, getattr(request.state, "tenant_id", None)):
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse({"ok": True})


@router.post("/api/crm/oportunidades/{oportunidad_id}/etapa")
def api_cambiar_etapa_oportunidad(oportunidad_id: int, body: OportunidadEtapaUpdate, request: Request):
    try:
        result = cambiar_etapa_oportunidad(
            oportunidad_id,
            body.etapa,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
            comentario=body.comentario,
            motivo=body.motivo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/oportunidades/{oportunidad_id}/ganar")
def api_marcar_oportunidad_ganada(oportunidad_id: int, body: OportunidadCerrarGanadaRequest, request: Request):
    try:
        result = marcar_oportunidad_ganada(
            oportunidad_id,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
            motivo_ganancia_id=body.motivo_ganancia_id,
            monto_real=body.monto_real,
            producto_vendido=body.producto_vendido,
            comentario=body.comentario,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/oportunidades/{oportunidad_id}/perder")
def api_marcar_oportunidad_perdida(oportunidad_id: int, body: OportunidadCerrarPerdidaRequest, request: Request):
    try:
        result = marcar_oportunidad_perdida(
            oportunidad_id,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
            motivo_perdida_id=body.motivo_perdida_id,
            comentario=body.comentario,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.get("/api/crm/oportunidades/{oportunidad_id}/historial")
def api_historial_etapas(oportunidad_id: int, request: Request):
    return JSONResponse(get_historial_oportunidad(oportunidad_id, getattr(request.state, "tenant_id", None)))

router = APIRouter()


@router.get("/api/crm/oportunidades")
def api_list_oportunidades(request: Request, contacto_id: int = 0, etapa: str = ""):
    return JSONResponse(list_oportunidades_by_tenant(getattr(request.state, "tenant_id", None), contacto_id or None, etapa or None))


@router.post("/api/crm/oportunidades")
def api_create_oportunidad(body: OportunidadCreate, request: Request):
    try:
        return JSONResponse(
            create_oportunidad(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/crm/oportunidades/{oportunidad_id}")
def api_update_oportunidad(oportunidad_id: int, body: OportunidadUpdate, request: Request):
    try:
        result = update_oportunidad(
            oportunidad_id,
            body.model_dump(exclude_unset=True),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.delete("/api/crm/oportunidades/{oportunidad_id}")
def api_delete_oportunidad(oportunidad_id: int, request: Request):
    if not delete_oportunidad(oportunidad_id, getattr(request.state, "tenant_id", None)):
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse({"ok": True})


@router.post("/api/crm/oportunidades/{oportunidad_id}/etapa")
def api_cambiar_etapa_oportunidad(oportunidad_id: int, body: OportunidadEtapaUpdate, request: Request):
    try:
        result = cambiar_etapa_oportunidad(
            oportunidad_id,
            body.etapa,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/oportunidades/{oportunidad_id}/ganar")
def api_marcar_oportunidad_ganada(oportunidad_id: int, request: Request):
    try:
        result = marcar_oportunidad_ganada(
            oportunidad_id,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/oportunidades/{oportunidad_id}/perder")
def api_marcar_oportunidad_perdida(oportunidad_id: int, request: Request):
    try:
        result = marcar_oportunidad_perdida(
            oportunidad_id,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)


@router.patch("/api/crm/oportunidades/{oportunidad_id}/archivar")
def api_archivar_oportunidad(oportunidad_id: int, request: Request):
    result = archivar_oportunidad(
        oportunidad_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return JSONResponse(result)
