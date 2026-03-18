from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import Request

from fastapi_modulo.modulos_sipet.web.repositorios.security_repository import log_security_event
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import request_ip, request_tenant_id, request_user_agent


def record_security_event(
    request: Request,
    event_type: str,
    *,
    user_id: Optional[int] = None,
    username: str = "",
    success: bool = True,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Registra un evento de seguridad en la base de datos.

    El análisis de riesgo ML se ejecuta de forma asíncrona vía Celery
    para no bloquear el login. El resultado queda disponible en el reporte
    periódico generado por build_access_risk_report_task (cada 30 min via beat).
    """
    event_metadata = metadata.copy() if isinstance(metadata, dict) else {}

    if event_type in {"login_success", "login_failed"}:
        _enqueue_risk_analysis()

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


def _enqueue_risk_analysis() -> None:
    """
    Encola el análisis de riesgo ML como tarea Celery.
    Analiza la última hora de actividad (limit=50 registros recientes).
    Falla silenciosamente si Celery/Redis no están disponibles para
    no interrumpir el flujo de autenticación.
    """
    try:
        from fastapi_modulo.modulos_sipet.web.tareas.security_tasks import build_access_risk_report_task
        build_access_risk_report_task.delay(hours=1, limit=50)
    except Exception:
        pass


def datetime_now_iso() -> str:
    return datetime.utcnow().isoformat()
