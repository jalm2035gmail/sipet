"""
Adaptadores y dependencias compartidas para el módulo de capacitación.

Proporciona funciones auxiliares para:
- Autenticación y autorización
- Gestión de tenants
- Acceso a datos de colaboradores
- Integración con otros módulos
- Renderizado de páginas backend
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import (
    render_backend_page
)
from fastapi_modulo.modulos_sipet.web.repositorios.core_repository import (
    find_user_by_login
)
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_user_screen_access_levels,
    get_user_app_access,
    is_admin_or_superadmin as web_is_admin_or_superadmin,
    sensitive_lookup_hash
)
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import (
    decrypt_sensitive,
    find_user_by_id
)
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import (
    require_app_access
)
from fastapi_modulo.modulos_sipet.web.servicios.session_service import (
    AUTH_COOKIE_NAME,
    read_session_cookie
)
from fastapi_modulo.modulos.capacitacion.modelos.enums import PermisoCapacitacion, RolCapacitacion


# ============================================================================
# CONSTANTES
# ============================================================================

# Roles considerados como administradores en el módulo de capacitación
CAP_ADMIN_ROLES = {
    "superadministrador",
    "superadmin",
    "administrador",
    "administrador_multiempresa",
    "admin_capacitacion"
}

# Nombre del módulo para verificación de acceso
MODULE_NAME = "Capacitacion"
MODULE_ACCESS_ALIASES = {"capacitacion", "capacitación", MODULE_NAME.lower()}
CAP_SCREEN_KEYS = ("capacitacion", "Capacitacion", "Capacitación")

# Mensaje de acceso denegado
ACCESS_DENIED_MESSAGE = "Acceso restringido al módulo de Capacitación"
CAP_PERMISSION_KEYS = tuple(permission.value for permission in PermisoCapacitacion)
CAP_VIEW_PERMISSION_KEYS = {
    PermisoCapacitacion.VER.value,
    PermisoCapacitacion.CATALOGO_VER.value,
    PermisoCapacitacion.DASHBOARD_VER.value,
    PermisoCapacitacion.PRESENTACIONES_VER.value,
    PermisoCapacitacion.CERTIFICADOS_VER.value,
    PermisoCapacitacion.AUDITORIA_VER.value,
}


# ============================================================================
# NORMALIZACIÓN DE TENANT
# ============================================================================

def normalize_tenant_id(value: Optional[str]) -> str:
    """
    Normaliza un ID de tenant a un formato válido.
    
    Args:
        value: ID de tenant a normalizar
        
    Returns:
        ID de tenant normalizado
        
    Examples:
        >>> normalize_tenant_id("Mi Empresa!")
        'mi-empresa'
        >>> normalize_tenant_id(None)
        'default'
        >>> normalize_tenant_id("  Test_123  ")
        'test_123'
    """
    # Convertir a string y limpiar
    raw = str(value or "").strip().lower()
    
    # Construir string normalizado
    cleaned = []
    for ch in raw:
        if ch.isalnum() or ch in "._-":
            cleaned.append(ch)
        else:
            cleaned.append("-")
    
    # Unir y limpiar bordes
    normalized = "".join(cleaned).strip("-._")
    
    # Retornar normalizado o default
    return normalized or "default"


# ============================================================================
# FUNCIONES DE ROLES Y PERMISOS
# ============================================================================

def current_role(request: Request) -> str:
    """
    Obtiene el rol actual del usuario desde la request.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Rol del usuario en minúsculas
        
    Examples:
        >>> # request con rol en state
        >>> current_role(request)
        'administrador'
    """
    # Intentar obtener desde request.state
    role = getattr(request.state, "user_role", None)
    
    # Si no está en state, buscar en cookies
    if not role:
        role = (
            request.cookies.get("user_role") or
            request.cookies.get("role") or
            request.cookies.get("rol")
        )
    
    return str(role or "").strip().lower()


def is_admin_or_superadmin(request: Request) -> bool:
    """
    Verifica si el usuario actual es administrador o superadministrador.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        True si el usuario es admin o superadmin
        
    Examples:
        >>> is_admin_or_superadmin(request)
        True
    """
    # Verificar rol en el módulo de capacitación
    if current_role(request) in CAP_ADMIN_ROLES:
        return True
    
    # Verificar rol global en el sistema
    return web_is_admin_or_superadmin(request)


def user_has_capacitacion_access(request: Request) -> bool:
    """
    Verifica si el usuario tiene acceso al módulo de capacitación.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        True si el usuario tiene acceso
        
    Examples:
        >>> user_has_capacitacion_access(request)
        True
    """
    # Los administradores siempre tienen acceso
    if is_admin_or_superadmin(request):
        return True
    
    user_apps = {str(item).strip().lower() for item in get_user_app_access(request)}
    if user_apps & MODULE_ACCESS_ALIASES:
        return True
    permissions = get_capacitacion_permissions(request)
    return any(bool(permissions.get(permission_key)) for permission_key in CAP_VIEW_PERMISSION_KEYS)


def require_access(request: Request) -> None:
    """
    Requiere acceso al módulo de capacitación o lanza excepción.
    
    Args:
        request: Request de FastAPI
        
    Raises:
        HTTPException: Si el usuario no tiene acceso (403)
        
    Examples:
        >>> require_access(request)  # No lanza excepción si tiene acceso
        >>> require_access(request)  # HTTPException si no tiene acceso
    """
    if not user_has_capacitacion_access(request):
        raise HTTPException(status_code=403, detail=ACCESS_DENIED_MESSAGE)


def require_admin_access(request: Request) -> None:
    """
    Requiere acceso de administrador o lanza excepción.
    
    Args:
        request: Request de FastAPI
        
    Raises:
        HTTPException: Si el usuario no es administrador (403)
        
    Examples:
        >>> require_admin_access(request)
    """
    if not is_admin_or_superadmin(request):
        raise HTTPException(
            status_code=403,
            detail="Se requieren permisos de administrador"
        )


def _screen_permission_enabled(request: Request, permission_key: str) -> bool:
    if is_admin_or_superadmin(request):
        return True
    access_levels = get_user_screen_access_levels(request)
    entry = access_levels.get(permission_key) or {}
    if isinstance(entry, bool):
        return entry
    if not isinstance(entry, dict):
        return False
    return any(
        bool(entry.get(level_key, False))
        for level_key in ("full_access", "read_only", "department_only", "user_only", "special_permissions")
    )


def _find_cap_screen_entry(request: Request) -> Any:
    access_levels = get_user_screen_access_levels(request)
    for key in CAP_SCREEN_KEYS:
        if key in access_levels:
            return access_levels.get(key)
    return None


def _empty_cap_permissions() -> Dict[str, bool]:
    return {permission_key: False for permission_key in CAP_PERMISSION_KEYS}


def current_cap_role(request: Request) -> str:
    if is_admin_or_superadmin(request):
        return RolCapacitacion.ADMIN.value
    access_levels = get_user_screen_access_levels(request)
    for permission_key in CAP_PERMISSION_KEYS:
        entry = access_levels.get(permission_key)
        if isinstance(entry, dict) and bool(entry.get("special_permissions")):
            return RolCapacitacion.COORDINADOR.value
    entry = _find_cap_screen_entry(request)
    if isinstance(entry, bool):
        return RolCapacitacion.ADMIN.value if entry else RolCapacitacion.COLABORADOR.value
    if isinstance(entry, dict):
        if bool(entry.get("full_access")):
            return RolCapacitacion.ADMIN.value
        if bool(entry.get("special_permissions")):
            return RolCapacitacion.COORDINADOR.value
        if bool(entry.get("department_only")):
            return RolCapacitacion.INSTRUCTOR.value
        if bool(entry.get("read_only")):
            return RolCapacitacion.LECTOR.value
        if bool(entry.get("user_only")):
            return RolCapacitacion.COLABORADOR.value
    if user_has_capacitacion_access_from_app(request):
        return RolCapacitacion.COLABORADOR.value
    return RolCapacitacion.COLABORADOR.value


def user_has_capacitacion_access_from_app(request: Request) -> bool:
    user_apps = {str(item).strip().lower() for item in get_user_app_access(request)}
    return bool(user_apps & MODULE_ACCESS_ALIASES)


def get_capacitacion_permissions(request: Request) -> Dict[str, bool]:
    if is_admin_or_superadmin(request):
        return {permission_key: True for permission_key in CAP_PERMISSION_KEYS}

    explicit = {permission_key: _screen_permission_enabled(request, permission_key) for permission_key in CAP_PERMISSION_KEYS}
    if any(explicit.values()):
        if any(
            explicit[key]
            for key in (
                PermisoCapacitacion.CATALOGO_EDITAR.value,
                PermisoCapacitacion.INSCRIPCIONES_GESTIONAR.value,
                PermisoCapacitacion.EVALUACIONES_GESTIONAR.value,
                PermisoCapacitacion.PRESENTACIONES_GESTIONAR.value,
                PermisoCapacitacion.GAMIFICACION_GESTIONAR.value,
            )
        ):
            explicit[PermisoCapacitacion.VER.value] = True
        if explicit[PermisoCapacitacion.CATALOGO_EDITAR.value]:
            explicit[PermisoCapacitacion.CATALOGO_VER.value] = True
        if explicit[PermisoCapacitacion.PRESENTACIONES_GESTIONAR.value]:
            explicit[PermisoCapacitacion.PRESENTACIONES_VER.value] = True
        if explicit[PermisoCapacitacion.AUTOGESTION_INSCRIBIRSE.value] or explicit[PermisoCapacitacion.AUTOGESTION_PROGRESO.value]:
            explicit[PermisoCapacitacion.CATALOGO_VER.value] = True
            explicit[PermisoCapacitacion.VER.value] = True
        if explicit[PermisoCapacitacion.CERTIFICADOS_VER.value]:
            explicit[PermisoCapacitacion.VER.value] = True
        return explicit

    permissions = _empty_cap_permissions()
    entry = _find_cap_screen_entry(request)
    if isinstance(entry, bool):
        return {permission_key: entry for permission_key in CAP_PERMISSION_KEYS}

    if isinstance(entry, dict):
        full = bool(entry.get("full_access"))
        special = bool(entry.get("special_permissions"))
        department = bool(entry.get("department_only"))
        read_only = bool(entry.get("read_only"))
        user_only = bool(entry.get("user_only"))
        if full:
            return {permission_key: True for permission_key in CAP_PERMISSION_KEYS}

        if special:
            for permission_key in (
                PermisoCapacitacion.VER.value,
                PermisoCapacitacion.CATALOGO_VER.value,
                PermisoCapacitacion.CATALOGO_EDITAR.value,
                PermisoCapacitacion.DASHBOARD_VER.value,
                PermisoCapacitacion.INSCRIPCIONES_GESTIONAR.value,
                PermisoCapacitacion.AUTOGESTION_INSCRIBIRSE.value,
                PermisoCapacitacion.AUTOGESTION_PROGRESO.value,
                PermisoCapacitacion.AUTOGESTION_EVALUACIONES.value,
                PermisoCapacitacion.EVALUACIONES_GESTIONAR.value,
                PermisoCapacitacion.PRESENTACIONES_VER.value,
                PermisoCapacitacion.PRESENTACIONES_GESTIONAR.value,
                PermisoCapacitacion.GAMIFICACION_GESTIONAR.value,
                PermisoCapacitacion.CERTIFICADOS_VER.value,
                PermisoCapacitacion.AUDITORIA_VER.value,
            ):
                permissions[permission_key] = True
            return permissions

        if department:
            for permission_key in (
                PermisoCapacitacion.VER.value,
                PermisoCapacitacion.CATALOGO_VER.value,
                PermisoCapacitacion.DASHBOARD_VER.value,
                PermisoCapacitacion.INSCRIPCIONES_GESTIONAR.value,
                PermisoCapacitacion.AUTOGESTION_INSCRIBIRSE.value,
                PermisoCapacitacion.AUTOGESTION_PROGRESO.value,
                PermisoCapacitacion.AUTOGESTION_EVALUACIONES.value,
                PermisoCapacitacion.PRESENTACIONES_VER.value,
                PermisoCapacitacion.CERTIFICADOS_VER.value,
                PermisoCapacitacion.AUDITORIA_VER.value,
            ):
                permissions[permission_key] = True
            return permissions

        if read_only:
            for permission_key in (
                PermisoCapacitacion.VER.value,
                PermisoCapacitacion.CATALOGO_VER.value,
                PermisoCapacitacion.DASHBOARD_VER.value,
                PermisoCapacitacion.PRESENTACIONES_VER.value,
                PermisoCapacitacion.CERTIFICADOS_VER.value,
                PermisoCapacitacion.AUDITORIA_VER.value,
            ):
                permissions[permission_key] = True
            return permissions

        if user_only:
            for permission_key in (
                PermisoCapacitacion.VER.value,
                PermisoCapacitacion.CATALOGO_VER.value,
                PermisoCapacitacion.AUTOGESTION_INSCRIBIRSE.value,
                PermisoCapacitacion.AUTOGESTION_PROGRESO.value,
                PermisoCapacitacion.AUTOGESTION_EVALUACIONES.value,
                PermisoCapacitacion.PRESENTACIONES_VER.value,
                PermisoCapacitacion.CERTIFICADOS_VER.value,
            ):
                permissions[permission_key] = True
            return permissions

    if user_has_capacitacion_access_from_app(request):
        for permission_key in (
            PermisoCapacitacion.VER.value,
            PermisoCapacitacion.CATALOGO_VER.value,
            PermisoCapacitacion.AUTOGESTION_INSCRIBIRSE.value,
            PermisoCapacitacion.AUTOGESTION_PROGRESO.value,
            PermisoCapacitacion.AUTOGESTION_EVALUACIONES.value,
            PermisoCapacitacion.PRESENTACIONES_VER.value,
            PermisoCapacitacion.CERTIFICADOS_VER.value,
        ):
            permissions[permission_key] = True
    return permissions


def require_cap_permission(request: Request, permission_key: PermisoCapacitacion | str, detail: Optional[str] = None) -> None:
    key = permission_key.value if isinstance(permission_key, PermisoCapacitacion) else str(permission_key)
    permissions = get_capacitacion_permissions(request)
    if not permissions.get(key, False):
        raise HTTPException(status_code=403, detail=detail or "No tienes permiso para realizar esta acción en Capacitación.")


def get_capacitacion_access_payload(request: Request) -> Dict[str, Any]:
    permissions = get_capacitacion_permissions(request)
    return {
        "module": MODULE_NAME,
        "role": current_cap_role(request),
        "tenant_id": get_current_tenant(request),
        "has_access": user_has_capacitacion_access(request),
        "is_admin": is_admin_or_superadmin(request),
        "permissions": permissions,
    }


# ============================================================================
# FUNCIONES DE TENANT
# ============================================================================

def get_current_tenant(request: Request) -> str:
    """
    Obtiene el tenant actual desde la request.
    
    Busca en el siguiente orden:
    1. request.state.tenant_id
    2. Cookie tenant_id
    3. Header x-tenant-id (solo para admins)
    4. Default
    
    Args:
        request: Request de FastAPI
        
    Returns:
        ID del tenant normalizado
        
    Examples:
        >>> get_current_tenant(request)
        'empresa-abc'
    """
    # 1. Verificar en request.state
    tenant = getattr(request.state, "tenant_id", None)
    if tenant:
        return normalize_tenant_id(tenant)
    
    # 2. Verificar en cookies
    cookie_tenant = request.cookies.get("tenant_id")
    if cookie_tenant:
        return normalize_tenant_id(cookie_tenant)
    
    # 3. Verificar en headers (solo para admins)
    header_tenant = request.headers.get("x-tenant-id")
    if header_tenant and is_admin_or_superadmin(request):
        return normalize_tenant_id(header_tenant)
    
    # 4. Retornar default
    return normalize_tenant_id("default")


# ============================================================================
# FUNCIONES DE SESIÓN Y USUARIO
# ============================================================================

def current_session_name(request: Request) -> str:
    """
    Obtiene el nombre de sesión (username) del usuario actual.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Nombre de usuario/sesión
        
    Examples:
        >>> current_session_name(request)
        'usuario@example.com'
    """
    # Intentar obtener desde request.state
    session_name = getattr(request.state, "user_name", None)
    
    # Si no está en state, buscar en cookies
    if not session_name:
        session_name = (
            request.cookies.get("user_name") or
            request.cookies.get("username") or
            request.cookies.get("usuario") or
            request.cookies.get("email")
        )
    
    session_name = str(session_name or "").strip()
    
    # Si ya tenemos session_name, retornar
    if session_name:
        return session_name
    
    # Intentar obtener desde el token de sesión
    session_token = request.cookies.get(AUTH_COOKIE_NAME, "")
    if session_token:
        session_data = read_session_cookie(session_token)
        if isinstance(session_data, dict):
            username = str(session_data.get("username") or "").strip()
            if username:
                return username
    
    return ""


def current_user_key(request: Request) -> str:
    """
    Obtiene la clave única del usuario actual.
    
    Preferencia:
    1. ID de usuario desde la base de datos
    2. Nombre de sesión
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Clave única del usuario
        
    Raises:
        HTTPException: Si no hay usuario autenticado (401)
        
    Examples:
        >>> current_user_key(request)
        '123'
    """
    session_name = current_session_name(request)
    
    db = core_db.SessionLocal()
    try:
        # Intentar obtener user_id desde la sesión
        session_token = request.cookies.get(AUTH_COOKIE_NAME, "")
        session_data = read_session_cookie(session_token) if session_token else None
        
        user = None
        
        # Buscar por user_id si está disponible
        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                try:
                    user = find_user_by_id(db, int(user_id))
                except (ValueError, TypeError):
                    user = None
        
        # Si no se encontró, buscar por session_name
        if not user and session_name:
            user = find_user_by_login(
                db,
                login_value=session_name,
                login_hash=sensitive_lookup_hash(session_name)
            )
        
        # Si se encontró el usuario, retornar su ID
        if user:
            return str(user.id)
        
    finally:
        db.close()
    
    # Si tenemos session_name pero no encontramos usuario, usar session_name
    if session_name:
        return session_name
    
    # Si no hay nada, usuario no autenticado
    raise HTTPException(
        status_code=401,
        detail="No autenticado"
    )


def current_user_name(request: Request) -> str:
    """
    Obtiene el nombre completo del usuario actual.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Nombre completo del usuario o username si no hay nombre
        
    Examples:
        >>> current_user_name(request)
        'Juan Pérez'
    """
    session_name = current_session_name(request)
    
    if not session_name:
        return "Usuario"
    
    user_row = find_user_row_by_session_name(session_name)
    
    if user_row:
        return user_row.get("full_name") or user_row.get("username") or session_name
    
    return session_name


def find_user_row_by_session_name(session_name: str) -> Optional[Dict[str, Any]]:
    """
    Encuentra los datos de un usuario por su nombre de sesión.
    
    Args:
        session_name: Nombre de sesión del usuario
        
    Returns:
        Diccionario con datos del usuario o None
        
    Examples:
        >>> find_user_row_by_session_name('user@example.com')
        {'id': 1, 'username': 'user@example.com', 'full_name': 'Usuario', 'role': 'admin'}
    """
    value = str(session_name or "").strip().lower()
    
    if not value:
        return None
    
    db = core_db.SessionLocal()
    try:
        user = find_user_by_login(
            db,
            login_value=value,
            login_hash=sensitive_lookup_hash(value)
        )
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": decrypt_sensitive(user.usuario) or "",
            "full_name": user.full_name or "",
            "role": user.role or "",
        }
        
    finally:
        db.close()


# ============================================================================
# FUNCIONES DE DATOS DE COLABORADORES
# ============================================================================

def load_colab_meta() -> Dict[str, Any]:
    """
    Carga metadata de colaboradores desde archivo JSON.
    
    Returns:
        Diccionario con metadata de colaboradores
        
    Examples:
        >>> meta = load_colab_meta()
        >>> meta.get('user123', {}).get('departamento')
        'TI'
    """
    # Determinar entorno
    app_env = (
        os.environ.get("APP_ENV") or
        os.environ.get("ENVIRONMENT") or
        "development"
    ).strip().lower()
    
    # Determinar directorio de datos
    sipet_data_dir = (
        os.environ.get("SIPET_DATA_DIR") or
        os.path.expanduser("~/.sipet/data")
    ).strip()
    
    # Determinar directorio runtime
    runtime_dir = (
        os.environ.get("RUNTIME_STORE_DIR") or
        os.path.join(sipet_data_dir, "runtime_store", app_env)
    ).strip()
    
    # Determinar ruta del archivo de metadata
    meta_path = (
        os.environ.get("COLAB_META_PATH") or
        os.path.join(runtime_dir, "colaboradores_meta.json")
    )
    
    # Intentar cargar el archivo
    try:
        with open(meta_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        
        # Validar que sea un diccionario
        return payload if isinstance(payload, dict) else {}
        
    except FileNotFoundError:
        # Archivo no existe, retornar diccionario vacío
        return {}
    except json.JSONDecodeError as e:
        # JSON inválido
        import logging
        logging.warning(f"JSON inválido en {meta_path}: {e}")
        return {}
    except Exception as e:
        # Otro error
        import logging
        logging.error(f"Error al cargar metadata de colaboradores: {e}")
        return {}


def get_colaborador_info(colaborador_key: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información de un colaborador desde la metadata.
    
    Args:
        colaborador_key: Identificador del colaborador
        
    Returns:
        Diccionario con información del colaborador o None
        
    Examples:
        >>> info = get_colaborador_info('user123')
        >>> info.get('departamento')
        'TI'
    """
    meta = load_colab_meta()
    return meta.get(colaborador_key)


# ============================================================================
# FUNCIONES DE RENDERIZADO
# ============================================================================

def render_backend_page_safe(
    request: Request,
    *,
    title: str,
    description: str = "",
    content: str = "",
    hide_floating_actions: bool = True,
    show_page_header: bool = False,
    section_label: str = "Capacitación",
    breadcrumbs: Optional[List[Dict[str, str]]] = None
) -> HTMLResponse:
    """
    Renderiza una página del backend de forma segura.
    
    Args:
        request: Request de FastAPI
        title: Título de la página
        description: Descripción de la página
        content: Contenido HTML de la página
        hide_floating_actions: Si debe ocultar acciones flotantes
        show_page_header: Si debe mostrar header de página
        section_label: Etiqueta de la sección
        breadcrumbs: Breadcrumbs personalizados
        
    Returns:
        HTMLResponse con la página renderizada
        
    Examples:
        >>> response = render_backend_page_safe(
        ...     request,
        ...     title="Cursos",
        ...     content="<div>Contenido</div>"
        ... )
    """
    return render_backend_page(
        request,
        title=title,
        description=description,
        content=content,
        hide_floating_actions=hide_floating_actions,
        show_page_header=show_page_header,
        section_label=section_label,
    )


# ============================================================================
# INTEGRACIÓN CON MÓDULO DE ENCUESTAS
# ============================================================================

def list_live_course_surveys_safe(
    curso_id: int,
    tenant_id: str
) -> List[Dict[str, Any]]:
    """
    Lista encuestas activas de un curso de forma segura.
    
    Integración opcional con el módulo de encuestas.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        
    Returns:
        Lista de encuestas activas o lista vacía si hay error
        
    Examples:
        >>> surveys = list_live_course_surveys_safe(123, 'default')
        >>> len(surveys)
        2
    """
    try:
        from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
            list_live_course_surveys
        )
        
        rows = list_live_course_surveys(curso_id, tenant_id)
        
        return rows if isinstance(rows, list) else []
        
    except ImportError:
        # Módulo de encuestas no disponible
        return []
    except Exception as e:
        # Otro error
        import logging
        logging.warning(f"Error al cargar encuestas del curso {curso_id}: {e}")
        return []


def create_course_survey_safe(
    curso_id: int,
    survey_data: Dict[str, Any],
    tenant_id: str
) -> Optional[Dict[str, Any]]:
    """
    Crea una encuesta para un curso de forma segura.
    
    Args:
        curso_id: ID del curso
        survey_data: Datos de la encuesta
        tenant_id: ID del tenant
        
    Returns:
        Encuesta creada o None si hay error
    """
    try:
        from fastapi_modulo.modulos.encuestas.modelos.encuestas_store import (
            create_course_survey
        )
        
        survey = create_course_survey(curso_id, survey_data, tenant_id)
        
        return survey
        
    except ImportError:
        return None
    except Exception as e:
        import logging
        logging.error(f"Error al crear encuesta para curso {curso_id}: {e}")
        return None


# ============================================================================
# UTILIDADES DE REQUEST
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Obtiene la IP del cliente desde la request.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Dirección IP del cliente
        
    Examples:
        >>> get_client_ip(request)
        '192.168.1.1'
    """
    # Verificar headers de proxy
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Tomar la primera IP de la lista
        return forwarded_for.split(",")[0].strip()
    
    # Verificar real IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Usar IP directa del cliente
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """
    Obtiene el User-Agent del cliente.
    
    Args:
        request: Request de FastAPI
        
    Returns:
        String del User-Agent
        
    Examples:
        >>> get_user_agent(request)
        'Mozilla/5.0...'
    """
    return request.headers.get("user-agent", "")


def extract_actor_info(request: Request) -> Dict[str, str]:
    """
    Extrae información del actor (usuario que realiza la acción).
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Diccionario con actor_key y actor_name
        
    Examples:
        >>> extract_actor_info(request)
        {'actor_key': '123', 'actor_name': 'Juan Pérez'}
    """
    try:
        actor_key = current_user_key(request)
        actor_name = current_user_name(request)
        
        return {
            "actor_key": actor_key,
            "actor_name": actor_name
        }
        
    except HTTPException:
        return {
            "actor_key": "system",
            "actor_name": "Sistema"
        }
    
