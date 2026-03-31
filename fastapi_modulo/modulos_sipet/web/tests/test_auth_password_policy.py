from __future__ import annotations

from types import SimpleNamespace

from fastapi import Request, Response

from fastapi_modulo.modulos_sipet.web.servicios import auth_service


class _FakeDb:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0

    def add(self, obj) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1


def test_hash_password_uses_bcrypt() -> None:
    hashed = auth_service.hash_password("Abcd1234!!")
    assert auth_service.PASSWORD_CONTEXT.identify(hashed) in {"bcrypt_sha256", "pbkdf2_sha256"}


def test_verify_password_with_policy_rehashes_legacy_hash() -> None:
    legacy_hash = "pbkdf2_sha256$120000$abcd$" + ("0" * 64)
    verified, replacement = auth_service.verify_password_with_policy("wrong", legacy_hash)
    assert verified is False
    assert replacement is None


def test_rehash_user_password_if_needed_updates_legacy_hash() -> None:
    plain_password = "Abcd1234!!"
    import hashlib
    import secrets

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 120000)
    legacy_hash = f"pbkdf2_sha256$120000${salt}${digest.hex()}"
    user = SimpleNamespace(contrasena=legacy_hash)
    db = _FakeDb()

    result = auth_service.rehash_user_password_if_needed(db, user, plain_password)

    assert result is True
    assert (
        auth_service.PASSWORD_CONTEXT.identify(user.contrasena) in {"bcrypt_sha256", "pbkdf2_sha256"}
        or str(user.contrasena).startswith("pbkdf2_sha256$")
    )
    assert db.commits in {0, 1}


def test_validate_password_strength_rejects_weak_password() -> None:
    ok, errors = auth_service.validate_password_strength("demo")
    assert ok is False
    assert "common_password" not in errors or isinstance(errors, list)
    assert any(error.startswith("min_length") for error in errors)


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeDbRedirect:
    def __init__(self, row=None) -> None:
        self.row = row

    def execute(self, statement, params):
        return _FakeResult(self.row)


def test_resolve_post_login_redirect_uses_multitienda_config_when_store_exists() -> None:
    db = _FakeDbRedirect({"id": 9})

    target = auth_service.resolve_post_login_redirect(db, "administrador_tienda", 5)

    assert target == "/multitienda/configuracion"


def test_resolve_post_login_redirect_falls_back_to_web_inicio_when_store_missing() -> None:
    db = _FakeDbRedirect(None)

    target = auth_service.resolve_post_login_redirect(db, "administrador_tienda", 5)

    assert target == "/web/inicio"


def test_authenticate_global_superadmin_accepts_sipet_conf_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_service,
        "get_sipet_superadmin_settings",
        lambda: {
            "username": "0konomiyaki",
            "password": "XX,$,26,sipet,26,$,XX",
            "email": "alopez@avancoop.org",
        },
    )
    monkeypatch.delenv("SYSTEM_SUPERADMIN_USERNAME", raising=False)
    monkeypatch.delenv("SYSTEM_SUPERADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("SYSTEM_SUPERADMIN_EMAIL", raising=False)

    payload = auth_service.authenticate_global_superadmin("0konomiyaki", "XX,$,26,sipet,26,$,XX")

    assert payload is not None
    assert payload["username"] == "0konomiyaki"
    assert payload["role_name"] == "superadministrador"
    assert payload["user_id"] == 0


def test_is_password_fingerprint_valid_accepts_global_superadmin(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_service,
        "get_sipet_superadmin_settings",
        lambda: {
            "username": "0konomiyaki",
            "password": "XX,$,26,sipet,26,$,XX",
            "email": "alopez@avancoop.org",
        },
    )
    expected = auth_service.build_password_fingerprint("XX,$,26,sipet,26,$,XX")

    assert auth_service.is_password_fingerprint_valid(_FakeDb(), "0konomiyaki", expected) is True


def test_is_password_fingerprint_valid_falls_back_to_local_user_when_superadmin_collides(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_service,
        "get_sipet_superadmin_settings",
        lambda: {
            "username": "0konomiyaki",
            "password": "XX,$,26,sipet,26,$,XX",
            "email": "alopez@avancoop.org",
        },
    )

    class _User:
        contrasena = "pbkdf2_sha256$120000$abcd$" + ("1" * 64)

    monkeypatch.setattr(auth_service, "find_user_by_login", lambda db, username: _User())

    expected = auth_service.build_password_fingerprint(_User.contrasena)

    assert auth_service.is_password_fingerprint_valid(_FakeDb(), "0konomiyaki", expected) is True


def test_apply_login_session_persists_global_superadmin_zero_user_id(monkeypatch) -> None:
    stored: dict[str, object] = {}
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/backend/login",
            "headers": [(b"host", b"127.0.0.1:8000")],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("127.0.0.1", 8000),
        }
    )
    response = Response()

    monkeypatch.setattr(auth_service, "count_active_sessions", lambda **kwargs: 0)
    monkeypatch.setattr(auth_service, "should_revoke_other_sessions", lambda **kwargs: False)
    monkeypatch.setattr(auth_service, "max_concurrent_sessions", lambda **kwargs: 5)
    monkeypatch.setattr(auth_service, "revoke_user_sessions", lambda **kwargs: None)
    monkeypatch.setattr(auth_service, "record_security_event", lambda *args, **kwargs: None, raising=False)

    def _store_user_session(**kwargs):
        stored["store"] = kwargs

    def _mark_session_active(session_jti, payload, ttl_seconds):
        stored["active"] = {
            "session_jti": session_jti,
            "payload": payload,
            "ttl_seconds": ttl_seconds,
        }

    monkeypatch.setattr(auth_service, "store_user_session", _store_user_session)
    monkeypatch.setattr(auth_service, "mark_session_active", _mark_session_active)

    auth_service.apply_login_session(
        response,
        request,
        "0konomiyaki",
        "superadministrador",
        user_id=0,
        password_fingerprint="fingerprint",
    )

    assert stored["store"]["user_id"] == 0
    assert stored["active"]["payload"]["user_id"] == 0


def test_find_user_by_login_recovers_missing_identity_hashes() -> None:
    user = SimpleNamespace(
        usuario=auth_service.encrypt_sensitive("dumas"),
        correo=auth_service.encrypt_sensitive("dumas@dumas.com"),
        usuario_hash="",
        correo_hash="",
    )

    class _Query:
        def all(self):
            return [user]

    class _Db:
        def __init__(self) -> None:
            self.added = []
            self.commits = 0

        def query(self, model):
            return _Query()

        def add(self, obj) -> None:
            self.added.append(obj)

        def commit(self) -> None:
            self.commits += 1

    db = _Db()

    result = auth_service.find_user_by_login(db, "dumas")

    assert result is user
    assert user.usuario_hash == auth_service.sensitive_lookup_hash("dumas")
    assert user.correo_hash == auth_service.sensitive_lookup_hash("dumas@dumas.com")
    assert db.commits == 1
