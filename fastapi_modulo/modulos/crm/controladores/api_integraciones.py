"""Endpoints REST para integraciones del ecosistema SIPET (Fase 9.2)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from fastapi_modulo.modulos.crm.controladores.dependencies import get_tenant
from fastapi_modulo.modulos.crm.servicios import multitienda_service as svc

router = APIRouter(prefix="/api/crm/integraciones", tags=["CRM Integraciones"])


# ── Estado ────────────────────────────────────────────────────────────────────

@router.get("/estado")
def estado_integraciones():
    """Retorna qué módulos externos están disponibles para integración."""
    return svc.estado_integracion()


# ── Multitienda ───────────────────────────────────────────────────────────────

@router.post("/multitienda/sync-clientes")
def sync_clientes(request: Request):
    """Importa clientes de Multitienda como contactos CRM."""
    tenant_id = get_tenant(request)
    try:
        return svc.sincronizar_clientes(tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class CarritosRequest(BaseModel):
    horas_min: int = 24
    monto_min: float = 0


@router.post("/multitienda/detectar-carritos")
def detectar_carritos(request: Request, body: CarritosRequest = CarritosRequest()):
    """Detecta carritos abandonados y crea oportunidades CRM."""
    tenant_id = get_tenant(request)
    try:
        return svc.detectar_carritos_abandonados(tenant_id, horas_min=body.horas_min, monto_min=body.monto_min)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class InactivosRequest(BaseModel):
    dias_inactivo: int = 90


@router.post("/multitienda/reactivar-inactivos")
def reactivar_inactivos(request: Request, body: InactivosRequest = InactivosRequest()):
    """Detecta clientes inactivos y crea oportunidades de reactivación."""
    tenant_id = get_tenant(request)
    try:
        return svc.reactivar_clientes_inactivos(tenant_id, dias_inactivo=body.dias_inactivo)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class PostventaRequest(BaseModel):
    monto_min: float = 5000
    dias_atras: int = 7


@router.post("/multitienda/postventa-pedidos")
def postventa_pedidos(request: Request, body: PostventaRequest = PostventaRequest()):
    """Crea actividades de seguimiento postventa para pedidos de alto valor."""
    tenant_id = get_tenant(request)
    try:
        return svc.procesar_pedidos_alto_valor(tenant_id, monto_min=body.monto_min, dias_atras=body.dias_atras)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/multitienda/enriquecer-scoring/{contacto_id}")
def enriquecer_scoring(request: Request, contacto_id: int):
    """Enriquece el lead score del contacto con datos de compra de Multitienda."""
    tenant_id = get_tenant(request)
    try:
        return svc.enriquecer_scoring_lead(tenant_id, contacto_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/multitienda/ejecutar-ciclo")
def ejecutar_ciclo(request: Request):
    """Ejecuta todos los triggers de integración Multitienda → CRM en un solo ciclo."""
    tenant_id = get_tenant(request)
    try:
        return svc.ejecutar_ciclo_multitienda(tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
