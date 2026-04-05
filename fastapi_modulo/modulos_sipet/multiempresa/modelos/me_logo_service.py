from __future__ import annotations

import mimetypes
import pathlib
import time
from typing import Optional

UPLOADS_DIR = pathlib.Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_MIME = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"}
_MAX_BYTES = 2 * 1024 * 1024  # 2 MB


def validate(data: bytes, content_type: str) -> None:
    if content_type not in _ALLOWED_MIME:
        raise ValueError(f"Tipo de archivo no soportado: {content_type}")
    if len(data) > _MAX_BYTES:
        raise ValueError("El archivo excede el tamaño máximo de 2 MB")


def build_filename(empresa_id: int, content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type) or ".bin"
    ext = {".jpe": ".jpg", ".jpeg": ".jpg", ".webp": ".webp"}.get(ext, ext)
    ts = int(time.time())
    return f"empresa_{empresa_id}_{ts}{ext}"


def save(filename: str, data: bytes) -> None:
    (UPLOADS_DIR / filename).write_bytes(data)


def remove(filename: str) -> None:
    path = UPLOADS_DIR / filename
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def get_path(filename: str) -> Optional[pathlib.Path]:
    safe = pathlib.Path(filename).name
    path = UPLOADS_DIR / safe
    return path if path.exists() else None
