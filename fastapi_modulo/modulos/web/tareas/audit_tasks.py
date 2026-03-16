from __future__ import annotations

from fastapi_modulo.modulos.web.repositorios.security_maintenance_repository import (
    build_access_report,
    build_backend_analytics_report,
    build_security_compliance_snapshot,
    build_security_alerts,
    export_backend_access_history_excel,
    export_security_audit_report_pdf,
)
from fastapi_modulo.modulos.web.tareas.celery_app import celery_app


@celery_app.task(name="web.build_access_report")
def build_access_report_task() -> dict:
    return {"status": "ok", "report": build_access_report()}


@celery_app.task(name="web.build_security_alerts")
def build_security_alerts_task() -> dict:
    return {"status": "ok", "alerts": build_security_alerts()}


@celery_app.task(name="web.build_backend_analytics_report")
def build_backend_analytics_report_task(hours: int = 24) -> dict:
    return {"status": "ok", "analytics": build_backend_analytics_report(hours)}


@celery_app.task(name="web.export_backend_access_history_excel")
def export_backend_access_history_excel_task(hours: int = 24, output_path: str = "") -> dict:
    return {"status": "ok", "file_path": export_backend_access_history_excel(hours, output_path)}


@celery_app.task(name="web.build_security_compliance_snapshot")
def build_security_compliance_snapshot_task(hours: int = 24) -> dict:
    return {"status": "ok", "report": build_security_compliance_snapshot(hours)}


@celery_app.task(name="web.export_security_audit_report_pdf")
def export_security_audit_report_pdf_task(hours: int = 24, output_path: str = "") -> dict:
    return {"status": "ok", "file_path": export_security_audit_report_pdf(hours, output_path)}
