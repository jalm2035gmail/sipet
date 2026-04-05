"""
Dependencias de autorización para el módulo de Reservaciones.

Niveles declarados en __manifest__.py:
  full_access         → RolReservaciones.ADMIN    (CRUD completo + stats)
  special_permissions → RolReservaciones.EJECUTIVO (sus citas y agenda)
  read_only           → RolReservaciones.LECTOR   (solo GET)
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, Request

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_user_screen_access_levels,
    is_admin_or_superadmin,
)
from fastapi_modulo.modulos.reservaciones.modelos.db_models import ResEjecutivo

# ──────────────────────────────────────────────────────────────────────────────

SCREEN_KEY = "reservaciones"
ACCESS_DENIED = "Acceso restringido al módulo de Reservaciones"


class RolReservaciones(str, Enum):
    ADMIN = "admin"
    EJECUTIVO = "ejecutivo"
    LECTOR = "lector"


# ──────────────────────────────────────────────────────────────────────────────
# Resolución de rol
# ──────────────────────────────────────────────────────────────────────────────

def _get_res_role(request: Request) -> Optional[RolReservaciones]:
    """Resuelve el rol del usuario en el módulo de reservaciones."""
    if is_admin_or_superadmin(request):
        return RolReservaciones.ADMIN
    try:
        levels: dict = get_user_screen_access_levels(request) or {}
        # La clave puede llegar con la capitalización original
        entry = levels.get(SCREEN_KEY) or levels.get(SCREEN_KEY.capitalize()) or {}
        if entry.get("full_access"):
            return RolReservaciones.ADMIN
        if entry.get("special_permissions"):
            return RolReservaciones.EJECUTIVO
        if entry.get("read_only"):
            return RolReservaciones.LECTOR
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Dependencias de acceso
# ──────────────────────────────────────────────────────────────────────────────

def require_any_res_access(request: Request) -> RolReservaciones:
    """Requiere cualquier nivel de acceso al módulo (full_access | special | read_only)."""
    rol = _get_res_role(request)
    if rol is None:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    return rol


def require_full_access(request: Request) -> RolReservaciones:
    """Requiere full_access (Administrador). Lanza 403 para otros roles."""
    rol = _get_res_role(request)
    if rol != RolReservaciones.ADMIN:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    return rol


def require_at_least_ejecutivo(request: Request) -> RolReservaciones:
    """Requiere full_access o special_permissions. Lanza 403 para read_only."""
    rol = _get_res_role(request)
    if rol not in (RolReservaciones.ADMIN, RolReservaciones.EJECUTIVO):
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    return rol


# ──────────────────────────────────────────────────────────────────────────────
# Lookup de ejecutivo en sesión
# ──────────────────────────────────────────────────────────────────────────────

def get_ejecutivo_id_en_sesion(
    request: Request,
    db=Depends(SessionLocal),
) -> Optional[int]:
    """
    Retorna el ID del ResEjecutivo vinculado al usuario en sesión.
    Intenta primero por email (via core repository), luego por nombre de login.
    Retorna None si no se encuentra o en caso de error.
    """
    user_name: str = getattr(request.state, "user_name", None) or ""
    if not user_name:
        return None

    # 1) Intentar por email usando repositorio central
    try:
        from fastapi_modulo.modulos_sipet.web.repositorios.core_repository import (
            find_user_by_login,
        )
        user = find_user_by_login(user_name)
        if user:
            email = getattr(user, "email", None) or getattr(user, "correo", None)
            if email:
                ej = (
                    db.query(ResEjecutivo)
                    .filter(ResEjecutivo.email == email, ResEjecutivo.disponible == True)
                    .first()
                )
                if ej:
                    return ej.id
    except Exception:
        pass

    # 2) Fallback: match por campo name == user_name (login)
    ej = (
        db.query(ResEjecutivo)
        .filter(ResEjecutivo.name == user_name, ResEjecutivo.disponible == True)
        .first()
    )
    return ej.id if ej else None


__all__ = [
    "RolReservaciones",
    "require_any_res_access",
    "require_full_access",
    "require_at_least_ejecutivo",
    "get_ejecutivo_id_en_sesion",
    "ACCESS_DENIED",
]
