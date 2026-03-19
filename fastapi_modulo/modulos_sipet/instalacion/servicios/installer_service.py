from __future__ import annotations

from typing import Any, Dict, Mapping

from sqlalchemy import func

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.database_router import (
    SIPET_CONFIG_PATH,
    can_connect_current_database,
    get_sipet_conf_settings,
    initialize_database_from_sipet_conf,
)
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol, Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import sensitive_lookup_hash
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import encrypt_sensitive, hash_password


def get_installation_status() -> Dict[str, Any]:
    if not SIPET_CONFIG_PATH.exists():
        return {
            "required": True,
            "reason": "sipet.conf no existe",
            "config_path": str(SIPET_CONFIG_PATH),
            "settings": get_sipet_conf_settings(),
        }
    ok, error = can_connect_current_database()
    return {
        "required": not ok,
        "reason": "" if ok else str(error or "No se pudo conectar a la base de datos"),
        "config_path": str(SIPET_CONFIG_PATH),
        "settings": get_sipet_conf_settings(),
    }


def _refresh_runtime_after_install() -> None:
    core_db.refresh_runtime_database_state()

    runtime_app = _get_runtime_app_module()

    runtime_app.refresh_runtime_database_globals()


def _get_runtime_app_module():
    from fastapi_modulo.modulos_sipet.modulo_base import runtime_app

    return runtime_app


def _ensure_installation_superadmin(payload: Mapping[str, Any]) -> Dict[str, str]:
    username = str(payload.get("superadmin_username") or payload.get("admin_username") or "").strip()
    password = str(payload.get("superadmin_password") or payload.get("admin_password") or "")
    email = str(payload.get("superadmin_email") or payload.get("admin_email") or "").strip().lower()

    if not username or not password or not email:
        runtime_app = _get_runtime_app_module()
        runtime_app.ensure_system_superadmin_user()
        return {
            "username": (runtime_app.os.environ.get("SYSTEM_SUPERADMIN_USERNAME") or runtime_app._decode_b64(runtime_app.DEFAULT_SUPERADMIN_USERNAME_B64)).strip(),
            "email": (runtime_app.os.environ.get("SYSTEM_SUPERADMIN_EMAIL") or runtime_app._decode_b64(runtime_app.DEFAULT_SUPERADMIN_EMAIL_B64)).strip(),
        }

    db = core_db.SessionLocal()
    try:
        role = db.query(Rol).filter(func.lower(Rol.nombre) == "superadministrador").first()
        if role is None:
            role = Rol(nombre="superadministrador", descripcion="Acceso total al sistema")
            db.add(role)
            db.commit()
            db.refresh(role)

        username_hash = sensitive_lookup_hash(username)
        email_hash = sensitive_lookup_hash(email)
        user = (
            db.query(Usuario)
            .filter((Usuario.usuario_hash == username_hash) | (Usuario.correo_hash == email_hash))
            .first()
        )
        if user is None:
            user = (
                db.query(Usuario)
                .filter(
                    (func.lower(Usuario.usuario) == username.lower())
                    | (func.lower(Usuario.correo) == email.lower())
                )
                .first()
            )
        password_hash = hash_password(password)
        if user is None:
            user = Usuario(
                full_name="Super Administrador",
                usuario=encrypt_sensitive(username),
                usuario_hash=username_hash,
                correo=encrypt_sensitive(email),
                correo_hash=email_hash,
                contrasena=password_hash,
                rol_id=role.id,
                role="superadministrador",
                is_active=True,
            )
        else:
            user.full_name = user.full_name or "Super Administrador"
            user.usuario = encrypt_sensitive(username)
            user.usuario_hash = username_hash
            user.correo = encrypt_sensitive(email)
            user.correo_hash = email_hash
            user.contrasena = password_hash
            user.rol_id = role.id
            user.role = "superadministrador"
            user.is_active = True
        db.add(user)
        db.commit()
        return {"username": username, "email": email}
    finally:
        db.close()


def bootstrap_installation(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = initialize_database_from_sipet_conf(payload)
    _refresh_runtime_after_install()
    runtime_app = _get_runtime_app_module()

    runtime_app.run_core_schema_bootstrap(force_refresh_database=False)
    admin_user = _ensure_installation_superadmin(payload)

    status = get_installation_status()
    result.update(
        {
            "connected": not bool(status["required"]),
            "error": "" if not status["required"] else str(status["reason"] or ""),
            "superadmin": admin_user,
        }
    )
    return result
