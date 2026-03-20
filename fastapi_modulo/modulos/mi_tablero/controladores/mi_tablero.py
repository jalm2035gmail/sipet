from fastapi import APIRouter

from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_api import router as dashboard_api_router
from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_pages import router as dashboard_pages_router


router = APIRouter()
router.include_router(dashboard_pages_router)
router.include_router(dashboard_api_router)
