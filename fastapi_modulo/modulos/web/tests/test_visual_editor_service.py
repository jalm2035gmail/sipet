from __future__ import annotations

from fastapi_modulo.modulos.web.servicios import visual_editor_service


def test_backend_visual_editor_config_contains_scopes() -> None:
    payload = visual_editor_service.backend_visual_editor_config()
    assert "backend_home" in payload["scopes"]
    assert payload["provider"] in {"", "grapesjs"}
