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
