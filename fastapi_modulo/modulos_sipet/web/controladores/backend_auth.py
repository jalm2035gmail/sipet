from __future__ import annotations

from fastapi import APIRouter

from fastapi_modulo.modulos_sipet.web.controladores.auth_api import router as auth_api_router
from fastapi_modulo.modulos_sipet.web.controladores.auth_pages import router as auth_pages_router
from fastapi_modulo.modulos_sipet.web.controladores.auth_passkey import router as auth_passkey_router

router = APIRouter()
router.include_router(auth_pages_router)
router.include_router(auth_api_router)
router.include_router(auth_passkey_router)

try:
    from fastapi_modulo.modulos_sipet.web.controladores.user_admin import router as user_admin_router
except ModuleNotFoundError:
    user_admin_router = None

if user_admin_router is not None:
    router.include_router(user_admin_router)
