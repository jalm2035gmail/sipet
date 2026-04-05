from __future__ import annotations

from fastapi import APIRouter

from .branding import router as branding_router
from .empresa_accesos import router as accesos_router
from .empresa_usuarios import router as usuarios_router


router = APIRouter()
router.include_router(branding_router)
router.include_router(usuarios_router)
router.include_router(accesos_router)

