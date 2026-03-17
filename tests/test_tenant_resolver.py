from fastapi_modulo.core import TenantResolver
from fastapi_modulo.core.tenant_resolver import classify_access_mode, normalize_host, tenant_key_from_host


def test_normalize_host() -> None:
    assert normalize_host("https://Cliente1.MiDominio.com:443/path") == "cliente1.midominio.com"


def test_classify_access_mode() -> None:
    assert classify_access_mode("/health") == "nodb"
    assert classify_access_mode("/admin/tenants") == "admin_global"
    assert classify_access_mode("/crm/contactos") == "tenant"


def test_tenant_key_from_host() -> None:
    assert tenant_key_from_host("cliente1.midominio.com") == "cliente1_midominio_com"


def test_resolve_tenant_from_domain() -> None:
    resolver = TenantResolver(default_tenant_id="default")
    assert resolver.resolve_tenant_from_domain("cliente1.midominio.com") == "cliente1_midominio_com"


def test_resolve_returns_db_context() -> None:
    resolver = TenantResolver(default_tenant_id="default")
    resolved = resolver.resolve("cliente1.midominio.com", path="/crm/contactos")
    assert resolved.tenant_id == "cliente1_midominio_com"
    assert resolved.access_mode == "tenant"
    assert resolved.db_key
    assert resolved.db_url
