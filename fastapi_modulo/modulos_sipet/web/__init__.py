# Módulo web — API pública
#
# Otros módulos que declaren depends: ["web"] en su manifest deben importar
# desde estas rutas. No importar directamente desde subpaquetes internos.

# Modelos de dominio compartidos
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores, Rol, Usuario

# Acceso y roles
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_current_role,
    is_superadmin,
    require_admin_or_superadmin,
    require_app_access,
    require_screen_access,
)

# Sesión y cookies
from fastapi_modulo.modulos_sipet.web.servicios.session_service import (
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_SECRET,
    apply_auth_cookies,
)

# Utilidades para módulos (shell, assets, respuestas JSON)
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import (
    build_module_backend_context,
    json_error,
    json_ok,
    read_text_file,
    render_backend_page_html,
    render_no_access_page,
    scoped_text_asset_response,
    text_asset_response,
    versioned_asset_url,
)

# Shell del backend
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import (
    backend_screen,
    render_backend_page,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_middleware import enforce_backend_login

__all__ = [
    # Modelos
    "Colores",
    "Rol",
    "Usuario",
    # Acceso
    "get_current_role",
    "is_superadmin",
    "require_admin_or_superadmin",
    "require_app_access",
    "require_screen_access",
    # Sesión
    "AUTH_COOKIE_NAME",
    "AUTH_COOKIE_SECRET",
    "apply_auth_cookies",
    # Module tools
    "build_module_backend_context",
    "json_error",
    "json_ok",
    "read_text_file",
    "render_backend_page_html",
    "render_no_access_page",
    "scoped_text_asset_response",
    "text_asset_response",
    "versioned_asset_url",
    # Backend shell
    "backend_screen",
    "enforce_backend_login",
    "render_backend_page",
]
