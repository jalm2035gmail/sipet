from __future__ import annotations

import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace


MODULE_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def patched_modules(stubs: dict[str, types.ModuleType]):
    previous = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def load_module(module_name: str, relative_path: str, stubs: dict[str, types.ModuleType]):
    spec = importlib.util.spec_from_file_location(module_name, MODULE_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    with patched_modules(stubs):
        spec.loader.exec_module(module)
    return module


def test_empresa_permissions_resolves_editor_scope() -> None:
    access_stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.access_service")
    module_registry_stub = types.ModuleType("fastapi_modulo.core.module_registry")
    module_registry_stub.list_modules_payload = lambda: []
    access_stub.can_assign_role = lambda *args, **kwargs: True
    access_stub.get_role_permission_catalog = lambda *args, **kwargs: []
    access_stub.get_user_screen_access_levels = lambda request: {
        "empresa": {"special_permissions": True},
        "empresa.roles": {"read_only": True},
        "empresa.acceso": {"read_only": True},
    }
    access_stub.is_admin_or_superadmin = lambda request: False
    access_stub.is_superadmin = lambda request: False
    access_stub.normalize_role_name = lambda value: str(value or "").strip().lower()
    access_stub.save_role_permission_profile = lambda **kwargs: kwargs

    service = load_module(
        "test_acceso_empresa_service",
        "servicios/acceso_empresa_service.py",
        {
            "fastapi_modulo.modulos_sipet.web.servicios.access_service": access_stub,
            "fastapi_modulo.core.module_registry": module_registry_stub,
        },
    )

    permissions = service.empresa_permissions(SimpleNamespace())

    assert permissions["ver_branding"] is True
    assert permissions["editar_branding"] is True
    assert permissions["ver_usuarios"] is False
    assert permissions["gestionar_acceso"] is False
    assert permissions["ver_acceso"] is True


def test_build_identidad_view_context_exposes_sidebar_variant() -> None:
    login_stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.login_identity_service")
    login_stub.DEFAULT_LOGIN_IDENTITY = {
        "favicon_filename": "icon.png",
        "logo_filename": "icon.png",
        "login_logo_filename": "icon.png",
        "desktop_bg_filename": "fondo.jpg",
        "mobile_bg_filename": "movil.jpg",
        "company_short_name": "AVAN",
        "login_message": "Mensaje",
        "menu_position": "arriba",
    }
    login_stub._build_login_asset_url = lambda selected, default: f"/templates/{selected or default}"
    login_stub._load_login_identity = lambda: {
        "favicon_filename": "fav.png",
        "logo_filename": "logo.png",
        "login_logo_filename": "login.png",
        "desktop_bg_filename": "desktop.webp",
        "mobile_bg_filename": "mobile.webp",
        "company_short_name": "SIPET",
        "login_message": "Hola",
        "menu_position": "abajo",
        "sidebar_style_variant": "original",
    }
    login_stub.clear_frontend_page_cache = lambda: None
    login_stub.remove_login_image_if_custom = lambda filename: None
    login_stub.save_login_identity = lambda data: None
    login_stub.store_login_image = lambda upload, prefix: None

    service = load_module(
        "test_identidad_service",
        "servicios/identidad_service.py",
        {"fastapi_modulo.modulos_sipet.web.servicios.login_identity_service": login_stub},
    )

    context = service.build_identidad_view_context()

    assert context["company_short_name"] == "SIPET"
    assert context["menu_position"] == "abajo"
    assert context["sidebar_style_variant"] == "original"
    assert context["loaded_assets"] == 5


def test_usuarios_service_list_payload_returns_meta_in_light_mode() -> None:
    core_db_stub = types.ModuleType("fastapi_modulo.core.db")
    module_registry_stub = types.ModuleType("fastapi_modulo.core.module_registry")
    access_stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.access_service")
    auth_stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.auth_service")
    models_stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.modelos.core_models")

    class DummyUser:
        id = object()
        full_name = object()
        usuario = object()
        correo = object()
        celular = object()
        departamento = object()
        puesto = object()
        role = object()
        is_active = object()
        totp_enabled = object()
        is_employee = object()
        app_access = object()
        menu_blocks = object()
        conversation_access = object()

        def __init__(self, user_id: int, role: str, active: bool = True) -> None:
            self.id = user_id
            self.full_name = f"Nombre {user_id}"
            self.usuario = f"user{user_id}"
            self.correo = f"user{user_id}@mail.test"
            self.celular = "555"
            self.departamento = "Ventas"
            self.puesto = "Analista"
            self.jefe_inmediato_id = 10
            self.imagen = "/avatar.png"
            self.role = role
            self.is_active = active
            self.totp_enabled = False
            self.is_employee = True
            self.app_access = '["CRM"]'
            self.menu_blocks = '["ventas"]'
            self.conversation_access = '{"role":"administrador"}'

    class DummyQuery:
        def __init__(self, rows):
            self.rows = list(rows)
            self._offset = 0
            self._limit = None

        def options(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def count(self):
            return len(self.rows)

        def offset(self, value):
            self._offset = value
            return self

        def limit(self, value):
            self._limit = value
            return self

        def all(self):
            end = None if self._limit is None else self._offset + self._limit
            return self.rows[self._offset:end]

    class DummySession:
        def __init__(self, rows):
            self.rows = rows

        def query(self, _model):
            return DummyQuery(self.rows)

        def close(self):
            return None

    rows = [DummyUser(1, "administrador"), DummyUser(2, "usuario")]
    core_db_stub.SessionLocal = lambda: DummySession(rows)
    module_registry_stub.get_active_app_access_names = lambda: ["CRM", "Mi tablero"]
    access_stub.can_assign_role = lambda *_args, **_kwargs: True
    access_stub.get_role_permission_catalog = lambda *_args, **_kwargs: [{"role_name": "usuario"}]
    access_stub.get_visible_role_names = lambda *_args, **_kwargs: ["usuario", "administrador"]
    access_stub.normalize_role_name = lambda value: str(value or "").strip().lower()
    access_stub.sensitive_lookup_hash = lambda value: f"hash:{value}"
    auth_stub.decrypt_sensitive = lambda value: value
    auth_stub.encrypt_sensitive = lambda value: value
    auth_stub.hash_password = lambda value: f"hashed:{value}"
    models_stub.Usuario = DummyUser

    service = load_module(
        "test_usuarios_empresa_service",
        "servicios/usuarios_empresa_service.py",
        {
            "fastapi_modulo.core.db": core_db_stub,
            "fastapi_modulo.core.module_registry": module_registry_stub,
            "fastapi_modulo.modulos_sipet.web.servicios.access_service": access_stub,
            "fastapi_modulo.modulos_sipet.web.servicios.auth_service": auth_stub,
            "fastapi_modulo.modulos_sipet.web.modelos.core_models": models_stub,
        },
    )
    service.load_only = lambda *args, **kwargs: None

    payload = service.list_colaboradores_payload(
        SimpleNamespace(),
        limit=1,
        offset=0,
        detail="light",
        include_catalogs="false",
    )

    assert payload["success"] is True
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["total"] == 2
    assert payload["meta"]["has_more"] is True
    assert len(payload["data"]) == 1
    assert "imagen" not in payload["data"][0]
