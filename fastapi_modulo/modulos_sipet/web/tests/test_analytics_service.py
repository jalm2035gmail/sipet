from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos_sipet.web.servicios import analytics_service


def test_analyze_failed_login_patterns_without_data(monkeypatch) -> None:
    monkeypatch.setattr(analytics_service, "load_access_history", lambda hours=24: [])
    payload = analytics_service.analyze_failed_login_patterns(24)
    assert payload["failed_attempts"] == 0
    assert payload["peak_hours"] == []


def test_build_backend_analytics_aggregates(monkeypatch) -> None:
    monkeypatch.setattr(
        analytics_service,
        "load_access_history",
        lambda hours=24: [
            {"success": True, "created_at": "2026-03-15T10:00:00", "ip": "1.1.1.1", "username": "a"},
            {"success": False, "created_at": "2026-03-15T10:10:00", "ip": "1.1.1.1", "username": "a"},
            {"success": False, "created_at": "2026-03-15T11:00:00", "ip": "2.2.2.2", "username": "b"},
        ],
    )
    monkeypatch.setattr(
        analytics_service,
        "load_screen_usage",
        lambda hours=24: [
            {"module_name": "rrhh", "role": "administrador", "screen_name": "/rrhh/dashboard"},
            {"module_name": "rrhh", "role": "administrador", "screen_name": "/rrhh/dashboard"},
            {"module_name": "finanzas", "role": "usuario", "screen_name": "/finanzas/reportes"},
        ],
    )
    payload = analytics_service.build_backend_analytics(24)
    assert payload["successful_logins"] == 1
    assert payload["failed_logins"] == 2
    assert payload["module_usage"]["total_views"] == 3


def test_export_access_history_excel_writes_file(monkeypatch, tmp_path: Path) -> None:
    if analytics_service.Workbook is None:
        assert analytics_service.export_access_history_excel(24, str(tmp_path / "historial.xlsx")) == ""
        return
    monkeypatch.setattr(
        analytics_service,
        "load_access_history",
        lambda hours=24: [
            {
                "created_at": "2026-03-15T10:00:00",
                "tenant_id": "default",
                "username": "admin",
                "ip": "1.1.1.1",
                "user_agent": "pytest",
                "success": True,
            }
        ],
    )
    monkeypatch.setattr(
        analytics_service,
        "build_backend_analytics",
        lambda hours=24: {
            "successful_logins": 1,
            "failed_logins": 0,
            "failure_rate": 0.0,
            "failed_login_patterns": {"peak_hours": []},
            "module_usage": {"top_modules": []},
        },
    )
    file_path = analytics_service.export_access_history_excel(24, str(tmp_path / "historial.xlsx"))
    assert Path(file_path).exists()
