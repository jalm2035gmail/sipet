"""
deps.py — inyección de dependencias para los routers raíz del módulo PWA.

Principio: delegar auth al core SIPET cuando está disponible.
Si el módulo se ejecuta en modo standalone (app/), usa el JWT propio.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

# ── Re-export de deps standalone para compatibilidad ──────────────────────────
from app.api.deps import (          # noqa: F401  (re-exported)
    DBSession,
    PaginationParams,
    Pagination,
    get_current_active_user,
    get_current_superuser,
)


# ── Garantiza usuario activo con id int ───────────────────────────────────────
CurrentUser = Depends(get_current_active_user)


def require_admin(current_user=Depends(get_current_active_user)):
    """Restringe el acceso a administradores o superusuarios."""
    if not (getattr(current_user, "is_superuser", False) or
            getattr(current_user, "is_admin", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user


def get_db_session() -> Session:  # noqa: D103
    yield from get_db()
