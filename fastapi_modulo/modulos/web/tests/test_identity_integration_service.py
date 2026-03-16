from __future__ import annotations

from fastapi_modulo.modulos.web.servicios import identity_integration_service


def test_merge_remote_branding_overrides_allowed_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        identity_integration_service,
        "fetch_remote_branding",
        lambda **_: {"branding": {"login_message": "Remoto", "login_company_short_name": "EXT", "ignored": "x"}},
    )
    merged = identity_integration_service.merge_remote_branding(
        {"login_message": "Local", "login_company_short_name": "LOC", "menu_position": "arriba"},
        host="example.com",
        tenant_id="default",
    )
    assert merged["login_message"] == "Remoto"
    assert merged["login_company_short_name"] == "EXT"
    assert "ignored" not in merged


def test_export_remote_config_snapshot_returns_json(monkeypatch) -> None:
    monkeypatch.setattr(identity_integration_service, "fetch_remote_branding", lambda **_: {"branding": {"login_message": "ok"}})
    monkeypatch.setattr(identity_integration_service, "fetch_remote_catalog", lambda **_: {"items": [1, 2]})
    snapshot = identity_integration_service.export_remote_config_snapshot(host="example.com", tenant_id="default")
    assert "\"branding\"" in snapshot
    assert "\"catalogs\"" in snapshot
