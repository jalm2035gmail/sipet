from fastapi import APIRouter, Depends

from .api import router as api_router
from .api import compat_router as compat_api_router
from .assets import router as assets_router
from .dependencies import require_any_section_access
from .pages import router as pages_router
from .placeholders import router as placeholders_router


router = APIRouter(dependencies=[Depends(require_any_section_access)])
router.include_router(compat_api_router)
router.include_router(api_router)
router.include_router(assets_router)
router.include_router(pages_router)
router.include_router(placeholders_router)

__all__ = ["router"]
