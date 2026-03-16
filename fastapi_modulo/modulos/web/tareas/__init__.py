from fastapi_modulo.modulos.web.tareas.audit_tasks import celery_app as audit_celery_app
from fastapi_modulo.modulos.web.tareas.cleanup_tasks import celery_app as cleanup_celery_app
from fastapi_modulo.modulos.web.tareas.security_tasks import celery_app as security_celery_app
from fastapi_modulo.modulos.web.tareas.audit_tasks import (
    build_backend_analytics_report_task,
    build_security_compliance_snapshot_task,
    export_backend_access_history_excel_task,
    export_security_audit_report_pdf_task,
)
from fastapi_modulo.modulos.web.tareas.security_tasks import (
    build_access_risk_report_task,
    train_backend_access_risk_model_task,
)

__all__ = [
    "audit_celery_app",
    "build_access_risk_report_task",
    "build_backend_analytics_report_task",
    "build_security_compliance_snapshot_task",
    "cleanup_celery_app",
    "export_backend_access_history_excel_task",
    "export_security_audit_report_pdf_task",
    "security_celery_app",
    "train_backend_access_risk_model_task",
]
