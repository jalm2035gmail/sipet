from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos.multitienda.controladores import multitienda as controller
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import encrypt_sensitive


class _FakeRole:
    def __init__(self, role_id: int, nombre: str) -> None:
        self.id = role_id
        self.nombre = nombre


class _FakeUserQuery:
    def __init__(self, rows) -> None:
        self._rows = rows

    def all(self):
        return list(self._rows)

    def order_by(self, *_args, **_kwargs):
        return self


class _FakeMappingsResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row

    def all(self):
        return [self._row] if self._row else []

    def mappings(self):
        return self


class _FakeMappingsRowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)

    def mappings(self):
        return self


class _FakeDb:
    def __init__(self, roles, users, store_row):
        self._roles = roles
        self._users = users
        self._store_row = store_row
        self.bound_params = []

    def query(self, model):
        if model is controller.Rol:
            return _FakeUserQuery(self._roles)
        if model is controller.Usuario:
            return _FakeUserQuery(self._users)
        raise AssertionError(model)

    def execute(self, _statement, params=None):
        self.bound_params.append(dict(params or {}))
        row = self._store_row
        if isinstance(row, list):
            row = row.pop(0) if row else None
        return _FakeMappingsResult(row)

    def close(self):
        return None


class _FakeStoreListDb(_FakeDb):
    def __init__(self, roles, users, store_row, execute_results):
        super().__init__(roles, users, store_row)
        self._execute_results = list(execute_results)

    def execute(self, _statement, params=None):
        self.bound_params.append(dict(params or {}))
        if self._execute_results:
            next_result = self._execute_results.pop(0)
            if isinstance(next_result, list):
                return _FakeMappingsRowsResult(next_result)
            return _FakeMappingsResult(next_result)
        return super().execute(_statement, params)


def _request(username: str = "dumas") -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(user_name=username, username=username),
        cookies={},
    )


def test_resolve_store_scope_restricts_store_admin_to_assigned_store() -> None:
    role = _FakeRole(1, "administrador_tienda")
    user = SimpleNamespace(
        id=10,
        usuario=encrypt_sensitive("dumas"),
        correo=encrypt_sensitive("dumas@dumas.com"),
        rol_id=1,
        role="administrador_tienda",
        full_name="dumas",
    )
    db = _FakeDb([role], [user], {"id": 77, "store_slug": "tienda-demo"})

    scope = controller._resolve_store_scope(_request(), db)

    assert scope == {
        "role": "administrador_tienda",
        "user_id": 10,
        "store_id": 77,
        "store_slug": "tienda-demo",
        "restricted": True,
    }


def test_resolve_store_scope_falls_back_to_employee_store_assignment() -> None:
    role = _FakeRole(1, "vendedor_tienda")
    user = SimpleNamespace(
        id=10,
        usuario=encrypt_sensitive("dumas"),
        correo=encrypt_sensitive("dumas@dumas.com"),
        rol_id=1,
        role="vendedor_tienda",
        full_name="dumas",
    )
    db = _FakeDb([role], [user], [None, {"id": 77, "store_slug": "dumas"}])

    scope = controller._resolve_store_scope(_request(), db)

    assert scope == {
        "role": "vendedor_tienda",
        "user_id": 10,
        "store_id": 77,
        "store_slug": "dumas",
        "restricted": True,
    }


def test_store_admin_user_listing_returns_only_current_admin(monkeypatch) -> None:
    role = _FakeRole(1, "administrador_tienda")
    current_user = SimpleNamespace(
        id=10,
        usuario=encrypt_sensitive("dumas"),
        correo=encrypt_sensitive("dumas@dumas.com"),
        rol_id=1,
        role="administrador_tienda",
        full_name="dumas",
    )
    other_user = SimpleNamespace(
        id=11,
        usuario=encrypt_sensitive("otro"),
        correo=encrypt_sensitive("otro@dumas.com"),
        rol_id=1,
        role="administrador_tienda",
        full_name="otro",
    )
    db = _FakeDb([role], [current_user, other_user], {"id": 77, "store_slug": "tienda-demo"})
    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: db)

    payload = controller.multitienda_store_admin_users(_request())

    assert payload["success"] is True
    assert payload["data"] == [
        {
            "id": 10,
            "usuario": "dumas",
            "nombre": "dumas",
            "rol": "administrador_tienda",
        }
    ]


def test_list_stores_falls_back_to_current_username_match(monkeypatch) -> None:
    role = _FakeRole(1, "administrador_tienda")
    user = SimpleNamespace(
        id=10,
        usuario=encrypt_sensitive("dumas"),
        correo=encrypt_sensitive("dumas@dumas.com"),
        rol_id=1,
        role="administrador_tienda",
        full_name="dumas",
    )
    store_row = {
        "id": 2,
        "vendor_id": 5,
        "store_name": "Dumas",
        "store_slug": "dumas",
        "store_theme": "{}",
        "is_featured": True,
        "is_active": True,
        "full_name": "dumas",
        "encrypted_username": encrypt_sensitive("dumas"),
    }
    db = _FakeStoreListDb(
        [role],
        [user],
        {"id": 77, "store_slug": "tienda-demo"},
        [
            {"id": 77, "store_slug": "tienda-demo"},
            [],
            [store_row],
        ],
    )
    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: db)

    payload = controller.multitienda_list_stores(_request())

    assert payload["success"] is True
    assert payload["data"][0]["name"] == "Dumas"


def test_visible_module_sections_hide_gestion_for_non_superadmin(monkeypatch) -> None:
    monkeypatch.setattr(controller, "_optional_section_available", lambda section_id: True)
    sections = controller._visible_module_sections("administrador_tienda")

    section_ids = [item["id"] for item in sections]

    assert "gestion" not in section_ids
    assert "inicio" in section_ids
    assert "productos" in section_ids
    assert "configuracion" in section_ids


def test_visible_module_sections_keep_gestion_for_superadmin(monkeypatch) -> None:
    monkeypatch.setattr(controller, "_optional_section_available", lambda section_id: True)
    sections = controller._visible_module_sections("superadministrador")

    section_ids = [item["id"] for item in sections]

    assert "gestion" in section_ids
    assert "referidos" in section_ids
    assert "productos" in section_ids
    assert "configuracion" in section_ids


def test_visible_module_sections_hide_fidelizacion_without_store_permission(monkeypatch) -> None:
    monkeypatch.setattr(controller, "_optional_section_available", lambda section_id: True)

    sections = controller._visible_module_sections("administrador_tienda", {"referrals": "1"})

    section_ids = [item["id"] for item in sections]

    assert "referidos" in section_ids
    assert "fidelizacion" not in section_ids


def test_visible_module_sections_show_fidelizacion_with_store_permission(monkeypatch) -> None:
    monkeypatch.setattr(controller, "_optional_section_available", lambda section_id: True)

    sections = controller._visible_module_sections("administrador_tienda", {"fidelizacion": "1"})

    section_ids = [item["id"] for item in sections]

    assert "fidelizacion" in section_ids


def test_gestion_entrypoint_redirects_store_admin_to_configuracion() -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    response = controller.multitienda_gestion_entrypoint(request)

    assert response.headers["location"] == "/multitienda/configuracion"


def test_referidos_entrypoint_redirects_to_central_referidos_module(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    class _FakeDb:
        def close(self):
            return None

    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: _FakeDb())
    monkeypatch.setattr(
        controller,
        "_resolve_store_scope",
        lambda request, db: {
            "role": "administrador_tienda",
            "user_id": 10,
            "store_id": 77,
            "store_slug": "tienda-demo",
            "restricted": True,
        },
    )
    monkeypatch.setattr(controller, "_resolve_store_permissions", lambda db, scope: {"referrals": "1"})
    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/referidos?business_slug=tienda-demo")

    response = controller.multitienda_referidos_entrypoint(request)

    assert response.headers["location"] == "/referidos?business_slug=tienda-demo"


def test_notificaciones_pwa_entrypoint_redirects_to_pwa_module(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    class _FakeDb:
        def close(self):
            return None

    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: _FakeDb())
    monkeypatch.setattr(
        controller,
        "_resolve_store_scope",
        lambda request, db: {
            "role": "administrador_tienda",
            "user_id": 10,
            "store_id": 77,
            "store_slug": "tienda-demo",
            "restricted": True,
        },
    )
    monkeypatch.setattr(controller, "_resolve_store_permissions", lambda db, scope: {"pwa_notifications": "1"})
    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/pwa/notificaciones-tienda?business_slug=tienda-demo")

    response = controller.multitienda_notificaciones_pwa_entrypoint(request)

    assert response.headers["location"] == "/pwa/notificaciones-tienda?business_slug=tienda-demo"


def test_reservaciones_entrypoint_redirects_to_central_reservaciones_module(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    class _FakeDb:
        def close(self):
            return None

    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: _FakeDb())
    monkeypatch.setattr(
        controller,
        "_resolve_store_scope",
        lambda request, db: {
            "role": "administrador_tienda",
            "user_id": 10,
            "store_id": 77,
            "store_slug": "tienda-demo",
            "restricted": True,
        },
    )
    monkeypatch.setattr(controller, "_resolve_store_permissions", lambda db, scope: {"appointments": "1"})
    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/reservaciones")

    response = controller.multitienda_reservaciones_entrypoint(request)

    assert response.headers["location"] == "/reservaciones"


def test_institucion_financiera_entrypoint_redirects_to_intelicoop(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    class _FakeDb:
        def close(self):
            return None

    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: _FakeDb())
    monkeypatch.setattr(
        controller,
        "_resolve_store_scope",
        lambda request, db: {
            "role": "administrador_tienda",
            "user_id": 10,
            "store_id": 77,
            "store_slug": "tienda-demo",
            "restricted": True,
        },
    )
    monkeypatch.setattr(controller, "_resolve_store_permissions", lambda db, scope: {"can_use_financial": "1"})
    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/inicio/intelicoop")

    response = controller.multitienda_institucion_financiera_entrypoint(request)

    assert response.headers["location"] == "/inicio/intelicoop"


def test_repartidores_entrypoint_redirects_to_central_repartidores_module(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="superadministrador"))

    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/repartidores")

    response = controller.multitienda_repartidores_entrypoint(request)

    assert response.headers["location"] == "/repartidores"


def test_subastas_entrypoint_redirects_to_central_subastas_module(monkeypatch) -> None:
    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda"))

    class _FakeDb:
        def close(self):
            return None

    monkeypatch.setattr(controller, "_db_session_for_request", lambda request: _FakeDb())
    monkeypatch.setattr(
        controller,
        "_resolve_store_scope",
        lambda request, db: {
            "role": "administrador_tienda",
            "user_id": 10,
            "store_id": 77,
            "store_slug": "tienda-demo",
            "restricted": True,
        },
    )
    monkeypatch.setattr(controller, "_resolve_store_permissions", lambda db, scope: {"can_use_auctions": "1"})
    monkeypatch.setattr(controller, "_resolve_integrated_section_target", lambda section_id, scope=None: "/subastas")

    response = controller.multitienda_subastas_entrypoint(request)

    assert response.headers["location"] == "/subastas"
