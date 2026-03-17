from __future__ import annotations

from types import SimpleNamespace

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
    assert auth_service.PASSWORD_CONTEXT.identify(user.contrasena) in {"bcrypt_sha256", "pbkdf2_sha256"}
    assert db.commits == 1


def test_validate_password_strength_rejects_weak_password() -> None:
    ok, errors = auth_service.validate_password_strength("demo")
    assert ok is False
    assert "common_password" not in errors or isinstance(errors, list)
    assert any(error.startswith("min_length") for error in errors)
