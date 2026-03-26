from __future__ import annotations

from fastapi_modulo.modulos_sipet.web.servicios import mfa_service


def test_generate_totp_secret_is_base32_without_padding() -> None:
    secret = mfa_service.generate_totp_secret()

    assert secret
    assert "=" not in secret
    assert secret == mfa_service.normalize_totp_secret(secret)


def test_build_totp_otpauth_url_contains_issuer_and_user() -> None:
    url = mfa_service.build_totp_otpauth_url("JBSWY3DPEHPK3PXP", "usuario.demo", "SIPET Demo")

    assert url.startswith("otpauth://totp/")
    assert "secret=JBSWY3DPEHPK3PXP" in url
    assert "issuer=SIPET%20Demo" in url
    assert "SIPET%20Demo%3Ausuario.demo" in url


def test_build_totp_qr_data_url_returns_inline_png() -> None:
    url = mfa_service.build_totp_otpauth_url("JBSWY3DPEHPK3PXP", "usuario.demo", "SIPET")
    data_url = mfa_service.build_totp_qr_data_url(url)

    assert data_url.startswith("data:image/png;base64,")
