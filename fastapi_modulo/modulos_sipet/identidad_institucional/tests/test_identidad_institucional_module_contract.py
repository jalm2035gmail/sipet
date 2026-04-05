from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos_sipet.identidad_institucional.__manifest__ import MANIFEST


MODULE_ROOT = Path(__file__).resolve().parents[1]
WEB_MODULE_ROOT = MODULE_ROOT.parent / "web"


def test_identidad_institucional_manifest_declares_module_assets() -> None:
    assets = MANIFEST.get("assets") or {}
    declared_css = set(assets.get("css") or [])
    declared_js = set(assets.get("js") or [])

    css_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.css")
        if "tests" not in path.parts
    }
    js_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.js")
        if "tests" not in path.parts
    }

    assert css_files.issubset(declared_css)
    assert js_files.issubset(declared_js)


def test_identidad_institucional_declares_own_tests() -> None:
    test_files = [path for path in (MODULE_ROOT / "tests").glob("test_*.py") if path.is_file()]

    assert test_files


def test_identidad_institucional_manifest_declares_refactored_structure() -> None:
    structure = MANIFEST.get("structure") or {}
    declared_router = set(structure.get("router") or [])
    declared_services = set(structure.get("services") or [])
    declared_tests = set(structure.get("tests") or [])

    assert "controladores/branding.py" in declared_router
    assert "controladores/empresa_usuarios.py" in declared_router
    assert "controladores/empresa_accesos.py" in declared_router
    assert "servicios/identidad_service.py" in declared_services
    assert "servicios/usuarios_empresa_service.py" in declared_services
    assert "servicios/acceso_empresa_service.py" in declared_services
    assert "tests/test_identidad_institucional_services.py" in declared_tests


def test_identidad_institucional_does_not_mutate_users_schema_at_runtime() -> None:
    controller_path = MODULE_ROOT / "controladores" / "identidad_institucional.py"
    content = controller_path.read_text(encoding="utf-8")

    assert "ALTER TABLE" not in content
    assert "_ensure_colaborador_cols" not in content
    assert "import sqlite3" not in content


def test_web_module_declares_users_empresa_access_migration() -> None:
    migration_path = WEB_MODULE_ROOT / "alembic" / "versions" / "20260402_0004_web_users_empresa_access_fields.py"
    content = migration_path.read_text(encoding="utf-8")

    assert migration_path.is_file()
    assert 'op.add_column("users", sa.Column("app_access"' in content
    assert 'op.add_column("users", sa.Column("menu_blocks"' in content
    assert 'op.add_column("users", sa.Column("conversation_access"' in content
    assert 'op.add_column("users", sa.Column("is_employee"' in content


def test_web_module_declares_sidebar_style_migration() -> None:
    migration_path = WEB_MODULE_ROOT / "alembic" / "versions" / "20260402_0005_web_login_identity_sidebar_style.py"
    content = migration_path.read_text(encoding="utf-8")

    assert migration_path.is_file()
    assert 'op.add_column(' in content
    assert '"web_login_identity"' in content
    assert '"sidebar_style_variant"' in content


def test_colaboradores_endpoint_declares_pagination_filters_and_meta_contract() -> None:
    controller_path = MODULE_ROOT / "controladores" / "identidad_institucional.py"
    content = controller_path.read_text(encoding="utf-8")

    users_controller = MODULE_ROOT / "controladores" / "empresa_usuarios.py"
    users_content = users_controller.read_text(encoding="utf-8")

    assert 'router.include_router(usuarios_router)' in content
    assert 'limit: Optional[int] = Query(default=None, ge=1, le=100)' in users_content
    assert 'offset: int = Query(default=0, ge=0)' in users_content
    assert 'detail: Literal["full", "light"] = Query(default="full")' in users_content
    assert "list_colaboradores_payload(" in users_content


def test_identidad_institucional_controller_is_router_assembly() -> None:
    controller_path = MODULE_ROOT / "controladores" / "identidad_institucional.py"
    content = controller_path.read_text(encoding="utf-8")

    assert "from .branding import router as branding_router" in content
    assert "from .empresa_accesos import router as accesos_router" in content
    assert "from .empresa_usuarios import router as usuarios_router" in content
    assert "router.include_router(branding_router)" in content
    assert "router.include_router(usuarios_router)" in content
    assert "router.include_router(accesos_router)" in content


def test_sprint_2_declares_domain_services_and_controllers() -> None:
    expected_files = [
        MODULE_ROOT / "controladores" / "branding.py",
        MODULE_ROOT / "controladores" / "empresa_usuarios.py",
        MODULE_ROOT / "controladores" / "empresa_accesos.py",
        MODULE_ROOT / "servicios" / "identidad_service.py",
        MODULE_ROOT / "servicios" / "usuarios_empresa_service.py",
        MODULE_ROOT / "servicios" / "acceso_empresa_service.py",
    ]

    assert all(path.is_file() for path in expected_files)


def test_identity_service_persists_sidebar_variant_and_template_uses_server_value() -> None:
    identity_service = (MODULE_ROOT / "servicios" / "identidad_service.py").read_text(encoding="utf-8")
    identity_view = (MODULE_ROOT / "vistas" / "identidad_institucional.html").read_text(encoding="utf-8")
    base_template = (MODULE_ROOT.parents[1] / "templates" / "base.html").read_text(encoding="utf-8")

    assert '"sidebar_style_variant"' in identity_service
    assert 'name="sidebar_style_variant"' in identity_view
    assert "window.localStorage.getItem('sipet_sidebar_style_variant') || '{{ sidebar_style_variant" in identity_view
    assert "window.localStorage.getItem('sipet_sidebar_style_variant') || serverVariant" in base_template


def test_login_identity_service_declares_stronger_upload_validation_contract() -> None:
    service_path = MODULE_ROOT.parent / "web" / "servicios" / "login_identity_service.py"
    content = service_path.read_text(encoding="utf-8")

    assert "IDENTITY_UPLOAD_SVG_MAX_BYTES" in content
    assert "IDENTITY_UPLOAD_IMAGE_MAX_BYTES" in content
    assert "def _detect_image_kind" in content
    assert "def _validate_identity_upload" in content
    assert "Formato de imagen no permitido." in content


def test_module_gitignore_covers_packaging_junk() -> None:
    gitignore_path = MODULE_ROOT / ".gitignore"
    content = gitignore_path.read_text(encoding="utf-8")

    assert "__pycache__/" in content
    assert "*.pyc" in content
    assert "__MACOSX/" in content
    assert ".pytest_cache/" in content


def test_module_tree_has_no_packaging_junk() -> None:
    junk_paths = [
        path
        for path in MODULE_ROOT.rglob("*")
        if "__pycache__" in path.parts or path.name == "__MACOSX" or path.suffix == ".pyc"
    ]

    assert junk_paths == []
