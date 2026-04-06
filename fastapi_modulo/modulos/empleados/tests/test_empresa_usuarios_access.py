from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos.empleados.controladores import empleados


class _FakeRole:
    def __init__(self, role_id: int, nombre: str) -> None:
        self.id = role_id
        self.nombre = nombre


class _FakeRoleQuery:
    def __init__(self, rows) -> None:
        self._rows = list(rows)

    def all(self):
        return list(self._rows)


class _FakeUserQuery:
    def __init__(self, user) -> None:
        self._user = user

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._user


class _FakeDb:
    def __init__(self, roles, user) -> None:
        self._roles = roles
        self._user = user
        self.closed = False

    def query(self, model):
        if model is empleados.Rol:
            return _FakeRoleQuery(self._roles)
        if model is empleados.Usuario:
            return _FakeUserQuery(self._user)
        raise AssertionError(model)

    def close(self):
        self.closed = True


def test_empresa_usuarios_page_allows_superadmin_from_db(monkeypatch) -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(user_role="usuario", user_name="0konomiyaki"),
        cookies={},
    )
    db = _FakeDb(
        [ _FakeRole(1, "superadministrador") ],
        SimpleNamespace(rol_id=1, role="usuario", username="0konomiyaki", usuario_hash="hash"),
    )

    monkeypatch.setattr(empleados, "_db_session", lambda: db)
    monkeypatch.setattr(empleados, "sensitive_lookup_hash", lambda _value: "hash")
    monkeypatch.setattr(empleados, "is_global_superadmin_username", lambda _value: False)
    monkeypatch.setattr(empleados, "_build_colaboradores_payload", lambda _request: {"success": True, "data": []})
    monkeypatch.setattr(empleados, "_load_empresa_usuarios_template", lambda initial_section="usuarios": "<section>usuarios</section>")
    monkeypatch.setattr(
        empleados,
        "render_backend_page",
        lambda request, **kwargs: SimpleNamespace(content=kwargs.get("content", ""), kwargs=kwargs),
    )

    response = empleados._render_empresa_usuarios_page(request)

    assert "Solo administrador y superadministrador pueden gestionar usuarios." not in response.content
    assert db.closed is True


def test_empresa_usuarios_page_allows_global_superadmin_username(monkeypatch) -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(user_role="usuario", user_name="0konomiyaki"),
        cookies={},
    )

    monkeypatch.setattr(empleados, "is_global_superadmin_username", lambda value: value == "0konomiyaki")
    monkeypatch.setattr(empleados, "_db_session", lambda: (_ for _ in ()).throw(RuntimeError("db not needed")))
    monkeypatch.setattr(empleados, "_build_colaboradores_payload", lambda _request: {"success": True, "data": []})
    monkeypatch.setattr(empleados, "_load_empresa_usuarios_template", lambda initial_section="usuarios": "<section>usuarios</section>")
    monkeypatch.setattr(
        empleados,
        "render_backend_page",
        lambda request, **kwargs: SimpleNamespace(content=kwargs.get("content", ""), kwargs=kwargs),
    )

    response = empleados._render_empresa_usuarios_page(request)

    assert "Solo administrador y superadministrador pueden gestionar usuarios." not in response.content


def test_empresa_usuarios_page_allows_superadmin_from_cookie_role(monkeypatch) -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(user_role="", user_name=""),
        cookies={"user_role": "superadministrador", "user_name": "0konomiyaki"},
    )

    monkeypatch.setattr(empleados, "is_global_superadmin_username", lambda _value: False)
    monkeypatch.setattr(empleados, "_db_session", lambda: (_ for _ in ()).throw(RuntimeError("db not needed")))
    monkeypatch.setattr(empleados, "_build_colaboradores_payload", lambda _request: {"success": True, "data": []})
    monkeypatch.setattr(empleados, "_load_empresa_usuarios_template", lambda initial_section="usuarios": "<section>usuarios</section>")
    monkeypatch.setattr(
        empleados,
        "render_backend_page",
        lambda request, **kwargs: SimpleNamespace(content=kwargs.get("content", ""), kwargs=kwargs),
    )

    response = empleados._render_empresa_usuarios_page(request)

    assert "Solo administrador y superadministrador pueden gestionar usuarios." not in response.content
