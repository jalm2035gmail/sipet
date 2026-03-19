from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.core.module_registry import list_system_app_access_options
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol, Usuario

ROLE_ALIASES: dict[str, str] = {}
ROLE_PROFILE_TABLE = "role_permission_profiles"
ADMIN_ROLES = {"superadministrador", "administrador_multiempresa", "administrador"}
PROTECTED_ROLE_NAMES = {"superadministrador", "administrador_multiempresa"}
ACCESS_LEVEL_KEYS = (
    "full_access",
    "read_only",
    "department_only",
    "user_only",
    "special_permissions",
)
DEFAULT_ROLE_NAMES = [
    "superadministrador",
    "administrador_multiempresa",
    "administrador",
    "autoridades",
    "departamento",
    "usuario",
]


def normalize_role_name(role_name: str | None) -> str:
    raw = (role_name or "").strip().lower()
    if not raw:
        return "usuario"
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if normalized in {"superadmin", "super_admin", "super_administrador", "superadministrador"}:
        return "superadministrador"
    return ROLE_ALIASES.get(normalized, normalized or "usuario")


def _normalize_key(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


def _blank_access_entry() -> dict[str, bool]:
    return {key: False for key in ACCESS_LEVEL_KEYS}


def _normalize_access_entry(value: Any) -> dict[str, bool]:
    if isinstance(value, bool):
        entry = _blank_access_entry()
        entry["full_access"] = bool(value)
        return entry
    if not isinstance(value, dict):
        return _blank_access_entry()
    entry = {key: bool(value.get(key, False)) for key in ACCESS_LEVEL_KEYS}
    selected = [key for key in ACCESS_LEVEL_KEYS if entry[key]]
    if len(selected) > 1:
        first = selected[0]
        entry = {key: key == first for key in ACCESS_LEVEL_KEYS}
    return entry


def _normalize_access_levels(value: Any) -> dict[str, dict[str, bool]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, bool]] = {}
    for raw_key, raw_entry in value.items():
        key = str(raw_key or "").strip()
        if not key:
            continue
        normalized[key] = _normalize_access_entry(raw_entry)
    return normalized


def _normalize_conversation_access(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "role": "",
            "can_create_groups": False,
            "can_send_notifications": False,
            "notification_scope": "",
        }
    role = str(value.get("role") or value.get("rol") or "").strip().lower()
    if role not in {"usuario", "administrador"}:
        role = ""
    scope = str(value.get("notification_scope") or value.get("scope") or "").strip().lower()
    if scope not in {"department", "company"}:
        scope = ""
    if role != "administrador":
        scope = ""
    can_send = role == "administrador" and bool(value.get("can_send_notifications"))
    if not can_send:
        scope = ""
    return {
        "role": role,
        "can_create_groups": bool(value.get("can_create_groups")) and bool(role),
        "can_send_notifications": can_send,
        "notification_scope": scope,
    }


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_permission_flags(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    return {_normalize_key(str(key)): bool(flag) for key, flag in value.items() if _normalize_key(str(key))}


def _parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _merge_access_levels(base: dict[str, dict[str, bool]], override: dict[str, dict[str, bool]] | None) -> dict[str, dict[str, bool]]:
    merged = {key: dict(entry) for key, entry in (base or {}).items()}
    if not isinstance(override, dict):
        return merged
    normalized_index = {_normalize_key(key): key for key in merged}
    for key, entry in override.items():
        resolved_key = normalized_index.get(_normalize_key(key), key)
        merged[resolved_key] = _normalize_access_entry(entry)
    return merged


def _merge_dict(base: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(base or {})
    if isinstance(override, dict):
        merged.update(override)
    return merged


def _first_matching_entry(levels: dict[str, dict[str, bool]], key: str) -> dict[str, bool]:
    if key in levels:
        return _normalize_access_entry(levels[key])
    canonical = _normalize_key(key)
    if not canonical:
        return {}
    for current_key, entry in levels.items():
        if _normalize_key(current_key) == canonical:
            return _normalize_access_entry(entry)
    if "__all__" in levels:
        return _normalize_access_entry(levels["__all__"])
    return {}


def _entry_level_name(entry: dict[str, bool]) -> str:
    normalized = _normalize_access_entry(entry)
    for key in ACCESS_LEVEL_KEYS:
        if normalized.get(key):
            return key
    return "no_access"


def _has_access_entry(entry: dict[str, bool]) -> bool:
    return _entry_level_name(entry) != "no_access"


def _full_access_profile() -> dict[str, dict[str, bool]]:
    return {"__all__": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False}}


def _default_profile_for_role(role_name: str, description: str = "") -> dict[str, Any]:
    normalized_role = normalize_role_name(role_name)
    if normalized_role in ADMIN_ROLES:
        screen_access_levels = _full_access_profile()
        conversation_access = {
            "role": "administrador",
            "can_create_groups": True,
            "can_send_notifications": True,
            "notification_scope": "company",
        }
    else:
        screen_access_levels = {}
        conversation_access = {
            "role": "usuario" if normalized_role in {"autoridades", "departamento", "usuario"} else "",
            "can_create_groups": normalized_role in {"autoridades", "departamento", "usuario"},
            "can_send_notifications": False,
            "notification_scope": "",
        }
    return {
        "role_name": normalized_role,
        "description": str(description or "").strip(),
        "screen_access_levels": screen_access_levels,
        "conversation_access": conversation_access,
        "backend_roles": [],
        "permission_flags": {},
        "is_system_role": normalized_role in set(DEFAULT_ROLE_NAMES),
        "is_protected": normalized_role in PROTECTED_ROLE_NAMES,
    }


def _ensure_role_profile_schema() -> None:
    db = SessionLocal()
    try:
        db.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {ROLE_PROFILE_TABLE} (
                    role_name VARCHAR(120) PRIMARY KEY,
                    screen_access_levels TEXT NOT NULL DEFAULT '{{}}',
                    conversation_access TEXT NOT NULL DEFAULT '{{}}',
                    backend_roles TEXT NOT NULL DEFAULT '[]',
                    permission_flags TEXT NOT NULL DEFAULT '{{}}',
                    updated_at VARCHAR(40) NOT NULL DEFAULT ''
                )
                """
            )
        )
        db.commit()
    finally:
        db.close()


def _seed_missing_role_profiles() -> None:
    _ensure_role_profile_schema()
    db = SessionLocal()
    try:
        role_rows = db.query(Rol).order_by(Rol.nombre.asc()).all()
        existing = {
            str(row[0]).strip().lower()
            for row in db.execute(text(f"SELECT role_name FROM {ROLE_PROFILE_TABLE}")).fetchall()
            if str(row[0]).strip()
        }
        for role in role_rows:
            role_name = normalize_role_name(role.nombre)
            if not role_name or role_name in existing:
                continue
            payload = _default_profile_for_role(role_name, role.descripcion or "")
            db.execute(
                text(
                    f"""
                    INSERT INTO {ROLE_PROFILE_TABLE}
                        (role_name, screen_access_levels, conversation_access, backend_roles, permission_flags, updated_at)
                    VALUES
                        (:role_name, :screen_access_levels, :conversation_access, :backend_roles, :permission_flags, :updated_at)
                    """
                ),
                {
                    "role_name": role_name,
                    "screen_access_levels": _json_dumps(payload["screen_access_levels"]),
                    "conversation_access": _json_dumps(payload["conversation_access"]),
                    "backend_roles": _json_dumps(payload["backend_roles"]),
                    "permission_flags": _json_dumps(payload["permission_flags"]),
                    "updated_at": "",
                },
            )
        db.commit()
    finally:
        db.close()


def sensitive_lookup_hash(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_current_role(request: Request) -> str:
    role = (
        getattr(request.state, "user_role", None)
        or getattr(request.state, "role", None)
        or request.cookies.get("user_role")
        or request.cookies.get("role")
        or request.cookies.get("rol")
        or ""
    )
    return normalize_role_name(role)


def _load_role_profile_from_db(db, role_name: str) -> dict[str, Any]:
    normalized_role = normalize_role_name(role_name)
    role_row = db.query(Rol).filter(Rol.nombre == normalized_role).first()
    description = (getattr(role_row, "descripcion", "") or "").strip()
    raw = db.execute(
        text(
            f"""
            SELECT screen_access_levels, conversation_access, backend_roles, permission_flags
            FROM {ROLE_PROFILE_TABLE}
            WHERE role_name = :role_name
            LIMIT 1
            """
        ),
        {"role_name": normalized_role},
    ).fetchone()
    if raw is None:
        return _default_profile_for_role(normalized_role, description)
    return {
        "role_name": normalized_role,
        "description": description,
        "screen_access_levels": _normalize_access_levels(_parse_json_field(raw[0])),
        "conversation_access": _normalize_conversation_access(_parse_json_field(raw[1])),
        "backend_roles": _normalize_string_list(_parse_json_field(raw[2])),
        "permission_flags": _normalize_permission_flags(_parse_json_field(raw[3])),
        "is_system_role": normalized_role in set(DEFAULT_ROLE_NAMES),
        "is_protected": normalized_role in PROTECTED_ROLE_NAMES,
    }


def get_role_permission_catalog(request: Request | None = None) -> list[dict[str, Any]]:
    _seed_missing_role_profiles()
    db = SessionLocal()
    try:
        role_names = [normalize_role_name(role.nombre) for role in db.query(Rol).order_by(Rol.nombre.asc()).all() if normalize_role_name(role.nombre)]
        if not role_names:
            role_names = list(DEFAULT_ROLE_NAMES)
        allowed = set(role_names)
        if request is not None:
            allowed = set(get_visible_role_names(request))
        return [_load_role_profile_from_db(db, role_name) for role_name in role_names if role_name in allowed]
    finally:
        db.close()


def save_role_permission_profile(
    *,
    role_name: str,
    description: str = "",
    screen_access_levels: Any = None,
    conversation_access: Any = None,
    backend_roles: Any = None,
    permission_flags: Any = None,
) -> dict[str, Any]:
    normalized_role = normalize_role_name(role_name)
    _seed_missing_role_profiles()
    db = SessionLocal()
    try:
        role = db.query(Rol).filter(Rol.nombre == normalized_role).first()
        if role is None:
            role = Rol(nombre=normalized_role, descripcion=str(description or "").strip())
            db.add(role)
            db.flush()
        else:
            role.descripcion = str(description or "").strip()
            db.add(role)
        stored_profile = _load_role_profile_from_db(db, normalized_role)
        profile = {
            "screen_access_levels": _normalize_access_levels(
                screen_access_levels if screen_access_levels is not None else stored_profile["screen_access_levels"]
            ),
            "conversation_access": _normalize_conversation_access(
                conversation_access if conversation_access is not None else stored_profile["conversation_access"]
            ),
            "backend_roles": _normalize_string_list(
                backend_roles if backend_roles is not None else stored_profile["backend_roles"]
            ),
            "permission_flags": _normalize_permission_flags(
                permission_flags if permission_flags is not None else stored_profile["permission_flags"]
            ),
        }
        row_exists = db.execute(
            text(f"SELECT role_name FROM {ROLE_PROFILE_TABLE} WHERE role_name = :role_name LIMIT 1"),
            {"role_name": normalized_role},
        ).fetchone()
        params = {
            "role_name": normalized_role,
            "screen_access_levels": _json_dumps(profile["screen_access_levels"]),
            "conversation_access": _json_dumps(profile["conversation_access"]),
            "backend_roles": _json_dumps(profile["backend_roles"]),
            "permission_flags": _json_dumps(profile["permission_flags"]),
            "updated_at": "",
        }
        if row_exists is None:
            db.execute(
                text(
                    f"""
                    INSERT INTO {ROLE_PROFILE_TABLE}
                        (role_name, screen_access_levels, conversation_access, backend_roles, permission_flags, updated_at)
                    VALUES
                        (:role_name, :screen_access_levels, :conversation_access, :backend_roles, :permission_flags, :updated_at)
                    """
                ),
                params,
            )
        else:
            db.execute(
                text(
                    f"""
                    UPDATE {ROLE_PROFILE_TABLE}
                    SET
                        screen_access_levels = :screen_access_levels,
                        conversation_access = :conversation_access,
                        backend_roles = :backend_roles,
                        permission_flags = :permission_flags,
                        updated_at = :updated_at
                    WHERE role_name = :role_name
                    """
                ),
                params,
            )
        db.commit()
        return _load_role_profile_from_db(db, normalized_role)
    finally:
        db.close()


def _list_role_names_from_db() -> list[str]:
    _seed_missing_role_profiles()
    db = SessionLocal()
    try:
        role_names = [normalize_role_name(role.nombre) for role in db.query(Rol).order_by(Rol.nombre.asc()).all()]
        return [role_name for role_name in role_names if role_name]
    finally:
        db.close()


def is_superadmin(request: Request) -> bool:
    return get_current_role(request) == "superadministrador"


def is_multiempresa_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador_multiempresa"


def is_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador"


def is_admin_or_superadmin(request: Request) -> bool:
    return get_current_role(request) in ADMIN_ROLES


def require_superadmin(request: Request, detail: str = "Acceso solo para superadministrador") -> None:
    if not is_superadmin(request):
        raise HTTPException(status_code=403, detail=detail)


def require_admin_or_superadmin(request: Request, detail: str = "Acceso solo para administracion") -> None:
    if not is_admin_or_superadmin(request):
        raise HTTPException(status_code=403, detail=detail)


def get_visible_role_names(request: Request) -> list[str]:
    role_names = _list_role_names_from_db() or list(DEFAULT_ROLE_NAMES)
    viewer_role = get_current_role(request)
    if viewer_role == "superadministrador":
        return role_names
    if viewer_role in ADMIN_ROLES:
        return [role_name for role_name in role_names if role_name not in PROTECTED_ROLE_NAMES]
    return ["usuario"]


def can_assign_role(request: Request, role_name: str | None) -> bool:
    return normalize_role_name(role_name) in set(get_visible_role_names(request))


def _build_admin_access_payload(role_name: str) -> dict[str, Any]:
    catalog = list(list_system_app_access_options())
    return {
        "role": normalize_role_name(role_name),
        "screen_access_levels": _full_access_profile(),
        "user_app_access": catalog,
        "backend_roles": [],
        "conversation_access": {
            "role": "administrador",
            "can_create_groups": True,
            "can_send_notifications": True,
            "notification_scope": "company",
        },
        "permission_flags": {},
    }


def get_effective_access_payload(request: Request) -> dict[str, Any]:
    cached = getattr(request.state, "_effective_access_payload", None)
    if isinstance(cached, dict):
        return cached

    current_role = get_current_role(request)
    if current_role in ADMIN_ROLES:
        payload = _build_admin_access_payload(current_role)
        request.state._effective_access_payload = payload
        return payload

    username = (
        getattr(request.state, "user_name", None)
        or getattr(request.state, "username", None)
        or request.cookies.get("user_name")
        or request.cookies.get("username")
        or request.cookies.get("usuario")
        or ""
    ).strip()
    if not username:
        payload = {
            "role": current_role,
            "screen_access_levels": {},
            "user_app_access": [],
            "backend_roles": [],
            "conversation_access": _normalize_conversation_access(None),
            "permission_flags": {},
        }
        request.state._effective_access_payload = payload
        return payload

    _seed_missing_role_profiles()
    db = SessionLocal()
    try:
        lookup_hash = sensitive_lookup_hash(username)
        try:
            user = (
                db.query(Usuario)
                .filter((Usuario.usuario_hash == lookup_hash) | (Usuario.correo_hash == lookup_hash))
                .first()
            )
        except SQLAlchemyError as exc:
            print(f"[web.access_service] hash lookup skipped: {exc}", flush=True)
            user = None
        if user is None:
            user = (
                db.query(Usuario)
                .filter((func.lower(Usuario.usuario) == username.lower()) | (func.lower(Usuario.correo) == username.lower()))
                .first()
            )
        if user is None:
            payload = {
                "role": current_role,
                "screen_access_levels": {},
                "user_app_access": [],
                "backend_roles": [],
                "conversation_access": _normalize_conversation_access(None),
                "permission_flags": {},
            }
            request.state._effective_access_payload = payload
            return payload

        resolved_role = normalize_role_name(getattr(user, "role", None) or current_role)
        role_profile = _load_role_profile_from_db(db, resolved_role)
        user_screen_access_raw = getattr(user, "app_access", None)
        user_conversation_raw = getattr(user, "conversation_access", None)
        user_screen_access = (
            _normalize_access_levels(_parse_json_field(user_screen_access_raw))
            if str(user_screen_access_raw or "").strip()
            else None
        )
        user_conversation_access = (
            _normalize_conversation_access(_parse_json_field(user_conversation_raw))
            if str(user_conversation_raw or "").strip()
            else None
        )
        merged_levels = (
            _merge_access_levels(role_profile["screen_access_levels"], user_screen_access)
            if user_screen_access is not None
            else dict(role_profile["screen_access_levels"])
        )
        if "__all__" in merged_levels and _has_access_entry(merged_levels["__all__"]):
            user_app_access = list(list_system_app_access_options())
        else:
            user_app_access = [key for key, entry in merged_levels.items() if key != "__all__" and _has_access_entry(entry)]
        payload = {
            "role": resolved_role,
            "screen_access_levels": merged_levels,
            "user_app_access": user_app_access,
            "backend_roles": list(role_profile["backend_roles"]),
            "conversation_access": (
                _merge_dict(role_profile["conversation_access"], user_conversation_access)
                if user_conversation_access is not None
                else dict(role_profile["conversation_access"])
            ),
            "permission_flags": dict(role_profile["permission_flags"]),
            "inherits_role_permissions": user_screen_access is None and user_conversation_access is None,
        }
        request.state._effective_access_payload = payload
        return payload
    finally:
        db.close()


def get_user_backend_roles(request: Request, username: str | None = None) -> list[str]:
    del username
    return list(get_effective_access_payload(request).get("backend_roles") or [])


def get_user_permission_flags(request: Request) -> dict[str, bool]:
    return dict(get_effective_access_payload(request).get("permission_flags") or {})


def has_permission_flag(request: Request, permission_key: str) -> bool:
    return bool(get_user_permission_flags(request).get(_normalize_key(permission_key)))


def get_user_app_access(request: Request) -> list[str]:
    if is_admin_or_superadmin(request):
        return list(list_system_app_access_options())
    return list(get_effective_access_payload(request).get("user_app_access") or [])


def get_user_app_access_level(request: Request, app_name: str) -> str:
    if is_admin_or_superadmin(request):
        return "full_access"
    levels = get_user_screen_access_levels(request)
    return _entry_level_name(_first_matching_entry(levels, app_name))


def require_app_access(request: Request, app_name: str, detail: str = "Sin acceso a la aplicacion") -> None:
    if get_user_app_access_level(request, app_name) == "no_access":
        raise HTTPException(status_code=403, detail=detail)


def get_user_strategy_submenu_access_levels(request: Request) -> dict:
    if is_admin_or_superadmin(request):
        return _full_access_profile()
    raw = getattr(request.state, "user_strategy_submenu_access_levels", None) or request.cookies.get(
        "user_strategy_submenu_access_levels"
    ) or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def get_user_strategy_submenu_access_level(request: Request, submenu_name: str) -> str:
    levels = get_user_strategy_submenu_access_levels(request)
    return _entry_level_name(_first_matching_entry(levels, submenu_name))


def has_strategy_submenu_access(request: Request, submenu_name: str) -> bool:
    return get_user_strategy_submenu_access_level(request, submenu_name) != "no_access"


def get_user_screen_access_levels(request: Request) -> dict:
    if is_admin_or_superadmin(request):
        return _full_access_profile()
    return dict(get_effective_access_payload(request).get("screen_access_levels") or {})


def has_screen_access(request: Request, screen_name: str, app_name: str = "") -> bool:
    del app_name
    if is_admin_or_superadmin(request):
        return True
    levels = get_user_screen_access_levels(request)
    return _has_access_entry(_first_matching_entry(levels, screen_name))


def require_screen_access(request: Request, screen_name: str, detail: str = "Sin acceso a la pantalla", app_name: str = "") -> None:
    del app_name
    if not has_screen_access(request, screen_name):
        raise HTTPException(status_code=403, detail=detail)
