from __future__ import annotations

import hashlib
import io
import os
from typing import Any

from fastapi import HTTPException
from fastapi.responses import Response

from fastapi_modulo.image_utils import image_info
from fastapi_modulo.modulos.aplicaciones.repositorios.package_repository import get_module_image_path

try:
    from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
except ImportError:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None
    UnidentifiedImageError = Exception


PREVIEW_SIZES = {
    "card": (160, 160),
    "detail": (320, 320),
    "full": (800, 800),
}


def _variant_size(variant: str) -> tuple[int, int]:
    return PREVIEW_SIZES.get(str(variant or "").strip().lower(), PREVIEW_SIZES["card"])


def _guess_media_type(path: str) -> str:
    ext = os.path.splitext(str(path or "").strip().lower())[1]
    return {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".ico": "image/x-icon",
    }.get(ext, "application/octet-stream")


def _fallback_colors(seed: str) -> tuple[str, str]:
    digest = hashlib.sha256(str(seed or "").encode("utf-8")).hexdigest()
    start = "#" + digest[:6]
    end = "#" + digest[6:12]
    return start, end


def _hex_rgb(value: str) -> tuple[int, int, int]:
    raw = str(value or "").strip().lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _font(size: int):
    if ImageFont is None:
        return None
    for font_path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _build_fallback_preview(module_key: str, label: str, variant: str = "card") -> bytes:
    width, height = _variant_size(variant)
    if Image is None or ImageDraw is None:
        raise HTTPException(status_code=500, detail="Pillow no esta disponible para generar previews.")

    start, end = _fallback_colors(module_key or label)
    image = Image.new("RGB", (width, height), _hex_rgb(start))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(_hex_rgb(start)[index] * (1 - ratio) + _hex_rgb(end)[index] * ratio)
            for index in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)

    initials = "".join(part[:1] for part in str(label or module_key or "App").split()[:2]).upper() or "A"
    font = _font(max(24, width // 3))
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((width - text_w) / 2, (height - text_h) / 2 - 4),
        initials,
        fill=(255, 255, 255),
        font=font,
    )

    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _render_thumbnail(path: str, variant: str) -> bytes:
    if Image is None:
        with open(path, "rb") as handle:
            return handle.read()
    width, height = _variant_size(variant)
    try:
        with Image.open(path) as image:
            image.load()
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "A" in image.mode else "RGB")
            else:
                image = image.copy()
            image.thumbnail((width, height), Image.LANCZOS)
            canvas = Image.new("RGBA", (width, height), (245, 247, 250, 0))
            offset = ((width - image.width) // 2, (height - image.height) // 2)
            canvas.paste(image, offset, image if image.mode == "RGBA" else None)
            out = io.BytesIO()
            canvas.save(out, format="PNG")
            return out.getvalue()
    except (OSError, UnidentifiedImageError) as exc:
        raise HTTPException(status_code=400, detail="La imagen del modulo no es valida.") from exc


def build_module_image_response(module_key: str, filename: str, *, label: str = "", variant: str = "card") -> Response:
    image_path = get_module_image_path(str(module_key or "").strip())
    requested_name = str(filename or "").strip()
    if not image_path:
        return Response(content=_build_fallback_preview(module_key, label or module_key, variant), media_type="image/png")

    basename = os.path.basename(image_path)
    if requested_name not in {basename, "preview.png"}:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    media_type = _guess_media_type(image_path)
    if media_type == "image/svg+xml" and requested_name != "preview.png":
        with open(image_path, "rb") as handle:
            return Response(content=handle.read(), media_type=media_type)

    with open(image_path, "rb") as handle:
        raw = handle.read()
    metadata = image_info(raw)
    if not int(metadata.get("width") or 0) or not int(metadata.get("height") or 0):
        return Response(content=_build_fallback_preview(module_key, label or module_key, variant), media_type="image/png")
    return Response(content=_render_thumbnail(image_path, variant), media_type="image/png")


def get_module_catalog_image_url(module_key: str) -> str:
    image_path = get_module_image_path(str(module_key or "").strip())
    filename = os.path.basename(image_path) if image_path else "preview.png"
    return f"/api/aplicaciones/assets/{str(module_key or '').strip()}/{filename}?variant=card"


__all__ = ["build_module_image_response", "get_module_catalog_image_url"]
