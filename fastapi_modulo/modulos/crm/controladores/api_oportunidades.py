from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import OportunidadCreate, OportunidadEtapaUpdate, OportunidadUpdate
from fastapi_modulo.modulos.crm.servicios.oportunidad_service import (
    cambiar_etapa_oportunidad,
    create_oportunidad,
    delete_oportunidad,
    list_oportunidades_by_tenant,
    marcar_oportunidad_ganada,
    marcar_oportunidad_perdida,
    update_oportunidad,
)

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
