from fastapi_modulo.core import DEFAULT_DATABASE_ROUTER
from fastapi_modulo.core.database_router import DatabaseRouter, normalize_database_url


def test_normalize_database_url() -> None:
    assert normalize_database_url("postgres://user:pass@localhost/db") == "postgresql://user:pass@localhost/db"


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
