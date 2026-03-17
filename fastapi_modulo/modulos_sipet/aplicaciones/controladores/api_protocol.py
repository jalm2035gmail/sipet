from fastapi import APIRouter, Body, Request

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_AUDIT_VIEW,
    APPLICATIONS_PERMISSION_PROTOCOL_SYNC,
    require_applications_permission,
    request_actor_context,
)
from fastapi_modulo.modulos_sipet.aplicaciones.modelos.schemas import (
    ProtocolAuditItem,
    ProtocolSyncResponse,
    ProtocolSyncSchema,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.audit_service import get_protocol_audit_map, sync_protocol_files
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.security_service import (
    SENSITIVE_ACTION_PROTOCOL_SYNC,
    verify_sensitive_action_token,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.task_queue_service import queue_task

router = APIRouter()


@router.get("/api/aplicaciones/protocolo", response_model=dict[str, ProtocolAuditItem])
def aplicaciones_protocol_status(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_AUDIT_VIEW)
    return get_protocol_audit_map()


@router.post("/api/aplicaciones/protocolo/sync", response_model=ProtocolSyncResponse)
def aplicaciones_sync_protocol(
    request: Request,
    body: ProtocolSyncSchema = Body(default_factory=ProtocolSyncSchema),
):
    require_applications_permission(request, APPLICATIONS_PERMISSION_PROTOCOL_SYNC)
    actor = request_actor_context(request)
    verify_sensitive_action_token(
        token=body.challenge_token,
        username=actor["user_id"],
        action=SENSITIVE_ACTION_PROTOCOL_SYNC,
        module_key="",
    )
    queued = queue_task(
        "protocol_sync",
        {
            "mode": body.mode,
            "overwrite_manifest": body.overwrite_manifest,
            "overwrite_init": body.overwrite_init,
            "user_id": actor["user_id"],
            "ip": actor["ip"],
        },
    )
    if queued["status"] == "inline":
        result = sync_protocol_files(
            mode=body.mode,
            overwrite_manifest=body.overwrite_manifest,
            overwrite_init=body.overwrite_init,
            user_id=actor["user_id"],
            ip=actor["ip"],
        )
        result["status"] = "success"
        result["task_id"] = ""
        result["task_name"] = ""
        return result
    return {
        "status": "queued",
        "task_id": str(queued["task_id"]),
        "task_name": "protocol_sync",
        "created_init": [],
        "created_manifest": [],
        "updated_init": [],
        "updated_manifest": [],
        "before": {},
        "after": {},
    }


__all__ = ["router"]
