from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.core.db import SessionLocal, get_current_database_info
from fastapi_modulo.core.module_registry import get_active_app_access_names, list_modules_payload
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    can_assign_role,
    get_role_permission_catalog,
    get_user_screen_access_levels,
    get_visible_role_names,
    is_admin_or_superadmin,
    is_superadmin,
    normalize_role_name,
    require_admin_or_superadmin,
    save_role_permission_profile,
    sensitive_lookup_hash,
)
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import (
    decrypt_sensitive,
    encrypt_sensitive,
    hash_password,
)
from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import (
    DEFAULT_LOGIN_IDENTITY,
    _build_login_asset_url,
    _load_login_identity,
    clear_frontend_page_cache,
    remove_login_image_if_custom,
    save_login_identity,
    store_login_image,
)
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates

router = APIRouter()

_MODULE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATE_NAME = "modulos/identidad_institucional/vistas/identidad_institucional.html"
_CSS_PATH = _MODULE_DIR / "static" / "css" / "identidad_institucional.css"

# ── Permisos del módulo Empresa ──────────────────────────────────────────────
# Niveles almacenados en screen_access_levels["empresa"]:
#   full_access        → Administrador  (todo)
#   special_permissions→ Editor         (branding + plantillas, sin usuarios)
#   department_only    → Gestor usuarios(usuarios, sin branding)
#   read_only          → Solo lectura   (ver, no editar)
#   sin entrada        → sidebar oculto (sin acceso)

_EMPRESA_SCREEN = "empresa"
_EMPRESA_ROLES_SCREEN = "empresa.roles"
_EMPRESA_ACCESS_SCREEN = "empresa.acceso"


def _screen_level_enabled(entry: Any, *level_keys: str) -> bool:
    if isinstance(entry, bool):
        return entry
    if not isinstance(entry, dict):
        return False
    return any(bool(entry.get(level_key)) for level_key in level_keys)


def _empresa_permissions(request: Any) -> dict[str, bool]:
    if is_admin_or_superadmin(request):
        return {
            "ver_branding": True,
            "editar_branding": True,
            "ver_usuarios": True,
            "gestionar_usuarios": True,
            "ver_acceso": True,
            "gestionar_acceso": True,
            "ver_datos": True,
            "ver_plantillas": True,
            "editar_plantillas": True,
        }
    levels = get_user_screen_access_levels(request)
    entry = levels.get(_EMPRESA_SCREEN) or {}
    roles_entry = levels.get(_EMPRESA_ROLES_SCREEN) or {}
    access_entry = levels.get(_EMPRESA_ACCESS_SCREEN) or {}
    if isinstance(entry, bool):
        return {
            k: entry
            for k in (
                "ver_branding",
                "editar_branding",
                "ver_usuarios",
                "gestionar_usuarios",
                "ver_acceso",
                "gestionar_acceso",
                "ver_datos",
                "ver_plantillas",
                "editar_plantillas",
            )
        }
    full = bool(entry.get("full_access"))
    editor = bool(entry.get("special_permissions"))
    gestor = bool(entry.get("department_only"))
    lector = bool(entry.get("read_only"))
    roles_admin = _screen_level_enabled(roles_entry, "full_access")
    roles_reader = _screen_level_enabled(roles_entry, "full_access", "read_only")
    access_admin = roles_admin or _screen_level_enabled(access_entry, "full_access")
    access_reader = roles_reader or _screen_level_enabled(access_entry, "full_access", "read_only")
    usuarios_admin = _screen_level_enabled(entry, "full_access")
    return {
        "ver_branding": full or editor or lector,
        "editar_branding": full or editor,
        "ver_usuarios": full or gestor or lector,
        "gestionar_usuarios": full or gestor,
        "ver_acceso": full or usuarios_admin or access_reader,
        "gestionar_acceso": full or access_admin,
        "ver_datos": full,
        "ver_plantillas": full or editor or lector,
        "editar_plantillas": full or editor,
    }


def _require_empresa_permission(request: Any, permission: str) -> None:
    if not _empresa_permissions(request).get(permission):
        raise HTTPException(status_code=403, detail="No tienes permiso para esta acción en Empresa.")


class IdentidadForm(BaseModel):
    company_short_name: str = Field(default="", max_length=60)
    login_message: str = Field(default="", max_length=200)
    menu_position: Literal["arriba", "abajo"] = "arriba"

    @field_validator("company_short_name", "login_message", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return (v or "").strip()


def _render_identidad_institucional_page(request: Request) -> HTMLResponse:
    identity = _load_login_identity()
    favicon_url = _build_login_asset_url(identity.get("favicon_filename"), DEFAULT_LOGIN_IDENTITY["favicon_filename"])
    logo_url = _build_login_asset_url(identity.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"])
    login_logo_url = _build_login_asset_url(identity.get("login_logo_filename"), DEFAULT_LOGIN_IDENTITY["login_logo_filename"])
    desktop_bg_url = _build_login_asset_url(identity.get("desktop_bg_filename"), DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"])
    mobile_bg_url = _build_login_asset_url(identity.get("mobile_bg_filename"), DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"])
    loaded_assets = sum(1 for v in [favicon_url, logo_url, login_logo_url, desktop_bg_url, mobile_bg_url] if (v or "").strip())
    consistency = max(60, min(100, int(round((loaded_assets / 5) * 100)))) if loaded_assets else 60

    template = get_templates().env.get_template(_TEMPLATE_NAME)
    content = template.render(
        saved=request.query_params.get("saved") == "1",
        company_short_name=identity.get("company_short_name", DEFAULT_LOGIN_IDENTITY["company_short_name"]),
        login_message=identity.get("login_message", DEFAULT_LOGIN_IDENTITY["login_message"]),
        menu_position=(identity.get("menu_position") or DEFAULT_LOGIN_IDENTITY["menu_position"]).strip().lower(),
        favicon_url=favicon_url,
        logo_url=logo_url,
        login_logo_url=login_logo_url,
        desktop_bg_url=desktop_bg_url,
        mobile_bg_url=mobile_bg_url,
        loaded_assets=loaded_assets,
        consistency=consistency,
    )
    return render_backend_page(
        request,
        title="Identidad institucional",
        description="Configuración de identidad para la pantalla de login.",
        content=content,
        hide_floating_actions=True,
        show_page_header=True,
    )


def _render_empresa_usuarios_shell(
    request: Request,
    *,
    initial_section: str,
    title: str,
    description: str,
    permission: str,
) -> HTMLResponse:
    _require_empresa_permission(request, permission)
    template = get_templates().env.get_template("modulos/empresa/usuarios.html")
    content = template.render(initial_section=initial_section)
    return render_backend_page(
        request,
        title=title,
        description=description,
        content=content,
        show_page_header=True,
    )


@router.get("/identidad-institucional/css/identidad_institucional.css")
def identidad_institucional_css():
    return FileResponse(_CSS_PATH, media_type="text/css")


@router.get("/identidad-institucional", response_class=HTMLResponse)
def identidad_institucional_page(request: Request):
    _require_empresa_permission(request, "ver_branding")
    return _render_identidad_institucional_page(request)


@router.get("/identidad-institucional/", response_class=HTMLResponse)
def identidad_institucional_page_slash(request: Request):
    _require_empresa_permission(request, "ver_branding")
    return RedirectResponse(url="/identidad-institucional", status_code=307)


@router.post("/identidad-institucional", response_class=HTMLResponse)
async def identidad_institucional_save(
    request: Request,
    company_short_name: str = Form(""),
    login_message: str = Form(""),
    menu_position: str = Form("arriba"),
    favicon: Optional[UploadFile] = File(None),
    logo_empresa: Optional[UploadFile] = File(None),
    logo_login: Optional[UploadFile] = File(None),
    fondo_escritorio: Optional[UploadFile] = File(None),
    fondo_movil: Optional[UploadFile] = File(None),
    remove_favicon: str = Form("0"),
    remove_logo: str = Form("0"),
    remove_login_logo: str = Form("0"),
    remove_desktop: str = Form("0"),
    remove_mobile: str = Form("0"),
):
    _require_empresa_permission(request, "editar_branding")
    form = IdentidadForm(
        company_short_name=company_short_name,
        login_message=login_message,
        menu_position=menu_position if menu_position in ("arriba", "abajo") else "arriba",
    )

    current = _load_login_identity()
    current["company_short_name"] = form.company_short_name or DEFAULT_LOGIN_IDENTITY["company_short_name"]
    current["login_message"] = form.login_message or DEFAULT_LOGIN_IDENTITY["login_message"]
    current["menu_position"] = form.menu_position

    if str(remove_favicon).strip() == "1":
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = DEFAULT_LOGIN_IDENTITY["favicon_filename"]
    if str(remove_logo).strip() == "1":
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = DEFAULT_LOGIN_IDENTITY["logo_filename"]
    if str(remove_login_logo).strip() == "1":
        remove_login_image_if_custom(current.get("login_logo_filename"))
        current["login_logo_filename"] = current.get("logo_filename") or DEFAULT_LOGIN_IDENTITY["logo_filename"]
    if str(remove_desktop).strip() == "1":
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"]
    if str(remove_mobile).strip() == "1":
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"]

    new_favicon = await store_login_image(favicon, "favicon") if favicon else None
    if new_favicon:
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = new_favicon

    new_logo = await store_login_image(logo_empresa, "logo_empresa") if logo_empresa else None
    if new_logo:
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = new_logo

    new_login_logo = await store_login_image(logo_login, "logo_login") if logo_login else None
    if new_login_logo:
        remove_login_image_if_custom(current.get("login_logo_filename"))
        current["login_logo_filename"] = new_login_logo

    new_desktop = await store_login_image(fondo_escritorio, "fondo_escritorio") if fondo_escritorio else None
    if new_desktop:
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = new_desktop

    new_mobile = await store_login_image(fondo_movil, "fondo_movil") if fondo_movil else None
    if new_mobile:
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = new_mobile

    save_login_identity(current)
    clear_frontend_page_cache()
    return RedirectResponse(url="/identidad-institucional?saved=1", status_code=303)


@router.get("/empresa/usuarios", response_class=HTMLResponse)
def empresa_usuarios_page(request: Request):
    return _render_empresa_usuarios_shell(
        request,
        initial_section="usuarios",
        title="Usuarios",
        description="Gestión de usuarios y permisos de acceso.",
        permission="ver_usuarios",
    )


@router.get("/empresa/usuarios/roles", response_class=HTMLResponse)
def empresa_roles_page(request: Request):
    return _render_empresa_usuarios_shell(
        request,
        initial_section="roles",
        title="Roles",
        description="Perfiles base de roles y permisos.",
        permission="ver_acceso",
    )


@router.get("/empresa/acceso", response_class=HTMLResponse)
@router.get("/empresa/usuarios/acceso", response_class=HTMLResponse)
def empresa_acceso_page(request: Request):
    return _render_empresa_usuarios_shell(
        request,
        initial_section="acceso",
        title="Niveles de acceso",
        description="Perfiles de rol y niveles de acceso por módulo.",
        permission="ver_acceso",
    )


_PLACEHOLDER_CONTENT = """
<section class="w-full flex flex-col items-center justify-center" style="min-height:260px;gap:1rem;">
  <i class="{icon}" style="font-size:3rem;opacity:0.25;"></i>
  <p style="font-size:1rem;opacity:0.5;margin:0;">{label}</p>
  <p style="font-size:0.85rem;opacity:0.35;margin:0;">Próximamente disponible.</p>
</section>
"""


@router.get("/empresa/MAIN-datos", response_class=HTMLResponse)
def empresa_main_datos_page(request: Request):
    _require_empresa_permission(request, "ver_datos")
    return RedirectResponse(url="/empresa/base-datos", status_code=307)


@router.get("/plantillas", response_class=HTMLResponse)
def plantillas_page(request: Request):
    _require_empresa_permission(request, "ver_plantillas")
    content = _PLACEHOLDER_CONTENT.format(icon="fa-solid fa-file-alt", label="Plantillas")
    return render_backend_page(
        request,
        title="Plantillas",
        description="Gestión de plantillas del sistema.",
        content=content,
        show_page_header=True,
    )


@router.get("/plantillas/constructor", response_class=HTMLResponse)
def plantillas_constructor_page(request: Request):
    _require_empresa_permission(request, "editar_plantillas")
    content = _PLACEHOLDER_CONTENT.format(icon="fa-solid fa-tools", label="Constructor de formularios")
    return render_backend_page(
        request,
        title="Constructor de formularios",
        description="Constructor visual de formularios y plantillas.",
        content=content,
        show_page_header=True,
    )


# ── /api/colaboradores ────────────────────────────────────────────────────────

_COLABORADOR_EXTRA_COLS = {
    "app_access": "TEXT",
    "menu_blocks": "TEXT",
    "conversation_access": "TEXT",
    "is_employee": "BOOLEAN DEFAULT 0",
}


def _ensure_colaborador_cols() -> None:
    """Agrega columnas extendidas a la tabla users si no existen."""
    try:
        info = get_current_database_info()
        db_path = info.get("path") or ""
        db_url = info.get("url") or ""
        if not db_url.startswith("sqlite:///") or not db_path:
            return
        with sqlite3.connect(db_path) as conn:
            existing = {row[1] for row in conn.execute('PRAGMA table_info("users")').fetchall()}
            for col, col_type in _COLABORADOR_EXTRA_COLS.items():
                if col not in existing:
                    conn.execute(f'ALTER TABLE "users" ADD COLUMN "{col}" {col_type}')
    except Exception:
        pass


def _serialize_user(u: Usuario) -> dict[str, Any]:
    nombre = decrypt_sensitive(u.full_name) or decrypt_sensitive(u.usuario) or ""
    raw_app_access = getattr(u, "app_access", None)
    raw_conversation_access = getattr(u, "conversation_access", None)
    return {
        "id": u.id,
        "nombre": nombre,
        "usuario": decrypt_sensitive(u.usuario) or "",
        "correo": decrypt_sensitive(u.correo) or "",
        "celular": str(u.celular or ""),
        "departamento": str(u.departamento or ""),
        "puesto": str(u.puesto or ""),
        "jefe_inmediato_id": u.jefe_inmediato_id,
        "imagen": str(u.imagen or ""),
        "rol": normalize_role_name(u.role),
        "is_active": bool(u.is_active if u.is_active is not None else True),
        "totp_enabled": bool(u.totp_enabled),
        "is_employee": bool(getattr(u, "is_employee", False)),
        "app_access": _parse_json_field(getattr(u, "app_access", None)),
        "menu_blocks": _parse_json_field(getattr(u, "menu_blocks", None)),
        "conversation_access": _parse_json_field(getattr(u, "conversation_access", None)),
        "app_access_levels": _parse_json_field(getattr(u, "app_access", None)),
        "inherit_role_permissions": not bool(str(raw_app_access or "").strip()) and not bool(str(raw_conversation_access or "").strip()),
    }


def _parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


@router.get("/api/colaboradores")
def api_colaboradores_list(request: Request):
    _require_empresa_permission(request, "ver_usuarios")
    _ensure_colaborador_cols()
    db = SessionLocal()
    try:
        users = db.query(Usuario).order_by(Usuario.id).all()
        data = [_serialize_user(u) for u in users]
        roles = get_visible_role_names(request)
        installed = get_active_app_access_names()
        return JSONResponse({
            "success": True,
            "data": data,
            "assignable_roles": roles,
            "role_profiles": get_role_permission_catalog(request),
            "installed_app_options": installed,
        })
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
    finally:
        db.close()


class ColaboradorPayload(BaseModel):
    id: Optional[int] = None
    nombre: str = ""
    usuario: str = ""
    correo: str = ""
    contrasena: Optional[str] = None
    empleado: bool = False
    totp_enabled: bool = False
    rol: str = "usuario"
    app_access: Optional[Any] = None
    app_access_levels: Optional[Any] = None
    menu_blocks: Optional[Any] = None
    conversation_access: Optional[Any] = None
    inherit_role_permissions: bool = True
    departamento: str = ""
    puesto: str = ""
    celular: str = ""
    jefe_inmediato_id: Optional[int] = None
    imagen: str = ""


@router.post("/api/colaboradores")
def api_colaboradores_save(request: Request, payload: ColaboradorPayload):
    _require_empresa_permission(request, "gestionar_usuarios")
    _ensure_colaborador_cols()

    nombre = (payload.nombre or "").strip()
    usuario = (payload.usuario or "").strip()
    correo = (payload.correo or "").strip()
    rol = normalize_role_name(payload.rol)
    if not can_assign_role(request, rol):
        return JSONResponse({"success": False, "error": "No puedes asignar ese rol."}, status_code=403)

    if not usuario:
        return JSONResponse({"success": False, "error": "El campo usuario es obligatorio."}, status_code=422)

    inherit_role_permissions = bool(payload.inherit_role_permissions)
    app_access_val = None if inherit_role_permissions else (payload.app_access_levels or payload.app_access)
    app_access_json = json.dumps(app_access_val) if app_access_val is not None else None
    menu_blocks_json = json.dumps(payload.menu_blocks) if payload.menu_blocks is not None else None
    conv_json = json.dumps(payload.conversation_access) if (not inherit_role_permissions and payload.conversation_access is not None) else None

    db = SessionLocal()
    try:
        if payload.id:
            u = db.query(Usuario).filter(Usuario.id == payload.id).first()
            if not u:
                return JSONResponse({"success": False, "error": "Usuario no encontrado."}, status_code=404)
            u.full_name = encrypt_sensitive(nombre) if nombre else u.full_name
            if usuario:
                u.usuario = encrypt_sensitive(usuario)
                u.usuario_hash = sensitive_lookup_hash(usuario)
            if correo:
                u.correo = encrypt_sensitive(correo)
                u.correo_hash = sensitive_lookup_hash(correo)
            if payload.contrasena:
                u.contrasena = hash_password(payload.contrasena)
            u.role = rol
            u.departamento = payload.departamento or u.departamento
            u.puesto = payload.puesto or u.puesto
            u.celular = payload.celular or u.celular
            u.jefe_inmediato_id = payload.jefe_inmediato_id or u.jefe_inmediato_id
            u.imagen = payload.imagen or u.imagen
            u.totp_enabled = payload.totp_enabled
            if hasattr(u, "is_employee"):
                u.is_employee = payload.empleado
            if hasattr(u, "app_access"):
                u.app_access = app_access_json
            if menu_blocks_json is not None and hasattr(u, "menu_blocks"):
                u.menu_blocks = menu_blocks_json
            if hasattr(u, "conversation_access"):
                u.conversation_access = conv_json
        else:
            if not payload.contrasena:
                return JSONResponse({"success": False, "error": "La contraseña es obligatoria para nuevos usuarios."}, status_code=422)
            existing = db.query(Usuario).filter(Usuario.usuario_hash == sensitive_lookup_hash(usuario)).first()
            if existing:
                return JSONResponse({"success": False, "error": f"El usuario '{usuario}' ya existe."}, status_code=409)
            u = Usuario(
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
            )
            if hasattr(u, "is_employee"):
                u.is_employee = payload.empleado
            if hasattr(u, "app_access"):
                u.app_access = app_access_json
            if menu_blocks_json is not None and hasattr(u, "menu_blocks"):
                u.menu_blocks = menu_blocks_json
            if hasattr(u, "conversation_access"):
                u.conversation_access = conv_json
            db.add(u)

        db.commit()
        db.refresh(u)
        return JSONResponse({"success": True, "data": _serialize_user(u)})
    except Exception as exc:
        db.rollback()
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
    finally:
        db.close()


class RolePermissionProfilePayload(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=255)
    screen_access_levels: Optional[Any] = None
    conversation_access: Optional[Any] = None
    backend_roles: Optional[Any] = None
    permission_flags: Optional[Any] = None

    @field_validator("role_name", "description", mode="before")
    @classmethod
    def strip_profile_fields(cls, value: str) -> str:
        return str(value or "").strip()


@router.get("/api/roles-permisos")
def api_role_permission_profiles(request: Request):
    _require_empresa_permission(request, "ver_acceso")
    return JSONResponse({"success": True, "data": get_role_permission_catalog(request)})


@router.post("/api/roles-permisos")
def api_role_permission_profiles_save(request: Request, payload: RolePermissionProfilePayload):
    _require_empresa_permission(request, "gestionar_acceso")
    role_name = normalize_role_name(payload.role_name)
    if role_name in {"superadministrador", "administrador_multiempresa"} and not is_superadmin(request):
        return JSONResponse({"success": False, "error": "No puedes administrar ese rol."}, status_code=403)
    if not can_assign_role(request, role_name) and role_name not in {"autoridades", "departamento", "usuario", "administrador"}:
        if not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No puedes administrar ese rol."}, status_code=403)
    elif not can_assign_role(request, role_name):
        return JSONResponse({"success": False, "error": "No puedes administrar ese rol."}, status_code=403)
    profile = save_role_permission_profile(
        role_name=role_name,
        description=payload.description,
        screen_access_levels=payload.screen_access_levels,
        conversation_access=payload.conversation_access,
        backend_roles=payload.backend_roles,
        permission_flags=payload.permission_flags,
    )
    return JSONResponse({"success": True, "data": profile})


@router.get("/api/screen-access-catalog")
def api_screen_access_catalog(request: Request):
    """Devuelve el catálogo de pantallas y niveles de acceso de todos los módulos instalados."""
    _require_empresa_permission(request, "ver_acceso")
    catalog: dict[str, Any] = {}
    try:
        for item in list_modules_payload():
            key = str(item.get("key") or "")
            screens = item.get("screen_access_levels")
            if isinstance(screens, dict) and screens:
                catalog[key] = {
                    "module_label": str(item.get("label") or key),
                    "screens": screens,
                }
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
    return JSONResponse({"success": True, "data": catalog})
