from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageEnhance
except Exception:  # pragma: no cover
    Image = None
    ImageEnhance = None


VARIANT_SPECS = {
    "favicon": {"size": (64, 64), "format": "PNG"},
    "login": {"size": (320, 320), "format": "PNG"},
    "sidebar": {"size": (160, 160), "format": "PNG"},
    "light": {"size": (320, 320), "format": "PNG"},
    "dark": {"size": (320, 320), "format": "PNG"},
}


def pillow_enabled() -> bool:
    return Image is not None


def _variant_dir(image_dir: str) -> Path:
    return Path(image_dir).joinpath("generated")


def _target_name(source_name: str, variant: str) -> str:
    stem = Path(source_name).stem or "branding"
    return f"{stem}-{variant}.png"


def _source_path(image_dir: str, filename: str) -> Path:
    return Path(image_dir).joinpath(filename)


def _variant_path(image_dir: str, filename: str, variant: str) -> Path:
    return _variant_dir(image_dir).joinpath(_target_name(filename, variant))


def _needs_regeneration(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    try:
        return target.stat().st_mtime < source.stat().st_mtime
    except OSError:
        return True


def _prepare_image(image: "Image.Image", variant: str) -> "Image.Image":
    prepared = image.convert("RGBA")
    if variant == "light" and ImageEnhance is not None:
        prepared = ImageEnhance.Brightness(prepared).enhance(1.1)
    if variant == "dark" and ImageEnhance is not None:
        prepared = ImageEnhance.Brightness(prepared).enhance(0.72)
    prepared.thumbnail(VARIANT_SPECS[variant]["size"], Image.LANCZOS)
    canvas = Image.new("RGBA", VARIANT_SPECS[variant]["size"], (0, 0, 0, 0))
    offset_x = max(0, (canvas.width - prepared.width) // 2)
    offset_y = max(0, (canvas.height - prepared.height) // 2)
    canvas.paste(prepared, (offset_x, offset_y), prepared)
    return canvas


def ensure_branding_variant(image_dir: str, filename: str, variant: str) -> str:
    source = _source_path(image_dir, filename)
    if not pillow_enabled() or not source.exists() or variant not in VARIANT_SPECS:
        return filename
    target = _variant_path(image_dir, filename, variant)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if _needs_regeneration(source, target):
            with Image.open(source) as image:
                prepared = _prepare_image(image, variant)
                prepared.save(target, VARIANT_SPECS[variant]["format"], optimize=True)
    except Exception:
        return filename
    return str(Path("generated").joinpath(target.name))


def resolve_branding_filename(image_dir: str, filename: Optional[str], fallback_filename: str, variant: str = "") -> str:
    selected = (filename or fallback_filename or "").strip()
    if not selected:
        return fallback_filename
    source = _source_path(image_dir, selected)
    if not source.exists():
        selected = fallback_filename
    if variant:
        return ensure_branding_variant(image_dir, selected, variant)
    return selected
