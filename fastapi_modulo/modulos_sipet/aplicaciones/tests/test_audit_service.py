from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi_modulo.modulos_sipet.aplicaciones.servicios import audit_service


def test_get_protocol_audit_map_uses_cached_protocol_status(monkeypatch) -> None:
    monkeypatch.setattr(
        audit_service,
        "get_cached_payload",
        lambda namespace, identifier: {"crm": {"ok": True, "missing": [], "module_dir": "/tmp/crm"}},
    )
    monkeypatch.setattr(audit_service, "get_latest_registry_audit", lambda module_key, action: None)
    monkeypatch.setattr(audit_service, "scan_protocol_status_map", lambda: (_ for _ in ()).throw(AssertionError("scan should not run")))

    payload = audit_service.get_protocol_audit_map()

    assert payload["crm"]["ok"] is True


def test_get_cached_protocol_status_map_uses_persisted_snapshot(monkeypatch) -> None:
    persisted = {
        "crm": {"ok": True, "missing": [], "module_dir": "/tmp/crm"},
        "rh": {"ok": False, "missing": ["__manifest__.py"], "module_dir": "/tmp/rh"},
    }
    cached_payloads: list[dict] = []
    monkeypatch.setattr(audit_service, "get_cached_payload", lambda namespace, identifier: None)
    monkeypatch.setattr(
        audit_service,
        "get_latest_registry_audit",
        lambda module_key, action: SimpleNamespace(payload_json=json.dumps({"modules": persisted})),
    )
    monkeypatch.setattr(
        audit_service,
        "set_cached_payload",
        lambda namespace, identifier, payload, ttl_seconds: cached_payloads.append(payload),
    )

    payload = audit_service.get_cached_protocol_status_map()

    assert payload == persisted
    assert cached_payloads[0] == persisted
