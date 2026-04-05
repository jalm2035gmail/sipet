"""
tests/test_gallery_controller.py
─────────────────────────────────────────────────────────────────────────────
Pruebas HTTP del gallery_controller usando TestClient.

Usa el fixture gallery_app de conftest.py que:
  • Parchea _GALLERY_DIR a un directorio temporal.
  • Sustituye cache_service con stubs no-op.
  • Registra el router en una FastAPI de prueba.
  • Parchea require_write para aceptar toda solicitud.

Cubre:
  • GET  /api/frontend/gallery  → lista vacía y con ficheros
  • POST /api/frontend/gallery/upload  → upload exitoso, tipo inválido, tamaño excedido
  • DELETE /api/frontend/gallery/{filename}  → eliminación OK y not-found
  • Path traversal en DELETE → 400
"""

from __future__ import annotations

import io
import os
import uuid


# ── GET /api/frontend/gallery ─────────────────────────────────────────────────

def test_gallery_list_empty(gallery_app):
    resp = gallery_app.get("/api/frontend/gallery")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


def test_gallery_list_shows_uploaded_file(gallery_app, patched_store, tmp_path, monkeypatch):
    import fastapi_modulo.modulos_sipet.frontend.controladores.gallery_controller as gc
    gallery_dir = gc._GALLERY_DIR

    # Place a file directly on disk (legacy, no DB record)
    img_path = os.path.join(gallery_dir, "legacy.webp")
    with open(img_path, "wb") as fh:
        fh.write(b"RIFF....WEBPVP8 ")

    resp = gallery_app.get("/api/frontend/gallery")
    assert resp.status_code == 200
    filenames = [item["filename"] for item in resp.json()["data"]]
    assert "legacy.webp" in filenames


# ── POST /api/frontend/gallery/upload ────────────────────────────────────────

def test_gallery_upload_valid_image(gallery_app):
    # Minimal 1×1 PNG (valid but tiny)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    resp = gallery_app.post(
        "/api/frontend/gallery/upload",
        files={"file": ("photo.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "filename" in body
    assert "url" in body
    assert "status" in body


def test_gallery_upload_rejected_extension(gallery_app):
    resp = gallery_app.post(
        "/api/frontend/gallery/upload",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert resp.status_code == 415
    assert resp.json()["success"] is False


def test_gallery_upload_rejected_size_exceeded(gallery_app, monkeypatch):
    import fastapi_modulo.modulos_sipet.frontend.controladores.gallery_controller as gc
    monkeypatch.setattr(gc, "_GALLERY_MAX_MB", 0)   # 0 MB limit → any upload fails

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
    resp = gallery_app.post(
        "/api/frontend/gallery/upload",
        files={"file": ("tiny.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert resp.status_code == 413
    assert resp.json()["success"] is False


def test_gallery_upload_no_file(gallery_app):
    resp = gallery_app.post("/api/frontend/gallery/upload")
    assert resp.status_code == 400
    assert resp.json()["success"] is False


# ── DELETE /api/frontend/gallery/{filename} ────────────────────────────────────

def test_gallery_delete_existing_file(gallery_app):
    import fastapi_modulo.modulos_sipet.frontend.controladores.gallery_controller as gc
    gallery_dir = gc._GALLERY_DIR

    fname   = f"{uuid.uuid4().hex}.webp"
    fpath   = os.path.join(gallery_dir, fname)
    with open(fpath, "wb") as fh:
        fh.write(b"fake webp")

    resp = gallery_app.delete(f"/api/frontend/gallery/{fname}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert not os.path.exists(fpath)


def test_gallery_delete_nonexistent_returns_success(gallery_app):
    """Eliminar un filename que no existe en disco devuelve success=True, deleted=False."""
    resp = gallery_app.delete("/api/frontend/gallery/ghost.webp")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"]  is True
    assert body["deleted"]  is False


def test_gallery_delete_path_traversal_rejected(gallery_app):
    resp = gallery_app.delete("/api/frontend/gallery/..%2Fother.webp")
    # Either 400 (caught) or 200 success=False — must not delete outside gallery
    assert resp.status_code in (400, 200)
    if resp.status_code == 200:
        assert resp.json()["success"] is False or resp.json().get("deleted") is False


def test_gallery_delete_double_dot_rejected(gallery_app):
    resp = gallery_app.delete("/api/frontend/gallery/../etc/passwd")
    assert resp.status_code == 400
    assert resp.json()["success"] is False
