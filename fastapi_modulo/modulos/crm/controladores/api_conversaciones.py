"""Endpoints REST para conversaciones contextuales del CRM (Fase 9.1)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from fastapi_modulo.modulos.crm import servicios
from fastapi_modulo.modulos.crm.controladores.dependencies import get_tenant
from fastapi_modulo.modulos.crm.servicios import conversacion_service as svc

router = APIRouter(prefix="/api/crm/conversaciones", tags=["CRM Conversaciones"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ConversacionCreate(BaseModel):
    ref_tipo: str           # contacto | oportunidad | actividad | campania
    ref_id: int
    asunto: str
    actor: str
    mensaje_inicial: str
    tipo_mensaje: str = "comentario"
    multitienda_uuid: Optional[str] = None


class MensajeCreate(BaseModel):
    actor: str
    contenido: str
    tipo: str = "comentario"   # comentario | apoyo | validacion | cierre


class CerrarRequest(BaseModel):
    actor: str
    observacion: str = ""


class AccionRequest(BaseModel):
    ref_tipo: str
    ref_id: int
    actor: str
    contenido: str
    destinatario: str = ""     # Usado solo por pedir_apoyo


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_conversaciones(
    request: Request,
    ref_tipo: Optional[str] = None,
    ref_id: Optional[int] = None,
    estado: Optional[str] = None,
):
    tenant_id = get_tenant(request)
    return svc.list_conversaciones(tenant_id, ref_tipo=ref_tipo, ref_id=ref_id, estado=estado)


@router.post("", status_code=201)
def crear_conversacion(request: Request, body: ConversacionCreate):
    tenant_id = get_tenant(request)
    try:
        return svc.crear_conversacion(
            tenant_id=tenant_id,
            ref_tipo=body.ref_tipo,
            ref_id=body.ref_id,
            asunto=body.asunto,
            actor=body.actor,
            mensaje_inicial=body.mensaje_inicial,
            tipo_mensaje=body.tipo_mensaje,
            multitienda_uuid=body.multitienda_uuid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{conversacion_id}")
def get_conversacion(request: Request, conversacion_id: int):
    tenant_id = get_tenant(request)
    result = svc.get_conversacion(tenant_id, conversacion_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return result


@router.post("/{conversacion_id}/mensajes", status_code=201)
def agregar_mensaje(request: Request, conversacion_id: int, body: MensajeCreate):
    tenant_id = get_tenant(request)
    try:
        return svc.agregar_mensaje(tenant_id, conversacion_id, body.actor, body.contenido, body.tipo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{conversacion_id}/leer")
def marcar_leidos(request: Request, conversacion_id: int, actor: str):
    tenant_id = get_tenant(request)
    try:
        return svc.marcar_mensajes_leidos(tenant_id, conversacion_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{conversacion_id}/cerrar")
def cerrar_conversacion(request: Request, conversacion_id: int, body: CerrarRequest):
    tenant_id = get_tenant(request)
    try:
        return svc.cerrar_conversacion(tenant_id, conversacion_id, body.actor, body.observacion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Acciones tipificadas ───────────────────────────────────────────────────────

@router.post("/accion/comentar", status_code=201)
def comentar_seguimiento(request: Request, body: AccionRequest):
    tenant_id = get_tenant(request)
    try:
        return svc.comentar_seguimiento(tenant_id, body.ref_tipo, body.ref_id, body.actor, body.contenido)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/accion/pedir-apoyo", status_code=201)
def pedir_apoyo(request: Request, body: AccionRequest):
    tenant_id = get_tenant(request)
    try:
        return svc.pedir_apoyo(tenant_id, body.ref_tipo, body.ref_id, body.actor, body.contenido, body.destinatario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/accion/validar-propuesta", status_code=201)
def validar_propuesta(request: Request, body: AccionRequest):
    tenant_id = get_tenant(request)
    try:
        return svc.validar_propuesta(tenant_id, body.ref_tipo, body.ref_id, body.actor, body.contenido)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/accion/observaciones-cierre", status_code=201)
def observaciones_cierre(request: Request, body: AccionRequest):
    tenant_id = get_tenant(request)
    try:
        return svc.registrar_observaciones_cierre(tenant_id, body.ref_tipo, body.ref_id, body.actor, body.contenido)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
