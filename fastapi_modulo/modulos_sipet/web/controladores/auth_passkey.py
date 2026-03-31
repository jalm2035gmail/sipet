from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.web.schemas import (
    PasskeyAuthOptionsSchema,
    PasskeyAuthVerifySchema,
    PasskeyRevokeSchema,
    PasskeyRegisterOptionsSchema,
    PasskeyRegisterVerifySchema,
    schema_to_dict,
)
from fastapi_modulo.modulos_sipet.web.servicios import auth_service, passkey_service
from fastapi_modulo.modulos_sipet.web.servicios.audit_service import record_security_event

router = APIRouter()


@router.post("/backend/passkey/register/options")
def passkey_register_options(
    request: Request,
    payload: PasskeyRegisterOptionsSchema,
):
    username = payload.usuario.strip()
    password = payload.contrasena
    if not username or not password:
        return JSONResponse({"success": False, "error": "Usuario y contraseña son obligatorios"}, status_code=400)
    if auth_service.is_demo_account(username):
        return JSONResponse({"success": False, "error": "La biometría no está habilitada para el usuario demo"}, status_code=403)

    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_login(db, username)
        if not user or not auth_service.rehash_user_password_if_needed(db, user, password):
            return JSONResponse({"success": False, "error": "Credenciales inválidas"}, status_code=401)
        options, token = passkey_service.build_passkey_registration(request, user, username)
    finally:
        db.close()

    response = JSONResponse({"success": True, "options": options})
    passkey_service.set_passkey_cookie(response, passkey_service.PASSKEY_COOKIE_REGISTER, token)
    return response


@router.post("/backend/passkey/register/verify")
def passkey_register_verify(
    request: Request,
    payload: PasskeyRegisterVerifySchema,
):
    token_data = passkey_service.read_passkey_token(
        request.cookies.get(passkey_service.PASSKEY_COOKIE_REGISTER, ""),
        "register",
    )
    if not token_data:
        return JSONResponse({"success": False, "error": "Solicitud biométrica expirada, inténtalo de nuevo"}, status_code=400)

    credential_id = payload.id.strip()
    response_payload = schema_to_dict(payload.response)
    if not credential_id:
        return JSONResponse({"success": False, "error": "Respuesta biométrica inválida"}, status_code=400)

    client_data = passkey_service.parse_client_data(str(response_payload.get("clientDataJSON", "")))
    public_key_b64 = str(response_payload.get("publicKey", "")).strip()
    if not client_data or not public_key_b64:
        return JSONResponse({"success": False, "error": "No se pudo registrar la clave biométrica"}, status_code=400)
    if client_data.get("type") != "webauthn.create":
        return JSONResponse({"success": False, "error": "Operación biométrica inválida"}, status_code=400)
    if client_data.get("challenge") != token_data["challenge"]:
        return JSONResponse({"success": False, "error": "Challenge inválido"}, status_code=400)
    expected_origin = token_data.get("origin") or passkey_service.passkey_origin(request)
    if client_data.get("origin") != expected_origin:
        return JSONResponse({"success": False, "error": "Origen inválido"}, status_code=400)

    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_id(db, token_data["user_id"])
        if not user:
            return JSONResponse({"success": False, "error": "Usuario no encontrado"}, status_code=404)
        user.backendauthn_credential_id = credential_id
        user.backendauthn_public_key = public_key_b64
        user.backendauthn_sign_count = int(response_payload.get("signCount") or 0)
        db.add(user)
        db.commit()
    finally:
        db.close()

    passkey_service.consume_passkey_challenge(
        token_data["user_id"],
        "register",
        token_data["jti"],
        token_data["challenge"],
    )
    response = JSONResponse({"success": True})
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_REGISTER)
    record_security_event(
        request,
        "passkey_registered",
        user_id=token_data["user_id"],
        username=auth_service.decrypt_sensitive(user.usuario) or "",
        metadata={"credential_id": credential_id},
    )
    return response


@router.post("/backend/passkey/auth/options")
def passkey_auth_options(
    request: Request,
    payload: PasskeyAuthOptionsSchema,
):
    if auth_service.is_sensitive_endpoint_rate_limited(request, "backend:passkey:auth:options"):
        return JSONResponse({"success": False, "error": "Demasiadas solicitudes biométricas"}, status_code=429)
    auth_service.register_sensitive_endpoint_hit(request, "backend:passkey:auth:options")
    username = payload.usuario.strip()
    if not username:
        return JSONResponse({"success": False, "error": "Usuario requerido"}, status_code=400)

    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_login(db, username)
        if not user or not user.backendauthn_credential_id:
            return JSONResponse({"success": False, "error": "Biometría no configurada"}, status_code=404)
        options, token = passkey_service.build_passkey_authentication(request, user)
    finally:
        db.close()

    response = JSONResponse({"success": True, "options": options})
    passkey_service.set_passkey_cookie(response, passkey_service.PASSKEY_COOKIE_AUTH, token)
    return response


@router.post("/backend/passkey/auth/verify")
def passkey_auth_verify(
    request: Request,
    payload: PasskeyAuthVerifySchema,
):
    if auth_service.is_sensitive_endpoint_rate_limited(request, "backend:passkey:auth:verify"):
        return JSONResponse({"success": False, "error": "Demasiadas verificaciones biométricas"}, status_code=429)
    auth_service.register_sensitive_endpoint_hit(request, "backend:passkey:auth:verify")
    token_data = passkey_service.read_passkey_token(
        request.cookies.get(passkey_service.PASSKEY_COOKIE_AUTH, ""),
        "auth",
    )
    if not token_data:
        return JSONResponse({"success": False, "error": "Solicitud biométrica expirada, inténtalo de nuevo"}, status_code=400)

    credential_id = payload.id.strip()
    response_payload = schema_to_dict(payload.response)
    if not credential_id:
        return JSONResponse({"success": False, "error": "Respuesta biométrica inválida"}, status_code=400)

    client_data = passkey_service.parse_client_data(str(response_payload.get("clientDataJSON", "")))
    if not client_data:
        return JSONResponse({"success": False, "error": "No se pudo validar la respuesta biométrica"}, status_code=400)
    if client_data.get("type") != "webauthn.get":
        return JSONResponse({"success": False, "error": "Operación biométrica inválida"}, status_code=400)
    if client_data.get("challenge") != token_data["challenge"]:
        return JSONResponse({"success": False, "error": "Challenge inválido"}, status_code=400)
    expected_origin = token_data.get("origin") or passkey_service.passkey_origin(request)
    if client_data.get("origin") != expected_origin:
        return JSONResponse({"success": False, "error": "Origen inválido"}, status_code=400)

    db = auth_service.get_session_local()()
    redirect_url = "/inicio"
    try:
        user = auth_service.find_user_by_id(db, token_data["user_id"])
        if not user or user.backendauthn_credential_id != credential_id:
            return JSONResponse({"success": False, "error": "Credencial biométrica no encontrada"}, status_code=404)
        user.backendauthn_sign_count = int(response_payload.get("signCount") or user.backendauthn_sign_count or 0)
        db.add(user)
        db.commit()
        role_name = auth_service.resolve_user_role_name(db, user)
        session_username = auth_service.decrypt_sensitive(user.usuario) or ""
        redirect_url = auth_service.resolve_post_login_redirect(db, role_name, int(user.id))
    finally:
        db.close()

    passkey_service.consume_passkey_challenge(
        token_data["user_id"],
        "auth",
        token_data["jti"],
        token_data["challenge"],
    )
    mfa_gate_token = request.cookies.get(passkey_service.PASSKEY_COOKIE_MFA_GATE, "")
    if mfa_gate_token:
        mfa_gate_data = passkey_service.read_passkey_token(mfa_gate_token, "mfa_gate")
        if mfa_gate_data:
            passkey_service.consume_passkey_challenge(
                token_data["user_id"],
                "mfa_gate",
                mfa_gate_data["jti"],
                mfa_gate_data["challenge"],
            )
    response = JSONResponse(
        {
            "success": True,
            "redirect_url": redirect_url,
        }
    )
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_AUTH)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_MFA_GATE)
    auth_service.apply_login_session(
        response,
        request,
        session_username,
        role_name,
        user.id,
        password_fingerprint=auth_service.password_fingerprint_for_user(user),
    )
    record_security_event(
        request,
        "passkey_auth_success",
        user_id=user.id,
        username=session_username,
        metadata={"credential_id": credential_id},
    )
    return response


@router.get("/backend/passkey/devices")
def passkey_devices(request: Request):
    username = str(getattr(request.state, "user_name", "") or "").strip()
    if not username:
        return JSONResponse({"success": False, "error": "No autenticado"}, status_code=401)
    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_login(db, username)
        if not user:
            return JSONResponse({"success": False, "error": "Usuario no encontrado"}, status_code=404)
        return JSONResponse({"success": True, "devices": passkey_service.list_registered_passkeys(user)})
    finally:
        db.close()


@router.post("/backend/passkey/revoke")
def passkey_revoke(request: Request, payload: PasskeyRevokeSchema):
    username = str(getattr(request.state, "user_name", "") or "").strip()
    credential_id = payload.credential_id.strip()
    if not username or not credential_id:
        return JSONResponse({"success": False, "error": "Solicitud inválida"}, status_code=400)
    db = auth_service.get_session_local()()
    try:
        user = auth_service.find_user_by_login(db, username)
        if not user:
            return JSONResponse({"success": False, "error": "Usuario no encontrado"}, status_code=404)
        if not passkey_service.revoke_registered_passkey(db, user, credential_id):
            return JSONResponse({"success": False, "error": "Dispositivo no encontrado"}, status_code=404)
    finally:
        db.close()
    record_security_event(
        request,
        "passkey_revoked",
        username=username,
        metadata={"credential_id": credential_id},
    )
    return JSONResponse({"success": True})
