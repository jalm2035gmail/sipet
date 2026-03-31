from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos.empleados.controladores import empleados


def test_self_service_password_only_update_uses_existing_identity(monkeypatch) -> None:
    existing = SimpleNamespace(
        id=5,
        full_name="Dumas",
        usuario="enc-user",
        correo="enc-mail",
        departamento="",
        puesto="",
        jefe="",
        jefe_inmediato_id=None,
        celular="",
        coach="",
        role="administrador_tienda",
        rol_id=3,
        contrasena="old-hash",
        imagen=None,
        is_active=True,
        totp_enabled=False,
        totp_secret=None,
    )

    class _FakeQuery:
        def __init__(self, items):
            self._items = items

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return list(self._items)

        def first(self):
            return self._items[0] if self._items else None

    class _FakeDb:
        def __init__(self):
            self.added = []
            self.committed = False

        def query(self, model):
            if model is empleados.Usuario:
                return _FakeQuery([existing])
            if model is empleados.Rol:
                return _FakeQuery([SimpleNamespace(id=3, nombre="administrador_tienda")])
            return _FakeQuery([])

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.committed = True

        def refresh(self, item):
            return None

        def close(self):
            return None

    fake_db = _FakeDb()

    monkeypatch.setattr(empleados, "_db_session", lambda: fake_db)
    monkeypatch.setattr(empleados, "ensure_default_roles", lambda: None)
    monkeypatch.setattr(empleados, "_load_puestos_laborales_catalog", lambda: [])
    monkeypatch.setattr(empleados, "_load_colab_meta", lambda: {})
    monkeypatch.setattr(empleados, "_save_colab_meta", lambda meta: None)
    monkeypatch.setattr(empleados, "_resolve_access_app_options", lambda request: ["Mi tablero"])
    monkeypatch.setattr(empleados, "_normalize_colaborador_kpis", lambda raw, allowed_ids: [])
    monkeypatch.setattr(empleados, "decrypt_sensitive", lambda value: "dumas" if value == "enc-user" else "dumas@dumas.com")
    monkeypatch.setattr(empleados, "encrypt_sensitive", lambda value: f"enc:{value}")
    monkeypatch.setattr(empleados, "sensitive_lookup_hash", lambda value: f"hash:{value}")
    monkeypatch.setattr(empleados, "hash_password", lambda value: f"hashed:{value}")

    request = SimpleNamespace(state=SimpleNamespace(user_role="administrador_tienda", user_name="dumas", tenant_key=""))
    response = empleados.api_guardar_colaborador(request, {"id": 5, "contrasena": "dumasdumas"})

    assert response["success"] is True
    assert existing.contrasena == "hashed:dumasdumas"
    assert fake_db.committed is True
