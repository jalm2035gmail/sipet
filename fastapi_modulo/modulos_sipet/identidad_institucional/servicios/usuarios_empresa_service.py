from __future__ import annotations

import json
from typing import Any, Literal, Optional

from fastapi import HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import load_only

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.core.module_registry import get_active_app_access_names
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    can_assign_role,
    get_role_permission_catalog,
    get_visible_role_names,
    normalize_role_name,
    sensitive_lookup_hash,
)
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import (
    decrypt_sensitive,
    encrypt_sensitive,
    hash_password,
)


def serialize_user_detail(user: Usuario) -> dict[str, Any]:
    nombre = decrypt_sensitive(user.full_name) or decrypt_sensitive(user.usuario) or ""
    raw_app_access = getattr(user, "app_access", None)
    raw_conversation_access = getattr(user, "conversation_access", None)
    return {
        "id": user.id,
        "nombre": nombre,
        "usuario": decrypt_sensitive(user.usuario) or "",
        "correo": decrypt_sensitive(user.correo) or "",
        "celular": str(user.celular or ""),
        "departamento": str(user.departamento or ""),
        "puesto": str(user.puesto or ""),
        "jefe_inmediato_id": user.jefe_inmediato_id,
        "imagen": str(user.imagen or ""),
        "rol": normalize_role_name(user.role),
        "is_active": bool(user.is_active if user.is_active is not None else True),
        "totp_enabled": bool(user.totp_enabled),
        "is_employee": bool(getattr(user, "is_employee", False)),
        "app_access": parse_json_field(getattr(user, "app_access", None)),
        "menu_blocks": parse_json_field(getattr(user, "menu_blocks", None)),
        "conversation_access": parse_json_field(getattr(user, "conversation_access", None)),
        "app_access_levels": parse_json_field(getattr(user, "app_access", None)),
        "inherit_role_permissions": not bool(str(raw_app_access or "").strip()) and not bool(str(raw_conversation_access or "").strip()),
    }


def serialize_user_list_item(user: Usuario) -> dict[str, Any]:
    data = serialize_user_detail(user)
    data.pop("imagen", None)
    data.pop("jefe_inmediato_id", None)
    return data


def serialize_user(user: Usuario) -> dict[str, Any]:
    return serialize_user_detail(user)


def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def _parse_optional_bool(value: Optional[str]) -> Optional[bool]:
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    if raw in {"1", "true", "t", "yes", "si", "sí", "on"}:
        return True
    if raw in {"0", "false", "f", "no", "off"}:
        return False
    raise HTTPException(status_code=422, detail="El parámetro is_active debe ser true o false.")


def _parse_optional_flag(value: Optional[str], *, default: bool = True) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "f", "no", "off"}


def _build_colaboradores_query(
    db: Any,
    *,
    q: str = "",
    role: str = "",
    is_active: Optional[bool] = None,
    detail: str = "full",
):
    query = db.query(Usuario)
    if detail == "light":
        query = query.options(
            load_only(
                Usuario.id,
                Usuario.full_name,
                Usuario.usuario,
                Usuario.correo,
                Usuario.celular,
                Usuario.departamento,
                Usuario.puesto,
                Usuario.role,
                Usuario.is_active,
                Usuario.totp_enabled,
                Usuario.is_employee,
                Usuario.app_access,
                Usuario.menu_blocks,
                Usuario.conversation_access,
            )
        )
    role_value = normalize_role_name(role) if str(role or "").strip() else ""
    if role_value:
        query = query.filter(Usuario.role == role_value)
    if is_active is not None:
        query = query.filter(Usuario.is_active.is_(is_active))
    q_value = str(q or "").strip()
    if q_value:
        q_hash = sensitive_lookup_hash(q_value)
        like_value = f"%{q_value}%"
        query = query.filter(
            or_(
                Usuario.departamento.ilike(like_value),
                Usuario.puesto.ilike(like_value),
                Usuario.celular.ilike(like_value),
                Usuario.role.ilike(like_value),
                Usuario.usuario_hash == q_hash,
                Usuario.correo_hash == q_hash,
            )
        )
    return query.order_by(Usuario.id)


def list_colaboradores_payload(
    request: Request,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    q: str = "",
    role: str = "",
    is_active: Optional[str] = None,
    detail: Literal["full", "light"] = "full",
    include_catalogs: Optional[str] = None,
) -> dict[str, Any]:
    legacy_mode = (
        limit is None
        and offset == 0
        and not str(q or "").strip()
        and not str(role or "").strip()
        and is_active is None
        and detail == "full"
        and include_catalogs is None
    )
    include_catalogs_value = _parse_optional_flag(include_catalogs, default=True)
    is_active_value = _parse_optional_bool(is_active)

    db = SessionLocal()
    try:
        if legacy_mode:
            users = db.query(Usuario).order_by(Usuario.id).all()
            return {
                "success": True,
                "data": [serialize_user(user) for user in users],
                "assignable_roles": get_visible_role_names(request),
                "role_profiles": get_role_permission_catalog(request),
                "installed_app_options": get_active_app_access_names(),
            }

        safe_limit = limit or 50
        query = _build_colaboradores_query(
            db,
            q=q,
            role=role,
            is_active=is_active_value,
            detail=detail,
        )
        total = query.order_by(None).count()
        users = query.offset(offset).limit(safe_limit).all()
        serializer = serialize_user_list_item if detail == "light" else serialize_user
        payload: dict[str, Any] = {
            "success": True,
            "data": [serializer(user) for user in users],
            "meta": {
                "limit": safe_limit,
                "offset": offset,
                "returned": len(users),
                "total": total,
                "has_more": (offset + len(users)) < total,
                "detail": detail,
                "filters": {
                    "q": str(q or "").strip(),
                    "role": normalize_role_name(role) if str(role or "").strip() else "",
                    "is_active": is_active_value,
                },
            },
        }
        if include_catalogs_value:
            payload["assignable_roles"] = get_visible_role_names(request)
            payload["role_profiles"] = get_role_permission_catalog(request)
            payload["installed_app_options"] = get_active_app_access_names()
        return payload
    finally:
        db.close()


def save_colaborador_payload(request: Request, payload: Any) -> dict[str, Any]:
    nombre = (payload.nombre or "").strip()
    usuario = (payload.usuario or "").strip()
    correo = (payload.correo or "").strip()
    rol = normalize_role_name(payload.rol)
    if not can_assign_role(request, rol):
        raise HTTPException(status_code=403, detail="No puedes asignar ese rol.")
    if not usuario:
        raise HTTPException(status_code=422, detail="El campo usuario es obligatorio.")

    inherit_role_permissions = bool(payload.inherit_role_permissions)
    app_access_val = None if inherit_role_permissions else (payload.app_access_levels or payload.app_access)
    app_access_json = json.dumps(app_access_val) if app_access_val is not None else None
    menu_blocks_json = json.dumps(payload.menu_blocks) if payload.menu_blocks is not None else None
    conv_json = json.dumps(payload.conversation_access) if (not inherit_role_permissions and payload.conversation_access is not None) else None

    db = SessionLocal()
    try:
        if payload.id:
            user = db.query(Usuario).filter(Usuario.id == payload.id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            user.full_name = encrypt_sensitive(nombre) if nombre else user.full_name
            if usuario:
                user.usuario = encrypt_sensitive(usuario)
                user.usuario_hash = sensitive_lookup_hash(usuario)
            if correo:
                user.correo = encrypt_sensitive(correo)
                user.correo_hash = sensitive_lookup_hash(correo)
            if payload.contrasena:
                user.contrasena = hash_password(payload.contrasena)
            user.role = rol
            user.departamento = payload.departamento or user.departamento
            user.puesto = payload.puesto or user.puesto
            user.celular = payload.celular or user.celular
            user.jefe_inmediato_id = payload.jefe_inmediato_id or user.jefe_inmediato_id
            user.imagen = payload.imagen or user.imagen
            user.totp_enabled = payload.totp_enabled
            user.is_employee = payload.empleado
            user.app_access = app_access_json
            if menu_blocks_json is not None:
                user.menu_blocks = menu_blocks_json
            user.conversation_access = conv_json
        else:
            if not payload.contrasena:
                raise HTTPException(status_code=422, detail="La contraseña es obligatoria para nuevos usuarios.")
            existing = db.query(Usuario).filter(Usuario.usuario_hash == sensitive_lookup_hash(usuario)).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"El usuario '{usuario}' ya existe.")
            user = Usuario(
                full_name=encrypt_sensitive(nombre),
                usuario=encrypt_sensitive(usuario),
                usuario_hash=sensitive_lookup_hash(usuario),
                correo=encrypt_sensitive(correo) if correo else None,
                correo_hash=sensitive_lookup_hash(correo) if correo else None,
                contrasena=hash_password(payload.contrasena),
                role=rol,
                departamento=payload.departamento,
                puesto=payload.puesto,
                celular=payload.celular,
                jefe_inmediato_id=payload.jefe_inmediato_id,
                imagen=payload.imagen,
                totp_enabled=payload.totp_enabled,
                is_active=True,
                is_employee=payload.empleado,
                app_access=app_access_json,
                menu_blocks=menu_blocks_json,
                conversation_access=conv_json,
            )
            db.add(user)

        db.commit()
        db.refresh(user)
        return serialize_user(user)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
