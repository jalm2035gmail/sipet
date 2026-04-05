from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.bootstrap import init_crm_module
from fastapi_modulo.modulos.crm.controladores.api_actividades import router as actividades_router
from fastapi_modulo.modulos.crm.controladores.api_automatizacion import router as automatizacion_router
from fastapi_modulo.modulos.crm.controladores.api_campanias import router as campanias_router
from fastapi_modulo.modulos.crm.controladores.api_contactos import router as contactos_router
from fastapi_modulo.modulos.crm.controladores.api_conversaciones import router as conversaciones_router
from fastapi_modulo.modulos.crm.controladores.api_eventos import router as eventos_router
from fastapi_modulo.modulos.crm.controladores.api_integraciones import router as integraciones_router
from fastapi_modulo.modulos.crm.controladores.api_motivos import router as motivos_router
from fastapi_modulo.modulos.crm.controladores.api_notificaciones import router as notificaciones_router
from fastapi_modulo.modulos.crm.controladores.api_notas import router as notas_router
from fastapi_modulo.modulos.crm.controladores.api_oportunidades import router as oportunidades_router
from fastapi_modulo.modulos.crm.controladores.dependencies import require_crm_access
from fastapi_modulo.modulos.crm.controladores.pages import router as pages_router
from fastapi_modulo.modulos.crm.servicios.dashboard_service import get_crm_resumen


@asynccontextmanager
async def crm_router_lifespan(_: APIRouter):
    init_crm_module()
    yield


router = APIRouter(
    dependencies=[Depends(require_crm_access)],
    lifespan=crm_router_lifespan,
)
router.include_router(pages_router)
router.include_router(contactos_router)
router.include_router(oportunidades_router)
router.include_router(actividades_router)
router.include_router(notas_router)
router.include_router(campanias_router)
router.include_router(eventos_router)
router.include_router(motivos_router)
router.include_router(notificaciones_router)
router.include_router(automatizacion_router)
router.include_router(conversaciones_router)
router.include_router(integraciones_router)


@router.get("/api/crm/resumen")
def crm_resumen(request: Request):
    return JSONResponse(get_crm_resumen(getattr(request.state, "tenant_id", None)))
