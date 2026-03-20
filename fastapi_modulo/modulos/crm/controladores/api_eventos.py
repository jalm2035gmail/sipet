from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.servicios.evento_service import list_eventos_by_tenant, list_seguimiento_by_tenant

router = APIRouter()


@router.get("/api/crm/eventos")
def api_list_eventos(request: Request, entidad: str = "", entidad_id: int = 0, limit: int = 50):
    return JSONResponse(
        list_eventos_by_tenant(
            getattr(request.state, "tenant_id", None),
            entidad=entidad or None,
            entidad_id=entidad_id or None,
            limit=limit,
        )
    )


@router.get("/api/crm/seguimiento")
def api_list_seguimiento(request: Request, contacto_id: int = 0, oportunidad_id: int = 0, limit: int = 50):
    return JSONResponse(
        list_seguimiento_by_tenant(
            getattr(request.state, "tenant_id", None),
            contacto_id=contacto_id or None,
            oportunidad_id=oportunidad_id or None,
            limit=limit,
        )
    )
