"""
servicios/frontend_context_service.py
─────────────────────────────────────────────────────────────────────────────
Capa de contexto del módulo frontend.

Centraliza la resolución de todos los datos de sesión/usuario/UI que los
controladores necesitan, eliminando la dependencia directa de cada controlador
a 5-6 servicios externos distintos.

Expone:
  get_frontend_context(request)  →  dict con usuario, permisos, branding y UI.
  get_branding(request)          →  subconjunto solo de branding (brand store).

Uso típico en un controlador:
    from fastapi_modulo.modulos_sipet.frontend.servicios.frontend_context_service import (
        get_frontend_context,
    )

    @router.get("/api/backend/me")
    def api_backend_me(request: Request):
        return get_frontend_context(request)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Request

logger = logging.getLogger(__name__)

_FRONTEND_APP_NAME = "Frontend"
_DEFAULT_BAR_COLOR = "#0f172a"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — HELPERS INTERNOS
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_session(request: Request) -> Dict[str, Any]:
    """
    Lee la cookie de sesión y devuelve los datos de sesión.
    Devuelve dict vacío si no hay sesión válida.
    """
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.session_service import (
            AUTH_COOKIE_NAME,
            read_session_cookie,
        )
        token = request.cookies.get(AUTH_COOKIE_NAME, "")
        return read_session_cookie(token) if token else {}
    except Exception as exc:
        logger.debug("frontend_context: no se pudo leer sesión: %s", exc)
        return {}


def _resolve_user_db(username: str, role: str, request: Request) -> Dict[str, Any]:
    """
    Consulta la BD de usuarios para obtener image_url y panel_url.
    Devuelve valores por defecto si falla o no hay usuario.
    """
    defaults: Dict[str, Any] = {"image_url": "", "panel_url": "/inicio"}
    try:
        from fastapi_modulo.modulos_sipet.web.servicios import auth_service
        db = auth_service.get_session_local()()
        try:
            user = auth_service.find_user_by_login(db, username)
            if user is not None:
                defaults["panel_url"] = auth_service.resolve_post_login_redirect(
                    db, role, int(user.id)
                )
                defaults["image_url"] = str(getattr(user, "imagen", "") or "").strip()
        finally:
            db.close()
    except Exception as exc:
        logger.debug("frontend_context: no se pudo resolver user DB (%s): %s", username, exc)
    return defaults


def _resolve_backend_roles(request: Request, username: str) -> list[str]:
    """Devuelve la lista de roles de backend del usuario, o [] si falla."""
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_user_backend_roles
        return get_user_backend_roles(request, username)
    except Exception as exc:
        logger.debug("frontend_context: no se pudo resolver backend_roles: %s", exc)
        return []


def _resolve_bar_color() -> str:
    """Devuelve el color de la barra lateral desde identidad de colores."""
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context
        colors = get_colores_context()
        color = str(colors.get("sidebar-bottom") or "").strip()
        return color if color else _DEFAULT_BAR_COLOR
    except Exception:
        return _DEFAULT_BAR_COLOR


def _resolve_app_level(request: Request) -> str:
    """Devuelve el nivel de acceso del usuario a la app Frontend."""
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_user_app_access_level
        return get_user_app_access_level(request, _FRONTEND_APP_NAME)
    except Exception:
        return "no_access"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def get_frontend_context(request: Request) -> Dict[str, Any]:
    """
    Resuelve todo el contexto de usuario/UI necesario para el módulo frontend.

    Ejecuta en orden:
      1. Leer cookie de sesión → session_data
      2. Si no hay sesión → devuelve contexto anónimo
      3. Normalizar role/username
      4. Si superadmin → valores hardcoded (no consulta BD)
      5. Si usuario normal → consulta BD (panel_url, image_url) + backend_roles
      6. Resolver bar_color desde identidad de colores
      7. Calcular can_use_bar

    Returns:
        {
          "authenticated":  bool,
          "can_use_bar":    bool,
          "is_superadmin":  bool,
          "backend_roles":  list[str],
          "role":           str,
          "username":       str,
          "image_url":      str,
          "panel_url":      str,
          "builder_url":    str,
          "bar_color":      str,
        }
    """
    session_data = _resolve_session(request)

    if not session_data:
        return {
            "authenticated": False,
            "can_use_bar":   False,
            "is_superadmin": False,
            "backend_roles": [],
            "role":          "",
            "username":      "",
            "image_url":     "",
            "panel_url":     "/backend/login",
            "builder_url":   "/frontend/builder",
            "bar_color":     _DEFAULT_BAR_COLOR,
        }

    try:
        from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name
        role = normalize_role_name(session_data.get("role") or "")
    except Exception:
        role = (session_data.get("role") or "").strip()

    username   = (session_data.get("username") or "").strip()
    superadmin = role == "superadministrador"

    if superadmin:
        image_url     = ""
        panel_url     = "/inicio"
        backend_roles = ["editor", "designer"]
    else:
        request.state.user_name = username
        request.state.user_role = role
        backend_roles           = _resolve_backend_roles(request, username)
        user_db                 = _resolve_user_db(username, role, request)
        panel_url               = user_db["panel_url"]
        image_url               = user_db["image_url"]

    app_level   = "full_access" if superadmin else _resolve_app_level(request)
    can_use_bar = superadmin or app_level != "no_access" or bool(backend_roles)
    bar_color   = _resolve_bar_color()

    return {
        "authenticated":  True,
        "can_use_bar":    can_use_bar,
        "is_superadmin":  superadmin,
        "backend_roles":  backend_roles,
        "role":           role,
        "username":       username,
        "image_url":      image_url,
        "panel_url":      panel_url,
        "builder_url":    "/frontend/builder",
        "bar_color":      bar_color,
    }


def get_branding(request: Request | None = None) -> Dict[str, Any]:  # noqa: ARG001
    """
    Devuelve el dict de branding activo desde la BD.
    El parámetro request es opcional y se reserva para caché por usuario futuro.

    Returns:
        dict con las mismas claves que frontend_store.get_brand().
    """
    try:
        from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import get_brand
        return get_brand()
    except Exception as exc:
        logger.warning("frontend_context: no se pudo resolver branding: %s", exc)
        return {}
