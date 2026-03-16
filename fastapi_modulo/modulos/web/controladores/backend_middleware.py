from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from fastapi_modulo import db as core_db
from fastapi_modulo.modulos.web.servicios.access_service import get_user_screen_access_levels, has_screen_access
from fastapi_modulo.modulos.web.servicios.session_service import (
    AUTH_COOKIE_NAME,
    CSRF_PROTECTION_ENABLED,
    clear_auth_cookies,
    is_same_origin_request,
    normalize_tenant_id,
    read_session_cookie,
    validate_csrf_request,
)
from fastapi_modulo.modulos.web.servicios.template_context_service import build_not_found_context

PUBLIC_PATHS = {
    "/",
    "/backend",
    "/backend/descripcion",
    "/backend/funcionalidades",
    "/backend/404",
    "/backend/login",
    "/logout",
    "/health",
    "/healthz",
    "/favicon.ico",
    "/api/backend/me",
}


def _path_analytics_context(path: str) -> dict[str, str]:
    cleaned = str(path or "").strip("/")
    parts = [part for part in cleaned.split("/") if part]
    screen_name = "/" + cleaned if cleaned else "/"
    module_name = "backend"
    if parts:
        if parts[0] == "backend" and len(parts) > 1:
            module_name = parts[1]
        elif parts[0] not in {"api", "backend"}:
            module_name = parts[0]
    return {"module_name": module_name, "screen_name": screen_name}


def is_public_backend_path(request: Request, path: str) -> bool:
    enable_api_docs = (request.app.docs_url is not None) if getattr(request, "app", None) else False
    public_paths = set(PUBLIC_PATHS)
    if enable_api_docs:
        public_paths.update({"/docs", "/redoc", "/openapi.json"})
    return bool(
        request.method == "OPTIONS"
        or path in public_paths
        or __import__(
            "fastapi_modulo.modulos.frontend.controladores.frontend",
            fromlist=["_is_public_frontend_page_path"],
        )._is_public_frontend_page_path(path)
        or path.startswith("/api/public/")
        or path.startswith("/backend/passkey/")
        or path.startswith("/identidad-institucional")
        or path.startswith("/templates/")
        or path.startswith("/static/")
        or path.startswith("/icon/")
        or path.startswith("/imagenes/")
        or path.startswith("/docs/")
        or path.startswith("/redoc/")
    )


def _screen_access_denied(request: Request, path: str) -> bool:
    if path.startswith("/api/"):
        return False
    analytics_context = _path_analytics_context(path)
    access_levels = get_user_screen_access_levels(request)
    if not access_levels:
        return False
    if analytics_context["screen_name"] in {"/", "/inicio"}:
        return False
    return not has_screen_access(request, analytics_context["screen_name"], app_name=analytics_context["module_name"])


async def enforce_backend_login(request: Request, call_next):
    host_token = core_db.set_request_host(
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.hostname
    )
    path = request.url.path
    if is_public_backend_path(request, path):
        try:
            return await call_next(request)
        finally:
            core_db.reset_request_host(host_token)

    session_data = read_session_cookie(request.cookies.get(AUTH_COOKIE_NAME, ""))
    if not session_data:
        try:
            if path.startswith("/api/") or path.startswith("/guardar-colores"):
                return JSONResponse({"success": False, "error": "No autenticado"}, status_code=401)
            return RedirectResponse(url="/backend/login", status_code=303)
        finally:
            core_db.reset_request_host(host_token)

    try:
        request.state.user_name = session_data["username"]
        request.state.user_role = session_data["role"]
        request.state.tenant_id = normalize_tenant_id(session_data.get("tenant_id"))
        try:
            from fastapi_modulo.modulos.web.servicios import auth_service

            session_db = auth_service.get_session_local()()
            try:
                if not auth_service.is_password_fingerprint_valid(
                    session_db,
                    session_data["username"],
                    str(session_data.get("password_fingerprint") or ""),
                ):
                    response = RedirectResponse(url="/backend/login", status_code=303)
                    clear_auth_cookies(response)
                    return response
            finally:
                session_db.close()
        except Exception:
            pass

        if (
            CSRF_PROTECTION_ENABLED
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and not path.startswith("/backend/passkey/")
            and not path.startswith("/identidad-institucional")
        ):
            csrf_ok = await validate_csrf_request(request)
            if not csrf_ok and is_same_origin_request(request):
                csrf_ok = True
            if not csrf_ok:
                if path.startswith("/api/") or path.startswith("/guardar-colores"):
                    return JSONResponse({"success": False, "error": "CSRF validation failed"}, status_code=403)
                from fastapi_modulo.modulos.web.servicios.template_service import get_templates

                return get_templates(request).TemplateResponse(
                    "not_found.html",
                    build_not_found_context(request, title="Solicitud no válida"),
                    status_code=403,
                )

        if _screen_access_denied(request, path):
            if path.startswith("/api/"):
                return JSONResponse({"success": False, "error": "Sin permisos para esta pantalla"}, status_code=403)
            from fastapi_modulo.modulos.web.servicios.template_service import render_no_access_module_page

            return render_no_access_module_page(
                request,
                title="Sin acceso",
                description="No tienes permisos para esta pantalla",
                message="Sin acceso a esta pantalla, consulte con el administrador",
            )

        response = await call_next(request)
        if request.method == "GET" and not path.startswith("/api/") and response.status_code < 400:
            try:
                from fastapi_modulo.modulos.web.servicios.audit_service import record_security_event

                analytics_context = _path_analytics_context(path)
                record_security_event(
                    request,
                    "screen_view",
                    username=session_data["username"],
                    metadata={
                        "path": path,
                        "role": session_data["role"],
                        "module_name": analytics_context["module_name"],
                        "screen_name": analytics_context["screen_name"],
                    },
                )
            except Exception:
                pass
        return response
    finally:
        core_db.reset_request_host(host_token)
