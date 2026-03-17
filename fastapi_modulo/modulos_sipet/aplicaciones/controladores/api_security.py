from fastapi import APIRouter, Request

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_PACKAGES_UPLOAD,
    APPLICATIONS_PERMISSION_PROTOCOL_SYNC,
    require_applications_permission,
    request_actor_context,
)
from fastapi_modulo.modulos_sipet.aplicaciones.modelos.schemas import (
    SensitiveActionChallengeResponse,
    SensitiveActionChallengeSchema,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.security_service import (
    SENSITIVE_ACTION_PACKAGE_ROLLBACK,
    SENSITIVE_ACTION_PACKAGE_UPLOAD,
    SENSITIVE_ACTION_PROTOCOL_SYNC,
    issue_sensitive_action_token,
)

router = APIRouter()


@router.post("/api/aplicaciones/security/challenge", response_model=SensitiveActionChallengeResponse)
def aplicaciones_security_challenge(body: SensitiveActionChallengeSchema, request: Request):
    actor = request_actor_context(request)
    if body.action == SENSITIVE_ACTION_PROTOCOL_SYNC:
        require_applications_permission(request, APPLICATIONS_PERMISSION_PROTOCOL_SYNC)
    elif body.action in {SENSITIVE_ACTION_PACKAGE_UPLOAD, SENSITIVE_ACTION_PACKAGE_ROLLBACK}:
        require_applications_permission(request, APPLICATIONS_PERMISSION_PACKAGES_UPLOAD)
    return issue_sensitive_action_token(
        username=actor["user_id"],
        password=body.password,
        action=body.action,
        module_key=body.module_key,
    )


__all__ = ["router"]
