import io
import logging
from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps, ExifTags

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

PWA_ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fix_orientation(img: Image.Image) -> Image.Image:
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img


def _open(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img = _fix_orientation(img)
    return img


# ── Resize / thumbnail ────────────────────────────────────────────────────────

def resize(
    data: bytes,
    width: int,
    height: int,
    fit: Literal["cover", "contain", "fill"] = "cover",
    fmt: str = "WEBP",
) -> bytes:
    img = _open(data).convert("RGBA" if fmt == "WEBP" else "RGB")

    if fit == "cover":
        img = ImageOps.fit(img, (width, height), method=Image.LANCZOS)
    elif fit == "contain":
        img.thumbnail((width, height), Image.LANCZOS)
    else:
        img = img.resize((width, height), Image.LANCZOS)

    buf = io.BytesIO()
    save_kwargs = {"format": fmt}
    if fmt == "WEBP":
        save_kwargs["quality"] = 85
    elif fmt == "JPEG":
        img = img.convert("RGB")
        save_kwargs["quality"] = 85
        save_kwargs["optimize"] = True
    img.save(buf, **save_kwargs)
    return buf.getvalue()


def thumbnail(data: bytes, size: int = 200) -> bytes:
    return resize(data, size, size, fit="cover", fmt="WEBP")


# ── PWA icons ─────────────────────────────────────────────────────────────────

def generate_pwa_icons(source_bytes: bytes, output_dir: str | Path = "static/icons") -> list[str]:
    """
    Genera todos los iconos PWA estándar a partir de una imagen fuente cuadrada.
    Retorna lista de rutas generadas.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = _open(source_bytes).convert("RGBA")
    paths = []

    for size in PWA_ICON_SIZES:
        icon = ImageOps.fit(img, (size, size), method=Image.LANCZOS)
        path = out / f"icon-{size}x{size}.png"
        icon.save(path, format="PNG", optimize=True)
        paths.append(str(path))
        logger.info("PWA icon generated: %s", path)

    # favicon 32x32
    favicon = ImageOps.fit(img, (32, 32), method=Image.LANCZOS)
    favicon_path = out / "favicon.ico"
    favicon.save(favicon_path, format="ICO", sizes=[(32, 32)])
    paths.append(str(favicon_path))

    return paths


# ── Save / delete ─────────────────────────────────────────────────────────────

def save_upload(data: bytes, filename: str, subfolder: str = "") -> Path:
    dest = MEDIA_DIR / subfolder
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / filename
    path.write_bytes(data)
    logger.info("Media saved: %s", path)
    return path


def delete_file(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
        logger.info("Media deleted: %s", p)


# ── Metadata ──────────────────────────────────────────────────────────────────

def get_image_info(data: bytes) -> dict:
    img = _open(data)
    return {
        "format": img.format,
        "mode": img.mode,
        "width": img.width,
        "height": img.height,
        "size_bytes": len(data),
    }
