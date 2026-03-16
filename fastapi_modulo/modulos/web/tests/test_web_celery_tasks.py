from __future__ import annotations

from fastapi_modulo.modulos.web.tareas import audit_tasks, cleanup_tasks, security_tasks


def test_cleanup_tasks(monkeypatch) -> None:
    monkeypatch.setattr(cleanup_tasks, "cleanup_expired_sessions", lambda: 2)
    monkeypatch.setattr(cleanup_tasks, "cleanup_expired_mfa_challenges", lambda: 3)
    assert cleanup_tasks.cleanup_expired_sessions_task() == {"status": "ok", "deleted_sessions": 2}
    assert cleanup_tasks.cleanup_expired_mfa_challenges_task() == {"status": "ok", "deleted_challenges": 3}


def test_security_and_audit_tasks(monkeypatch) -> None:
    monkeypatch.setattr(security_tasks, "detect_suspicious_login_patterns", lambda: [{"ip": "1.1.1.1", "attempts": 6}])
    monkeypatch.setattr(security_tasks, "summarize_active_sessions", lambda: {"active_sessions": 4, "active_users": 2})
    monkeypatch.setattr(security_tasks, "train_backend_access_risk_model", lambda hours=24 * 30: {"status": "trained", "samples": 8})
    monkeypatch.setattr(security_tasks, "build_access_risk_report", lambda hours=24, limit=100: {"high_risk_count": 2, "evaluated_events": 7})
    monkeypatch.setattr(audit_tasks, "build_access_report", lambda: {"successful_logins": 5, "failed_logins": 1})
    monkeypatch.setattr(audit_tasks, "build_security_alerts", lambda: [{"type": "suspicious_login_pattern"}])
    monkeypatch.setattr(audit_tasks, "build_backend_analytics_report", lambda hours=24: {"window_hours": hours, "module_usage": {"total_views": 9}})
    monkeypatch.setattr(audit_tasks, "build_security_compliance_snapshot", lambda hours=24: {"window_hours": hours, "compliance_score": 91})
    monkeypatch.setattr(audit_tasks, "export_backend_access_history_excel", lambda hours=24, output_path="": "/tmp/report.xlsx")
    monkeypatch.setattr(audit_tasks, "export_security_audit_report_pdf", lambda hours=24, output_path="": "/tmp/security-audit.pdf")
    assert security_tasks.detect_suspicious_login_patterns_task()["status"] == "ok"
    assert security_tasks.summarize_active_sessions_task()["summary"]["active_sessions"] == 4
    assert security_tasks.train_backend_access_risk_model_task()["training"]["samples"] == 8
    assert security_tasks.build_access_risk_report_task()["report"]["high_risk_count"] == 2
    assert audit_tasks.build_access_report_task()["report"]["successful_logins"] == 5
    assert audit_tasks.build_security_alerts_task()["alerts"][0]["type"] == "suspicious_login_pattern"
    assert audit_tasks.build_backend_analytics_report_task(48)["analytics"]["window_hours"] == 48
    assert audit_tasks.build_security_compliance_snapshot_task()["report"]["compliance_score"] == 91
    assert audit_tasks.export_backend_access_history_excel_task()["file_path"] == "/tmp/report.xlsx"
    assert audit_tasks.export_security_audit_report_pdf_task()["file_path"] == "/tmp/security-audit.pdf"
