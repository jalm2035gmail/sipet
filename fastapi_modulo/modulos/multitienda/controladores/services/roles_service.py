from __future__ import annotations

from threading import Lock
from time import monotonic

from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol
from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name

_ROLES_CACHE_TTL_SECONDS = 300
_ROLES_CACHE_LOCK = Lock()
_ROLES_CACHE: dict[str, object] = {
    "expires_at": 0.0,
    "roles_by_id": {},
}


def get_roles_map(db) -> dict[int, str]:
    now = monotonic()
    with _ROLES_CACHE_LOCK:
        expires_at = float(_ROLES_CACHE.get("expires_at") or 0.0)
        cached = _ROLES_CACHE.get("roles_by_id") or {}
        if expires_at > now and cached:
            return dict(cached)

    roles_by_id = {role.id: normalize_role_name(role.nombre) for role in db.query(Rol).all()}
    with _ROLES_CACHE_LOCK:
        _ROLES_CACHE["expires_at"] = now + _ROLES_CACHE_TTL_SECONDS
        _ROLES_CACHE["roles_by_id"] = dict(roles_by_id)
    return roles_by_id


def clear_roles_cache() -> None:
    with _ROLES_CACHE_LOCK:
        _ROLES_CACHE["expires_at"] = 0.0
        _ROLES_CACHE["roles_by_id"] = {}
