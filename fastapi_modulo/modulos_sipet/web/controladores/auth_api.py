from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos_sipet.web.schemas import LoginFormSchema
from fastapi_modulo.modulos_sipet.web.repositorios.security_repository import list_active_sessions, revoke_session
from fastapi_modulo.modulos_sipet.web.servicios import auth_service, mfa_service, passkey_service
from fastapi_modulo.modulos_sipet.web.servicios.access_service import is_admin_or_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.audit_service import record_security_event
from fastapi_modulo.modulos_sipet.web.servicios.auth_response_service import auth_page_error
from fastapi_modulo.modulos_sipet.web.servicios.security_policy_service import is_mfa_required
from fastapi_modulo.modulos_sipet.web.servicios.session_service import AUTH_COOKIE_NAME, clear_auth_cookies, read_session_cookie
from fastapi_modulo.modulos_sipet.web.servicios.tenant_observability_service import build_tenant_diagnostics

router = APIRouter()


def _redirect_to_database_setup(request: Request) -> RedirectResponse:
    app_state = getattr(getattr(request, "app", None), "state", None)
    if app_state is not None:
        app_state.database_setup_required = True
    return RedirectResponse(url="/base_datos/inicializar", status_code=303)


@router.get("/api/backend/login/mfa-hint")
def backend_login_mfa_hint(request: Request, usuario: str = ""):
    if bool(getattr(getattr(request, "app", None), "state", None) and getattr(request.app.state, "database_setup_required", False)):
        return JSONResponse({"success": False, "error": "Base de datos no inicializada"}, status_code=503)
    username = (usuario or "").strip()
    if not username:
        return {"success": True, "show_authenticator_code": False}

    db = auth_service.get_session_local()()
    try:
        try:
            user = auth_service.find_user_by_login(db, username)
        except SQLAlchemyError:
            return _redirect_to_database_setup(request)
        show_authenticator_code = bool(
            user
            and bool(getattr(user, "totp_enabled", False))
            and str(getattr(user, "totp_secret", "") or "").strip()
        )
        return {
            "success": True,
            "show_authenticator_code": show_authenticator_code,
        }
    finally:
        db.close()


@router.post("/backend/login")
def backend_login_submit(
    request: Request,
    usuario: str = Form(""),
    contrasena: str = Form(""),
    codigo_autenticador: str = Form(""),
):
    if bool(getattr(getattr(request, "app", None), "state", None) and getattr(request.app.state, "database_setup_required", False)):
        return RedirectResponse(url="/base_datos/inicializar", status_code=303)
    import re
    from urllib.parse import quote

    form_data = LoginFormSchema(
        usuario=usuario,
        contrasena=contrasena,
        codigo_autenticador=codigo_autenticador or None,
    )
    if auth_service.is_login_rate_limited(request):
        return auth_page_error(request, "Demasiados intentos. Intenta de nuevo en unos minutos.", 429)
    username = form_data.usuario.strip()
    request.state.pending_username = username
    password = form_data.contrasena or ""
    if not username or not password:
        auth_service.register_failed_login_attempt(request)
        auth_service.record_login_attempt(request, username, False)
        return auth_page_error(request, "Datos incorrectos", 401)

    db = auth_service.get_session_local()()
    has_passkey = False
    totp_secret = ""
    global_superadmin = None
    redirect_url = "/inicio"
    try:
        try:
            user = auth_service.find_user_by_login(db, username)
            if not user or not auth_service.rehash_user_password_if_needed(db, user, password):
                global_superadmin = auth_service.authenticate_global_superadmin(username, password)
                if not global_superadmin:
                    auth_service.register_failed_login_attempt(request)
                    auth_service.record_login_attempt(request, username, False)
                    return auth_page_error(request, "Datos incorrectos", 401)
                role_name = str(global_superadmin["role_name"])
                session_username = str(global_superadmin["username"])
                has_passkey = False
                totp_secret = ""
            else:
                role_name = auth_service.resolve_user_role_name(db, user)
                session_username = auth_service.decrypt_sensitive(user.usuario) or username
                has_passkey = bool(user.backendauthn_credential_id and user.backendauthn_public_key)
                totp_secret = mfa_service.get_user_totp_secret(user, role_name)
                redirect_url = auth_service.resolve_post_login_redirect(db, role_name, int(user.id))
        except SQLAlchemyError:
            return _redirect_to_database_setup(request)
    finally:
        db.close()

    auth_service.clear_failed_login_attempts(request)
    if global_superadmin:
        password_fingerprint = str(global_superadmin["password_fingerprint"])
        resolved_user_id = int(global_superadmin["user_id"])
    else:
        password_fingerprint = auth_service.password_fingerprint_for_user(user)
        resolved_user_id = int(user.id)
    if is_mfa_required(
        role_name=role_name,
        tenant_id=auth_service.request_tenant_id(request),
        user_id=resolved_user_id,
        username=session_username,
    ):
        code_value = re.sub(r"\s+", "", form_data.codigo_autenticador or "")
        if code_value:
            if not totp_secret:
                auth_service.register_failed_login_attempt(request)
                auth_service.record_login_attempt(request, username, False)
                return auth_page_error(request, "El código autenticador no está configurado para este usuario.", 403)
            if not mfa_service.verify_totp_code(totp_secret, code_value):
                auth_service.register_failed_login_attempt(request)
                auth_service.record_login_attempt(request, username, False)
                return auth_page_error(request, "Código de autenticador inválido.", 401)
            response = RedirectResponse(url=redirect_url if not global_superadmin else "/inicio", status_code=303)
            mfa_service.finish_mfa_login(
                request,
                response,
                session_username,
                role_name,
                resolved_user_id,
                password_fingerprint=password_fingerprint,
            )
            auth_service.record_login_attempt(request, username, True)
            return response
        if not has_passkey and not totp_secret:
            return auth_page_error(
                request,
                "El rol Autoridades requiere segundo factor (biometría o autenticador) configurado.",
                403,
            )
        if has_passkey:
            response = RedirectResponse(url=f"/backend/login?mfa=required&usuario={quote(username)}", status_code=303)
            passkey_service.set_passkey_cookie(
                response,
                passkey_service.PASSKEY_COOKIE_MFA_GATE,
                passkey_service.issue_mfa_gate_token(request, resolved_user_id),
            )
            return response
        return auth_page_error(request, "Ingresa tu código de autenticador para completar el acceso.", 401)

    response = RedirectResponse(url=redirect_url if not global_superadmin else "/inicio", status_code=303)
    try:
        auth_service.apply_login_session(
            response,
            request,
            session_username,
            role_name,
            resolved_user_id,
            password_fingerprint=password_fingerprint,
        )
        auth_service.record_login_attempt(request, username, True)
    except SQLAlchemyError:
        return _redirect_to_database_setup(request)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_MFA_GATE)
    return response


@router.get("/logout")
def backend_logout(request: Request):
    session_data = read_session_cookie(request.cookies.get(AUTH_COOKIE_NAME, ""))
    revoke_session(str((session_data or {}).get("session_jti") or ""))
    response = RedirectResponse(url="/backend/login", status_code=303)
    clear_auth_cookies(response)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_AUTH)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_REGISTER)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_MFA_GATE)
    record_security_event(
        request,
        "logout",
        username=str((session_data or {}).get("username") or ""),
        success=True,
        metadata={"session_jti": str((session_data or {}).get("session_jti") or "")},
    )
    return response


@router.get("/api/backend/sessions")
def backend_active_sessions(request: Request):
    username = str(getattr(request.state, "user_name", "") or "").strip()
    if not username:
        return RedirectResponse(url="/backend/login", status_code=303)
    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_login(db, username)
        if not user:
            return RedirectResponse(url="/backend/login", status_code=303)
        return {
            "success": True,
            "sessions": list_active_sessions(
                user_id=int(user.id),
                tenant_id=auth_service.request_tenant_id(request),
            ),
        }
    finally:
        db.close()


@router.get("/api/backend/tenant-diagnostics")
def backend_tenant_diagnostics(request: Request):
    username = str(getattr(request.state, "user_name", "") or "").strip()
    role = str(getattr(request.state, "user_role", "") or "").strip().lower()
    if not username:
        return RedirectResponse(url="/backend/login", status_code=303)
    if not is_admin_or_superadmin(request):
        return JSONResponse({"success": False, "error": "Acceso restringido a administradores"}, status_code=403)
    payload = build_tenant_diagnostics(request)
    payload["viewer"] = {
        "username": username,
        "role": role,
    }
    return {
        "success": True,
        "diagnostics": payload,
    }
