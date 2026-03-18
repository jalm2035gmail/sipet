from __future__ import annotations

import logging

from celery.exceptions import MaxRetriesExceededError

from fastapi_modulo.modulos_sipet.web.repositorios.security_maintenance_repository import (
    build_access_report,
    build_backend_analytics_report,
    build_security_alerts,
    build_security_compliance_snapshot,
    export_backend_access_history_excel,
    export_security_audit_report_pdf,
)
from fastapi_modulo.modulos_sipet.web.tareas.celery_app import celery_app

logger = logging.getLogger(__name__)

# ── Configuración de reintentos compartida ────────────────────────────────────
_RETRY_KWARGS = {
    "autoretry_for": (Exception,),
    "max_retries": 3,
    "default_retry_delay": 30,   # segundos entre reintentos
    "retry_backoff": True,        # espera exponencial: 30s, 60s, 120s
    "retry_backoff_max": 300,     # máximo 5 minutos entre reintentos
    "retry_jitter": True,         # añade variación aleatoria para evitar thundering herd
}


@celery_app.task(name="web.build_access_report", **_RETRY_KWARGS)
def build_access_report_task() -> dict:
    try:
        return {"status": "ok", "report": build_access_report()}
    except MaxRetriesExceededError:
        logger.error("build_access_report_task: máximo de reintentos alcanzado")
        return {"status": "error", "report": None}


@celery_app.task(name="web.build_security_alerts", **_RETRY_KWARGS)
def build_security_alerts_task() -> dict:
    try:
        return {"status": "ok", "alerts": build_security_alerts()}
    except MaxRetriesExceededError:
        logger.error("build_security_alerts_task: máximo de reintentos alcanzado")
        return {"status": "error", "alerts": []}


@celery_app.task(name="web.build_backend_analytics_report", **_RETRY_KWARGS)
def build_backend_analytics_report_task(hours: int = 24) -> dict:
    try:
        return {"status": "ok", "analytics": build_backend_analytics_report(hours)}
    except MaxRetriesExceededError:
        logger.error("build_backend_analytics_report_task: máximo de reintentos alcanzado, hours=%s", hours)
        return {"status": "error", "analytics": None}


@celery_app.task(name="web.export_backend_access_history_excel", **_RETRY_KWARGS)
def export_backend_access_history_excel_task(hours: int = 24, output_path: str = "") -> dict:
    """
    Exporta el historial de acceso a Excel.
    Si output_path está vacío, el repositorio genera la ruta en /tmp.
    El archivo resultante debe ser consumido o eliminado por el caller.
    """
    try:
        file_path = export_backend_access_history_excel(hours, output_path)
        if not file_path:
            logger.warning("export_backend_access_history_excel_task: exportación devolvió ruta vacía")
            return {"status": "empty", "file_path": ""}
        return {"status": "ok", "file_path": file_path}
    except MaxRetriesExceededError:
        logger.error("export_backend_access_history_excel_task: máximo de reintentos alcanzado")
        return {"status": "error", "file_path": ""}


@celery_app.task(name="web.build_security_compliance_snapshot", **_RETRY_KWARGS)
def build_security_compliance_snapshot_task(hours: int = 24) -> dict:
    try:
        return {"status": "ok", "report": build_security_compliance_snapshot(hours)}
    except MaxRetriesExceededError:
        logger.error("build_security_compliance_snapshot_task: máximo de reintentos alcanzado, hours=%s", hours)
        return {"status": "error", "report": None}


@celery_app.task(name="web.export_security_audit_report_pdf", **_RETRY_KWARGS)
def export_security_audit_report_pdf_task(hours: int = 24, output_path: str = "") -> dict:
    """
    Exporta el reporte de auditoría a PDF.
    Si output_path está vacío, el repositorio genera la ruta en /tmp.
    El archivo resultante debe ser consumido o eliminado por el caller.
    """
    try:
        file_path = export_security_audit_report_pdf(hours, output_path)
        if not file_path:
            logger.warning("export_security_audit_report_pdf_task: exportación devolvió ruta vacía")
            return {"status": "empty", "file_path": ""}
        return {"status": "ok", "file_path": file_path}
    except MaxRetriesExceededError:
        logger.error("export_security_audit_report_pdf_task: máximo de reintentos alcanzado")
        return {"status": "error", "file_path": ""}
    