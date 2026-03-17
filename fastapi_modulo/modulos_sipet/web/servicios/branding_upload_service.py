from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile

from fastapi_modulo.modulos_sipet.web.servicios.branding_image_service import Image, ensure_branding_variant, pillow_enabled

BRANDING_MAX_UPLOAD_BYTES = int((os.environ.get("WEB_BRANDING_MAX_UPLOAD_BYTES") or str(4 * 1024 * 1024)).strip() or str(4 * 1024 * 1024))
BRANDING_ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/x-icon",
    "image/vnd.microsoft.icon",
}
SLOT_VARIANTS = {
    "logo": ("login", "sidebar", "light", "dark", "favicon"),
    "favicon": ("favicon",),
    "desktop_bg": (),
    "mobile_bg": (),
    "report_signature": (),
}
SLOT_OUTPUT_FORMAT = {
    "logo": ("PNG", ".png"),
    "favicon": ("PNG", ".png"),
    "desktop_bg": ("JPEG", ".jpg"),
    "mobile_bg": ("JPEG", ".jpg"),
    "report_signature": ("PNG", ".png"),
}


def sanitize_upload_filename(filename: str, slot: str) -> str:
    suffix = SLOT_OUTPUT_FORMAT.get(slot, ("PNG", ".png"))[1]
    stem = re.sub(r"[^a-z0-9]+", "-", f"branding-{slot}-{uuid.uuid4().hex[:10]}".lower()).strip("-")
    return f"{stem}{suffix}"


def _validate_content_type(upload: UploadFile) -> None:
    content_type = str(upload.content_type or "").strip().lower()
    if content_type not in BRANDING_ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo MIME no permitido")


def _read_limited_bytes(file_obj: BinaryIO, max_bytes: int) -> bytes:
    data = file_obj.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    return data


def _validate_slot(slot: str) -> None:
    if slot not in SLOT_VARIANTS:
        raise HTTPException(status_code=400, detail="Tipo de branding no soportado")


def _delete_old_variants(image_dir: str, filename: str) -> None:
    if not filename:
        return
    generated_dir = Path(image_dir).joinpath("generated")
    stem = Path(filename).stem
    if not generated_dir.exists():
        return
    for item in generated_dir.iterdir():
        if item.is_file() and item.name.startswith(f"{stem}-"):
            try:
                item.unlink()
            except OSError:
                continue


def _normalize_image(raw_bytes: bytes, slot: str):
    if not pillow_enabled() or Image is None:
        raise HTTPException(status_code=500, detail="Pillow es requerido para procesar branding")
    try:
        from io import BytesIO

        with Image.open(BytesIO(raw_bytes)) as image:
            prepared = image.convert("RGBA" if slot in {"logo", "favicon", "report_signature"} else "RGB")
            target_format, _target_suffix = SLOT_OUTPUT_FORMAT.get(slot, ("PNG", ".png"))
            if slot in {"desktop_bg", "mobile_bg"}:
                if prepared.width < 640 or prepared.height < 360:
                    raise HTTPException(status_code=400, detail="La imagen de fondo es demasiado pequena")
            else:
                prepared.thumbnail((1024, 1024), Image.LANCZOS)
            output = BytesIO()
            save_kwargs = {"optimize": True}
            if target_format == "JPEG":
                background = Image.new("RGB", prepared.size, (255, 255, 255))
                if prepared.mode == "RGBA":
                    background.paste(prepared, mask=prepared.getchannel("A"))
                else:
                    background.paste(prepared)
                background.save(output, target_format, quality=90, **save_kwargs)
            else:
                prepared.save(output, target_format, **save_kwargs)
            output.seek(0)
            return output.read()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Archivo de imagen invalido") from exc


async def save_branding_upload(
    upload: UploadFile,
    *,
    slot: str,
    image_dir: str,
    previous_filename: str = "",
) -> dict[str, str]:
    _validate_slot(slot)
    _validate_content_type(upload)
    if upload.file is None:
        raise HTTPException(status_code=400, detail="Archivo no recibido")
    upload.file.seek(0)
    raw_bytes = _read_limited_bytes(upload.file, BRANDING_MAX_UPLOAD_BYTES)
    normalized_bytes = _normalize_image(raw_bytes, slot)
    filename = sanitize_upload_filename(upload.filename or "", slot)
    target_path = Path(image_dir).joinpath(filename)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(normalized_bytes)
    _delete_old_variants(image_dir, previous_filename)
    if previous_filename:
        previous_path = Path(image_dir).joinpath(previous_filename)
        if previous_path.exists():
            try:
                previous_path.unlink()
            except OSError:
                pass
    for variant in SLOT_VARIANTS.get(slot, ()):
        ensure_branding_variant(image_dir, filename, variant)
    return {"filename": filename, "slot": slot}
