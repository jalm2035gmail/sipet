from __future__ import annotations

from typing import Any, Optional

from fastapi import Request

from fastapi_modulo.modulos.web.repositorios.security_repository import log_security_event
from fastapi_modulo.modulos.web.servicios.access_risk_ml_service import predict_access_risk
from fastapi_modulo.modulos.web.servicios.auth_service import request_ip, request_tenant_id, request_user_agent


def record_security_event(
    request: Request,
    event_type: str,
    *,
    user_id: Optional[int] = None,
    username: str = "",
    success: bool = True,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    event_metadata = metadata.copy() if isinstance(metadata, dict) else {}
    if event_type in {"login_success", "login_failed"}:
        risk_payload = predict_access_risk(
            {
                "created_at": datetime_now_iso(),
                "username": username,
                "ip": request_ip(request),
                "user_agent": request_user_agent(request),
                "success": success,
                "metadata": event_metadata,
            }
        )
        event_metadata["access_risk_label"] = risk_payload["label"]
        event_metadata["access_risk_score"] = risk_payload["risk_score"]
        event_metadata["access_risk_model_status"] = risk_payload["model_status"]
    log_security_event(
        tenant_id=request_tenant_id(request),
        event_type=event_type,
        user_id=user_id,
        username=username,
        ip=request_ip(request),
        user_agent=request_user_agent(request),
        success=success,
        metadata=event_metadata,
    )


def datetime_now_iso() -> str:
    from datetime import datetime

    return datetime.utcnow().isoformat()
