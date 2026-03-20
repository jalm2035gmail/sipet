from fastapi import APIRouter, Depends

from fastapi_modulo.modulos.brujula.controladores.api import router as api_router
from fastapi_modulo.modulos.brujula.controladores.dependencies import require_brujula_access
from fastapi_modulo.modulos.brujula.controladores.pages import router as pages_router
from fastapi_modulo.modulos.brujula.servicios.indicator_service import initialize_indicator_storage_on_startup


router = APIRouter(dependencies=[Depends(require_brujula_access)])
router.include_router(pages_router)
router.include_router(api_router)


@router.on_event("startup")
def initialize_brujula_module() -> None:
    initialize_indicator_storage_on_startup()

__all__ = ["router"]
