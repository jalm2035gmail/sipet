"""
controladores/frontend.py
Agregador principal: registra todos los sub-routers del modulo frontend.
"""

from fastapi import APIRouter

from .brand_controller   import router as _brand_router
from .builder_controller import router as _builder_router
from .contact_controller import router as _contact_router
from .gallery_controller import router as _gallery_router
from .pages_controller   import router as _pages_router
from .public_controller  import router as _public_router
from .tasas_controller   import router as _tasas_router

router = APIRouter()

router.include_router(_builder_router)
router.include_router(_pages_router)
router.include_router(_public_router)
router.include_router(_tasas_router)
router.include_router(_contact_router)
router.include_router(_gallery_router)
router.include_router(_brand_router)
