from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SERVICE_PATH = Path(__file__).resolve().parents[1] / "servicios" / "security_service.py"
SPEC = spec_from_file_location("aplicaciones_security_service_test", SERVICE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_issue_and_verify_sensitive_action_token(monkeypatch) -> None:
    monkeypatch.setattr(MODULE, "_get_user_password_hash", lambda username: "stored-hash")
    monkeypatch.setattr(MODULE, "_verify_password", lambda password, stored_hash: password == "secret123")

    challenge = MODULE.issue_sensitive_action_token(
        username="tester",
        password="secret123",
        action=MODULE.SENSITIVE_ACTION_PACKAGE_UPLOAD,
        module_key="crm",
    )

    assert challenge["token"]
    MODULE.verify_sensitive_action_token(
        token=challenge["token"],
        username="tester",
        action=MODULE.SENSITIVE_ACTION_PACKAGE_UPLOAD,
        module_key="crm",
    )


def test_issue_and_verify_sensitive_action_token_for_rollback(monkeypatch) -> None:
    monkeypatch.setattr(MODULE, "_get_user_password_hash", lambda username: "stored-hash")
    monkeypatch.setattr(MODULE, "_verify_password", lambda password, stored_hash: password == "secret123")

    challenge = MODULE.issue_sensitive_action_token(
        username="tester",
        password="secret123",
        action=MODULE.SENSITIVE_ACTION_PACKAGE_ROLLBACK,
        module_key="crm",
    )

    MODULE.verify_sensitive_action_token(
        token=challenge["token"],
        username="tester",
        action=MODULE.SENSITIVE_ACTION_PACKAGE_ROLLBACK,
        module_key="crm",
    )
