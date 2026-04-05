from pathlib import Path

from fastapi_modulo.core import DEFAULT_DATABASE_ROUTER
from fastapi_modulo.core import database_router as database_router_module
from fastapi_modulo.core.database_router import DatabaseRouter, normalize_database_url


def test_normalize_database_url() -> None:
    assert normalize_database_url("postgres://user:pass@localhost/db") == "postgresql://user:pass@localhost/db"
    assert normalize_database_url("mysql://user:pass@localhost/db") == "mysql+pymysql://user:pass@localhost/db"


def test_database_router_resolves_default_target() -> None:
    router = DatabaseRouter()
    target = router.get_database_target("cliente1.midominio.com")
    assert target.db_url
    assert target.engine_name in {"sqlite", "postgresql"}


def test_database_router_request_host_roundtrip() -> None:
    token = DEFAULT_DATABASE_ROUTER.set_request_host("cliente1.midominio.com")
    try:
        assert DEFAULT_DATABASE_ROUTER.get_request_host() == "cliente1.midominio.com"
    finally:
        DEFAULT_DATABASE_ROUTER.reset_request_host(token)


def test_database_router_uses_mysql_url_env(monkeypatch) -> None:
    monkeypatch.delenv("DATAMAIN_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("POSTGRESQL_URL", raising=False)
    monkeypatch.setenv("MYSQL_URL", "mysql://user:pass@db.railway.internal:3306/railway")
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", Path("/tmp/nonexistent-sipet.conf"))

    router = DatabaseRouter()

    assert router.default_database_url == "mysql+pymysql://user:pass@db.railway.internal:3306/railway"


def test_resolve_sipet_config_path_prefers_domain_specific_conf(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text("[options]\ndomain = default.local\n", encoding="utf-8")
    domain_conf = domain_dir / "oaxaca.tunegociovale.com.conf"
    domain_conf.write_text("[options]\ndomain = oaxaca.tunegociovale.com\n", encoding="utf-8")

    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", global_conf)

    resolved = database_router_module.resolve_sipet_config_path("oaxaca.tunegociovale.com")

    assert resolved == domain_conf


def test_resolve_sipet_config_path_uses_localhost_conf_for_loopback_alias(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text("[options]\ndomain = default.local\n", encoding="utf-8")
    localhost_conf = domain_dir / "localhost.conf"
    localhost_conf.write_text("[options]\ndomain = localhost\nsqlite_db_path = /tmp/local.db\n", encoding="utf-8")

    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", global_conf)

    resolved = database_router_module.resolve_sipet_config_path("127.0.0.1")

    assert resolved == localhost_conf


def test_get_sipet_superadmin_settings_uses_domain_conf(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text(
        "[options]\ndomain = default.local\n\n"
        "[superadmin]\n"
        "superadmin_user = global\n",
        encoding="utf-8",
    )
    domain_conf = domain_dir / "oaxaca.tunegociovale.com.conf"
    domain_conf.write_text(
        "[options]\ndomain = oaxaca.tunegociovale.com\n\n"
        "[superadmin]\n"
        "superadmin_user = oaxaca-admin\n"
        "superadmin_password = secret\n"
        "superadmin_email = admin@oaxaca.test\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", global_conf)

    settings = database_router_module.get_sipet_superadmin_settings("oaxaca.tunegociovale.com")

    assert settings["username"] == "oaxaca-admin"
    assert settings["password"] == "secret"
    assert settings["email"] == "admin@oaxaca.test"


def test_has_complete_database_config_requires_password_for_postgresql(tmp_path, monkeypatch) -> None:
    conf_path = tmp_path / "sipet.conf"
    conf_path.write_text(
        "[options]\n"
        "domain = oaxaca.tunegociovale.com\n"
        "db_host = 127.0.0.1\n"
        "db_port = 5432\n"
        "db_user = sipet\n"
        "db_name = sipet_oaxaca\n"
        "db_engine = postgresql\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", conf_path)
    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", tmp_path / "dominios")

    assert database_router_module.has_complete_database_config() is False


def test_has_complete_database_config_accepts_complete_domain_conf(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    domain_conf = domain_dir / "oaxaca.tunegociovale.com.conf"
    domain_conf.write_text(
        "[options]\n"
        "domain = oaxaca.tunegociovale.com\n"
        "db_host = 127.0.0.1\n"
        "db_port = 5432\n"
        "db_user = sipet\n"
        "db_password = secret\n"
        "db_name = sipet_oaxaca\n"
        "db_engine = postgresql\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", tmp_path / "sipet.conf")

    assert database_router_module.has_complete_database_config("oaxaca.tunegociovale.com") is True


def test_load_domain_database_map_reuses_localhost_mapping_for_loopback_aliases(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    domain_conf = domain_dir / "localhost.conf"
    domain_conf.write_text(
        "[options]\n"
        "domain = localhost\n"
        "sqlite_db_path = /tmp/local.db\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)

    mapping = database_router_module.load_domain_database_map()

    assert mapping["localhost"] == "sqlite:////tmp/local.db"
    assert mapping["127.0.0.1"] == "sqlite:////tmp/local.db"


def test_resolve_database_url_from_sipet_conf_encodes_special_chars_in_password(tmp_path, monkeypatch) -> None:
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir(parents=True)
    domain_conf = domain_dir / "oaxaca.tunegociovale.com.conf"
    domain_conf.write_text(
        "[options]\n"
        "domain = oaxaca.tunegociovale.com\n"
        "db_host = 127.0.0.1\n"
        "db_port = 5432\n"
        "db_user = sipet\n"
        "db_password = XX,$,26/sipet@26,%\n"
        "db_name = sipet_oaxaca\n"
        "db_engine = postgresql\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_router_module, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setattr(database_router_module, "SIPET_CONFIG_PATH", tmp_path / "sipet.conf")

    resolved = database_router_module.resolve_database_url_from_sipet_conf("oaxaca.tunegociovale.com")

    assert resolved == "postgresql://sipet:XX%2C%24%2C26%2Fsipet%4026%2C%25@127.0.0.1:5432/sipet_oaxaca"
