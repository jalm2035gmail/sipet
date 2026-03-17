from __future__ import annotations

import io
import os
import re
import secrets
from pathlib import Path
from typing import Any

from fastapi import HTTPException

try:
    from PIL import Image, ImageOps
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]

MEDIA_STORAGE_ROOT = Path(
    os.environ.get("MODULE_BASE_MEDIA_ROOT")
    or (Path(__file__).resolve().parents[1] / "static" / "media")
).resolve()

IMAGE_PROFILE_SIZES = {
    "logo": (512, 512),
    "favicon": (64, 64),
    "thumbnail": (320, 320),
    "preview": (1280, 720),
}

ALLOWED_IMAGE_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "ICO": ".ico",
}


def ensure_media_storage_dir(category: str) -> Path:
    target = (MEDIA_STORAGE_ROOT / sanitize_media_name(category)).resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target


def sanitize_media_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return normalized or "asset"


def build_media_filename(prefix: str, original_name: str, ext: str = "") -> str:
    safe_prefix = sanitize_media_name(prefix)
    original_ext = Path(str(original_name or "").strip()).suffix.lower()
    safe_ext = (ext or original_ext or ".bin").lower()
    return f"{safe_prefix}_{secrets.token_hex(8)}{safe_ext}"


def validate_image_payload(contents: bytes, filename: str = "") -> dict[str, Any]:
    if not contents:
        raise HTTPException(status_code=400, detail="La imagen esta vacia.")
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La imagen supera el tamano maximo permitido.")
    if Image is None:
        raise HTTPException(status_code=500, detail="Pillow no esta disponible.")
    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.verify()
        with Image.open(io.BytesIO(contents)) as image:
            image.load()
            image_format = str(image.format or "").upper()
            width, height = image.size
    except Exception as exc:
        raise HTTPException(status_code=400, detail="La imagen no es valida.") from exc
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado.")
    return {
        "filename": str(filename or "").strip(),
        "format": image_format,
        "width": width,
        "height": height,
        "size_bytes": len(contents),
        "extension": ALLOWED_IMAGE_FORMATS[image_format],
    }


def normalize_image(
    contents: bytes,
    *,
    profile: str = "logo",
    output_format: str = "PNG",
    background: str = "#FFFFFF",
) -> tuple[bytes, dict[str, Any]]:
    metadata = validate_image_payload(contents)
    if Image is None or ImageOps is None:
        raise HTTPException(status_code=500, detail="Pillow no esta disponible.")
    target_size = IMAGE_PROFILE_SIZES.get(profile, IMAGE_PROFILE_SIZES["logo"])
    with Image.open(io.BytesIO(contents)) as image:
        processed = ImageOps.exif_transpose(image)
        if output_format.upper() in {"PNG", "ICO"}:
            processed = processed.convert("RGBA")
        else:
            processed = processed.convert("RGB")
        fitted = ImageOps.contain(processed, target_size)
        canvas_mode = "RGBA" if output_format.upper() in {"PNG", "ICO"} else "RGB"
        canvas_color = (255, 255, 255, 0) if canvas_mode == "RGBA" else background
        canvas = Image.new(canvas_mode, target_size, canvas_color)
        offset = ((target_size[0] - fitted.width) // 2, (target_size[1] - fitted.height) // 2)
        canvas.paste(fitted, offset, fitted if fitted.mode == "RGBA" and canvas_mode == "RGBA" else None)
        output = io.BytesIO()
        save_kwargs: dict[str, Any] = {"format": output_format.upper()}
        if output_format.upper() == "JPEG":
            save_kwargs["quality"] = 90
            save_kwargs["optimize"] = True
        canvas.save(output, **save_kwargs)
    return output.getvalue(), {
        **metadata,
        "profile": profile,
        "output_format": output_format.upper(),
        "output_extension": ALLOWED_IMAGE_FORMATS.get(output_format.upper(), ".png"),
        "target_width": target_size[0],
        "target_height": target_size[1],
    }


def create_thumbnail(contents: bytes, *, size: tuple[int, int] = (320, 320)) -> tuple[bytes, dict[str, Any]]:
    metadata = validate_image_payload(contents)
    if Image is None or ImageOps is None:
        raise HTTPException(status_code=500, detail="Pillow no esta disponible.")
    with Image.open(io.BytesIO(contents)) as image:
        processed = ImageOps.exif_transpose(image).convert("RGB")
        processed.thumbnail(size)
        output = io.BytesIO()
        processed.save(output, format="JPEG", quality=88, optimize=True)
    return output.getvalue(), {
        **metadata,
        "profile": "thumbnail",
        "output_format": "JPEG",
        "output_extension": ".jpg",
        "target_width": processed.width,
        "target_height": processed.height,
    }


def store_media(contents: bytes, *, category: str, filename: str) -> dict[str, Any]:
    directory = ensure_media_storage_dir(category)
    safe_name = build_media_filename(category, filename)
    target = (directory / safe_name).resolve()
    target.write_bytes(contents)
    return {
        "filename": safe_name,
        "path": str(target),
        "category": sanitize_media_name(category),
        "size_bytes": len(contents),
    }


def process_and_store_media(
    contents: bytes,
    *,
    category: str,
    original_name: str,
    profile: str = "logo",
    output_format: str = "PNG",
) -> dict[str, Any]:
    processed, metadata = normalize_image(contents, profile=profile, output_format=output_format)
    stored = store_media(
        processed,
        category=category,
        filename=build_media_filename(category, original_name, metadata["output_extension"]),
    )
    return {**stored, **metadata}


__all__ = [
    "ALLOWED_IMAGE_FORMATS",
    "IMAGE_PROFILE_SIZES",
    "MEDIA_STORAGE_ROOT",
    "build_media_filename",
    "create_thumbnail",
    "ensure_media_storage_dir",
    "normalize_image",
    "process_and_store_media",
    "sanitize_media_name",
    "store_media",
    "validate_image_payload",
]
