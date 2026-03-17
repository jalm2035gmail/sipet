from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos_sipet.web.servicios import branding_image_service


def test_resolve_branding_filename_falls_back_without_pillow(tmp_path: Path, monkeypatch) -> None:
    image_dir = tmp_path / "imagenes"
    image_dir.mkdir()
    (image_dir / "logo.png").write_bytes(b"not-an-image")
    monkeypatch.setattr(branding_image_service, "Image", None)
    resolved = branding_image_service.resolve_branding_filename(str(image_dir), "logo.png", "logo.png", "favicon")
    assert resolved == "logo.png"
