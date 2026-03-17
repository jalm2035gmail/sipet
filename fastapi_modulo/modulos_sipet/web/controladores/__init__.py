from fastapi_modulo.modulos_sipet.web.controladores.backend_auth import router as backend_auth_router
from fastapi_modulo.modulos_sipet.web.controladores.auth_api import router as auth_api_router
from fastapi_modulo.modulos_sipet.web.controladores.auth_pages import router as auth_pages_router
from fastapi_modulo.modulos_sipet.web.controladores.auth_passkey import router as auth_passkey_router

__all__ = ["auth_api_router", "auth_pages_router", "auth_passkey_router", "backend_auth_router"]
