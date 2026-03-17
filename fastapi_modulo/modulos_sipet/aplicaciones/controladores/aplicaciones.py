from fastapi import APIRouter

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.api_packages import router as packages_router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.api_protocol import router as protocol_router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.api_security import router as security_router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.api_state import router as state_router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.api_tasks import router as tasks_router
from fastapi_modulo.modulos_sipet.aplicaciones.controladores.pages import router as pages_router

router = APIRouter()
router.include_router(pages_router)
router.include_router(protocol_router)
router.include_router(packages_router)
router.include_router(security_router)
router.include_router(state_router)
router.include_router(tasks_router)

__all__ = ["router"]
