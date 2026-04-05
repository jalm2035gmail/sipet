"""Controladores de identidad_institucional."""

from .branding import router as branding_router
from .empresa_accesos import router as empresa_accesos_router
from .empresa_usuarios import router as empresa_usuarios_router
from .identidad_institucional import router


__all__ = [
    "branding_router",
    "empresa_accesos_router",
    "empresa_usuarios_router",
    "router",
]
