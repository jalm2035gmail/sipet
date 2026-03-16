from __future__ import annotations

from fastapi_modulo.modulos.web.servicios import security_policy_service


def test_mfa_policy_by_role_and_tenant(monkeypatch) -> None:
    monkeypatch.setenv(
        "WEB_MFA_POLICY_JSON",
        '{"roles":{"autoridades":true},"tenants":{"tenant-a":true},"users":{"jane":true}}',
    )
    assert security_policy_service.is_mfa_required(role_name="autoridades") is True
    assert security_policy_service.is_mfa_required(role_name="usuario", tenant_id="tenant-a") is True
    assert security_policy_service.is_mfa_required(role_name="usuario", username="jane") is True
    assert security_policy_service.is_mfa_required(role_name="usuario", username="john") is False


def test_session_policy_limits(monkeypatch) -> None:
    monkeypatch.setenv(
        "WEB_SESSION_POLICY_JSON",
        '{"mode":"allow_multiple","max_sessions":3,"role_single_session":{"autoridades":true},"role_max_sessions":{"usuario":2}}',
    )
    assert security_policy_service.should_revoke_other_sessions(role_name="autoridades") is True
    assert security_policy_service.should_revoke_other_sessions(role_name="usuario") is False
    assert security_policy_service.max_concurrent_sessions(role_name="usuario") == 2
