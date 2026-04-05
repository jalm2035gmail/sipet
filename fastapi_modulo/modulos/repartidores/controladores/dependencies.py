"""
Dependencias de autenticación y autorización — Módulo Repartidores.

Sigue el mismo patrón que otros módulos SIPET:
  - request.state.user_name    → username activo (fijado por el middleware de sesión)
  - request.state.user_role    → rol normalizado del usuario
  - request.state.tenant_id    → tenant (multiempresa, del host)

Niveles de acceso declarados en __manifest__.py:
  full_access          → Administrador — CRUD completo
  special_permissions  → Supervisor logístico — asignar, liquidar, gestionar
  delivery_access      → Repartidor — solo ve sus propias entregas
  read_only            → Solo lectura — consulta sin modificar
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.repartidores.modelos.db_models import RepRepartidor

# ── Conjuntos de roles ───────────────────────────────────────────────────────

# Roles de sistema que siempre tienen acceso total
_ADMIN_ROLES = frozenset({
    'superadministrador', 'superadmin', 'administrador',
    'administrador_multiempresa', 'full_access',
})

# Acceso de supervisor (full + special)
_SUPERVISOR_ROLES = _ADMIN_ROLES | frozenset({
    'special_permissions', 'supervisor_logistico', 'supervisor',
})

# Cualquier rol autorizado en el módulo
_ALLOWED_ROLES = _SUPERVISOR_ROLES | frozenset({
    'delivery_access', 'read_only',
})


# ── Helpers de sesión ────────────────────────────────────────────────────────

def get_user_info(request: Request) -> dict:
    """Lee los datos de sesión inyectados por el middleware SIPET."""
    username = getattr(request.state, 'user_name', None)
    if not username:
        raise HTTPException(status_code=401, detail='Sesión no válida. Inicia sesión para continuar.')
    return {
        'username': str(username),
        'role': str(getattr(request.state, 'user_role', '') or '').lower(),
        'tenant_id': getattr(request.state, 'tenant_id', None),
    }


def require_access(request: Request) -> dict:
    """Verifica que el usuario tiene acceso al módulo de Repartidores."""
    info = get_user_info(request)
    role = info['role']
    # Admins siempre pasan aunque su rol no esté en _ALLOWED_ROLES
    if role in _ADMIN_ROLES:
        return info
    if role not in _ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail='Sin acceso al módulo de Repartidores.',
        )
    return info


def require_write(user: dict = Depends(require_access)) -> dict:
    """Bloquea a usuarios con rol read_only."""
    if user['role'] == 'read_only':
        raise HTTPException(status_code=403, detail='Acceso de solo lectura.')
    return user


def require_supervisor(user: dict = Depends(require_access)) -> dict:
    """Requiere rol de supervisor o administrador (bloquea delivery_access y read_only)."""
    if user['role'] not in _SUPERVISOR_ROLES:
        raise HTTPException(
            status_code=403,
            detail='Se requiere rol de supervisor o administrador para esta operación.',
        )
    return user


# ── Predicados de rol ────────────────────────────────────────────────────────

def is_delivery_only(user: dict) -> bool:
    """True si el usuario solo puede ver sus propias entregas."""
    return user['role'] == 'delivery_access'


def is_read_only(user: dict) -> bool:
    return user['role'] == 'read_only'


def is_supervisor_or_above(user: dict) -> bool:
    return user['role'] in _SUPERVISOR_ROLES


# ── Vinculación repartidor ↔ usuario SIPET ───────────────────────────────────

def get_linked_repartidor_id(db: Session, username: str) -> Optional[int]:
    """Devuelve el repartidor_id vinculado al usuario SIPET, o None."""
    rep = (
        db.query(RepRepartidor)
        .filter(
            RepRepartidor.sipet_username == username,
            RepRepartidor.activo == True,
        )
        .first()
    )
    return rep.id if rep else None
