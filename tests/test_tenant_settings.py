from fastapi_modulo.core.tenant_settings import build_database_name, normalize_tenant_slug
from fastapi_modulo.core.tenant_types import DatabaseEngine
from fastapi_modulo.core import ARCHITECTURE_SETTINGS


def test_normalize_tenant_slug() -> None:
    assert normalize_tenant_slug("Cliente-1.midominio.com") == "cliente_1_midominio_com"


def test_build_database_name() -> None:
    assert build_database_name("cliente1.midominio.com", "prod") == "cliente1_midominio_com_prod"


def test_architecture_defaults() -> None:
    assert ARCHITECTURE_SETTINGS.web_framework == "fastapi"
    assert ARCHITECTURE_SETTINGS.orm == "sqlalchemy"
    assert ARCHITECTURE_SETTINGS.production_engine == DatabaseEngine.POSTGRESQL
