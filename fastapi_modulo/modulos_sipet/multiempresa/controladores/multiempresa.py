from __future__ import annotations

from fastapi import APIRouter

from fastapi_modulo.modulos.multiempresa.controladores.multiempresa_api import router as api_router
from fastapi_modulo.modulos.multiempresa.controladores.multiempresa_page import router as page_router

router = APIRouter()
router.include_router(page_router)
router.include_router(api_router)


