from pathlib import Path

from fastapi_modulo.modulos_sipet.instalacion.servicios import installer_service


def test_installation_status_requires_setup_when_conf_missing(monkeypatch) -> None:
    monkeypatch.setattr(installer_service, "SIPET_CONFIG_PATH", Path("/tmp/nonexistent-sipet.conf"))
    monkeypatch.setattr(installer_service, "get_sipet_conf_settings", lambda: {"path": "/tmp/nonexistent-sipet.conf"})

    status = installer_service.get_installation_status()

    assert status["required"] is True
    assert "sipet.conf no existe" in status["reason"]


def test_bootstrap_installation_refreshes_runtime_and_returns_superadmin(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        installer_service,
        "initialize_database_from_sipet_conf",
        lambda payload: {"db_url": "sqlite:////tmp/test.db", "connected": True, "error": "", "payload": dict(payload)},
    )
    monkeypatch.setattr(installer_service, "_refresh_runtime_after_install", lambda: calls.append("refresh"))
    monkeypatch.setattr(installer_service, "_ensure_installation_superadmin", lambda payload: {"username": "root", "email": "root@sipet.local"})
    monkeypatch.setattr(
        installer_service,
        "get_installation_status",
        lambda: {"required": False, "reason": "", "config_path": "/tmp/sipet.conf", "settings": {}},
    )

    class FakeRuntimeApp:
        @staticmethod
        def run_core_schema_bootstrap(*, force_refresh_database: bool = False) -> None:
            calls.append(f"bootstrap:{force_refresh_database}")

    monkeypatch.setattr(installer_service, "_get_runtime_app_module", lambda: FakeRuntimeApp)
    result = installer_service.bootstrap_installation({"db_name": "sipet"})

    assert result["connected"] is True
    assert result["superadmin"]["username"] == "root"
    assert calls == ["refresh", "bootstrap:False"]
