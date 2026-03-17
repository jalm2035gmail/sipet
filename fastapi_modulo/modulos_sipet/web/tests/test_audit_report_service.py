from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos_sipet.web.servicios import audit_report_service


def test_build_security_compliance_report(monkeypatch) -> None:
    monkeypatch.setattr(audit_report_service, "active_sessions_by_user", lambda limit=100: [{"user_id": 1, "tenant_id": "default", "active_sessions": 2}])
    monkeypatch.setattr(audit_report_service, "failed_login_attempts", lambda hours=24, limit=100: [{"username": "admin"}])
    monkeypatch.setattr(audit_report_service, "users_with_mfa_disabled", lambda limit=100: [{"username": "demo"}])
    monkeypatch.setattr(audit_report_service, "credential_change_events", lambda hours=24, limit=100: [{"event_type": "passkey_registered"}])
    payload = audit_report_service.build_security_compliance_report(24)
    assert payload["active_sessions_users"] == 1
    assert payload["users_with_mfa_disabled"] == 1


def test_export_security_audit_pdf(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        audit_report_service,
        "build_security_compliance_report",
        lambda hours=24: {
            "window_hours": hours,
            "active_sessions_users": 1,
            "failed_login_attempts": 0,
            "users_with_mfa_disabled": 0,
            "credential_change_events": 0,
            "compliance_score": 96,
        },
    )
    monkeypatch.setattr(audit_report_service, "active_sessions_by_user", lambda limit=12: [])
    monkeypatch.setattr(audit_report_service, "failed_login_attempts", lambda hours=24, limit=12: [])
    monkeypatch.setattr(audit_report_service, "credential_change_events", lambda hours=24, limit=12: [])
    monkeypatch.setattr(audit_report_service, "access_events_by_role", lambda hours=24: [])
    if not audit_report_service.reportlab_enabled():
        assert audit_report_service.export_security_audit_pdf(24, str(tmp_path / "audit.pdf")) == ""
        return
    file_path = audit_report_service.export_security_audit_pdf(24, str(tmp_path / "audit.pdf"))
    assert Path(file_path).exists()
