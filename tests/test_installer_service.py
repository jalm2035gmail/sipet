from pathlib import Path

from fastapi_modulo.core import database_router
from fastapi_modulo.modulos_sipet.instalacion.servicios import installer_service


def test_installation_status_requires_setup_when_conf_missing(monkeypatch) -> None:
    monkeypatch.setattr(installer_service, "SIPET_CONFIG_PATH", Path("/tmp/nonexistent-sipet.conf"))
    monkeypatch.setattr(installer_service, "has_explicit_database_config", lambda: False)
    monkeypatch.setattr(installer_service, "get_sipet_conf_settings", lambda: {"path": "/tmp/nonexistent-sipet.conf"})

    status = installer_service.get_installation_status()

    assert status["required"] is True
    assert "No existe configuracion" in status["reason"]


def test_installation_status_uses_env_database_when_conf_missing(monkeypatch) -> None:
    monkeypatch.setattr(installer_service, "SIPET_CONFIG_PATH", Path("/tmp/nonexistent-sipet.conf"))
    monkeypatch.setattr(installer_service, "has_explicit_database_config", lambda: True)
    monkeypatch.setattr(installer_service, "get_sipet_conf_settings", lambda: {"path": "/tmp/nonexistent-sipet.conf"})
    monkeypatch.setattr(installer_service, "can_connect_current_database", lambda: (True, ""))

    status = installer_service.get_installation_status()

    assert status["required"] is False


def test_list_domain_conf_entries_exposes_runtime_entry_from_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database_router, "DOMAIN_CONFIG_DIR", tmp_path / "dominios")
    monkeypatch.setattr(database_router, "SIPET_CONFIG_PATH", tmp_path / "sipet.conf")
    monkeypatch.setenv("MYSQL_URL", "mysql://root:secret@mysql.railway.internal:3306/railway")
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "backend-production-f1ca.up.railway.app")

    entries = database_router.list_domain_conf_entries()

    assert len(entries) == 1
    assert entries[0]["domain"] == "backend-production-f1ca.up.railway.app"
    assert entries[0]["db_engine"] == "mysql"
    assert entries[0]["db_name"] == "railway"
    assert entries[0]["is_runtime_entry"] is True


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


def test_get_sipet_superadmin_settings_reads_superadmin_section(tmp_path, monkeypatch) -> None:
    conf_path = tmp_path / "sipet.conf"
    conf_path.write_text(
        "[options]\n"
        "domain = localhost\n\n"
        "[superadmin]\n"
        "superadmin_user = 0konomiyaki\n"
        "superadmin_password = XX,$,26,sipet,26,$,XX\n"
        "superadmin_email = alopez@avancoop.org\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_router, "SIPET_CONFIG_PATH", conf_path)

    settings = database_router.get_sipet_superadmin_settings()

    assert settings["username"] == "0konomiyaki"
    assert settings["password"] == "XX,$,26,sipet,26,$,XX"
    assert settings["email"] == "alopez@avancoop.org"
