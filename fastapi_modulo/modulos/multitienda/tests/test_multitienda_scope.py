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
        return _FakeMappingsResult(self._store_row)

    def close(self):
        return None


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


def test_visible_module_sections_hide_gestion_for_non_superadmin() -> None:
    sections = controller._visible_module_sections("administrador_tienda")

    section_ids = [item["id"] for item in sections]

    assert "gestion" not in section_ids
    assert "inicio" in section_ids
    assert "productos" in section_ids
    assert "configuracion" in section_ids


def test_visible_module_sections_keep_gestion_for_superadmin() -> None:
    sections = controller._visible_module_sections("superadministrador")

    section_ids = [item["id"] for item in sections]

    assert "gestion" in section_ids
    assert "referidos" in section_ids
    assert "productos" in section_ids
    assert "configuracion" in section_ids


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

    response = controller.multitienda_referidos_entrypoint(request)

    assert response.headers["location"] == "/referidos?business_slug=tienda-demo"
