from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import MotivoGananciaCreate, MotivoPerdidaCreate
from fastapi_modulo.modulos.crm.repositorios.motivo_repository import (
    create_motivo_ganancia,
    create_motivo_perdida,
    delete_motivo_ganancia,
    delete_motivo_perdida,
    list_motivos_ganancia,
    list_motivos_perdida,
)
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id

router = APIRouter()


# ── Motivos de pérdida ──────────────────────────────────────────────────────

@router.get("/api/crm/motivos-perdida")
def api_list_motivos_perdida(request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    return JSONResponse(list_motivos_perdida(tenant_id))


@router.post("/api/crm/motivos-perdida")
def api_create_motivo_perdida(body: MotivoPerdidaCreate, request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    try:
        return JSONResponse(create_motivo_perdida(tenant_id, body.nombre), status_code=201)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/api/crm/motivos-perdida/{motivo_id}")
def api_delete_motivo_perdida(motivo_id: int, request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    if not delete_motivo_perdida(tenant_id, motivo_id):
        raise HTTPException(status_code=404, detail="Motivo no encontrado")
    return JSONResponse({"ok": True})


# ── Motivos de ganancia ─────────────────────────────────────────────────────

@router.get("/api/crm/motivos-ganancia")
def api_list_motivos_ganancia(request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    return JSONResponse(list_motivos_ganancia(tenant_id))


@router.post("/api/crm/motivos-ganancia")
def api_create_motivo_ganancia(body: MotivoGananciaCreate, request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    try:
        return JSONResponse(create_motivo_ganancia(tenant_id, body.nombre), status_code=201)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/api/crm/motivos-ganancia/{motivo_id}")
def api_delete_motivo_ganancia(motivo_id: int, request: Request):
    tenant_id = normalize_tenant_id(getattr(request.state, "tenant_id", None))
    if not delete_motivo_ganancia(tenant_id, motivo_id):
        raise HTTPException(status_code=404, detail="Motivo no encontrado")
    return JSONResponse({"ok": True})
