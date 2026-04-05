"""
servicios/builder_access.py
─────────────────────────────────────────────────────────────────────────────
Control de acceso específico del constructor de páginas frontend.

Envuelve la lógica de resolución de nivel de acceso por pantalla y
expone dos helpers listos para usar en controladores:

  get_builder_access_level(request)  →  str  (nombre del nivel)
  require_write(request)             →  None  (lanza 403 si no tiene permisos)

Niveles soportados (de mayor a menor):
    full_access, special_permissions, department_only, user_only, read_only

Solo full_access y special_permissions pueden escribir.

Uso típico:
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import (
        get_builder_access_level,
        require_write,
    )

    level = get_builder_access_level(request)
    require_write(request)  # lanza HTTPException 403 si no autorizado
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_user_screen_access_levels,
)

_FRONTEND_APP_NAME       = "Frontend"
_FRONTEND_BUILDER_SCREEN = "frontend.builder"

_WRITE_LEVELS = {"full_access", "special_permissions"}
_ALL_LEVELS   = ("full_access", "special_permissions", "department_only", "user_only", "read_only")


def get_builder_access_level(request: Request) -> str:
    """
    Resuelve el nivel de acceso del usuario actual al constructor frontend.

    Examina los niveles de pantalla en orden de prioridad:
    frontend.builder → Frontend → __all__

    Devuelve:
        Nombre del nivel ('full_access', 'read_only', 'no_access', etc.)
    """
    levels = get_user_screen_access_levels(request)
    for key in (_FRONTEND_BUILDER_SCREEN, _FRONTEND_APP_NAME, "__all__"):
        entry = levels.get(key) or {}
        if isinstance(entry, bool):
            return "full_access" if entry else "no_access"
        if not isinstance(entry, dict):
            continue
        for level_name in _ALL_LEVELS:
            if entry.get(level_name):
                return level_name
    return "no_access"


def require_write(request: Request) -> None:
    """
    Eleva HTTPException 403 si el usuario no tiene permisos de escritura
    en el constructor frontend (necesita full_access o special_permissions).
    """
    level = get_builder_access_level(request)
    if level not in _WRITE_LEVELS:
        raise HTTPException(
            status_code=403,
            detail="Sin permisos de edición en el constructor frontend.",
        )
