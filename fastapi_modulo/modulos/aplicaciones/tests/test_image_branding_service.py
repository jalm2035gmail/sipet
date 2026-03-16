from __future__ import annotations

import io
from pathlib import Path

from fastapi_modulo.modulos.aplicaciones.servicios import image_branding_service

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def test_build_module_image_response_falls_back_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(image_branding_service, "get_module_image_path", lambda module_key: None)

    response = image_branding_service.build_module_image_response("crm", "preview.png", label="CRM", variant="card")

    assert response.media_type == "image/png"
    assert response.body


def test_build_module_image_response_generates_thumbnail(monkeypatch, tmp_path: Path) -> None:
    if Image is None:
        return
    image_path = tmp_path / "crm.png"
    image = Image.new("RGB", (640, 480), (12, 120, 200))
    image.save(image_path, format="PNG")
    monkeypatch.setattr(image_branding_service, "get_module_image_path", lambda module_key: str(image_path))

    response = image_branding_service.build_module_image_response("crm", "crm.png", label="CRM", variant="card")

    assert response.media_type == "image/png"
    with Image.open(io.BytesIO(response.body)) as thumb:
        assert thumb.width <= 160
        assert thumb.height <= 160
