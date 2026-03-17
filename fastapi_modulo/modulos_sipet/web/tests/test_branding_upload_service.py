from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

from fastapi_modulo.modulos_sipet.web.servicios import branding_upload_service


def _upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(payload), headers={"content-type": content_type})


def _png_bytes() -> bytes:
    if branding_upload_service.Image is None:
        return b""
    image = branding_upload_service.Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_save_branding_upload_rejects_invalid_mime(tmp_path: Path) -> None:
    upload = _upload("logo.txt", "text/plain", b"demo")
    with pytest.raises(HTTPException):
        asyncio.run(branding_upload_service.save_branding_upload(upload, slot="logo", image_dir=str(tmp_path)))


def test_save_branding_upload_rejects_large_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(branding_upload_service, "BRANDING_MAX_UPLOAD_BYTES", 4)
    upload = _upload("logo.png", "image/png", b"12345")
    with pytest.raises(HTTPException):
        asyncio.run(branding_upload_service.save_branding_upload(upload, slot="logo", image_dir=str(tmp_path)))


def test_save_branding_upload_normalizes_and_renames(tmp_path: Path) -> None:
    if branding_upload_service.Image is None:
        pytest.skip("Pillow no disponible")
    upload = _upload("Mi Logo.png", "image/png", _png_bytes())
    payload = asyncio.run(branding_upload_service.save_branding_upload(upload, slot="logo", image_dir=str(tmp_path)))
    saved_path = tmp_path / payload["filename"]
    assert saved_path.exists()
    assert payload["filename"].startswith("branding-logo-")
    assert (tmp_path / "generated").exists()
