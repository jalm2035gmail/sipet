"""
Servicio de procesamiento de assets visuales con Pillow.

Centraliza toda la lógica de validación, redimensionado y conversión
de imágenes subidas al módulo de personalización.

Responsabilidades:
  - Verificar que el archivo sea una imagen real (no un ejecutable renombrado)
  - Rechazar extensiones no permitidas por tipo de asset
  - Rechazar archivos que superen el tamaño máximo (5 MB por defecto)
  - Redimensionar si supera el tamaño recomendado para el asset
  - Convertir a WebP para optimizar peso (excepto favicon y SVG)
  - Devolver bytes listos para escribir a disco

SVGs se tratan como texto — Pillow no los procesa, pasan directo.
Favicons se mantienen en PNG (no WebP) para máxima compatibilidad.

Variables de entorno:
  WEB_ASSET_MAX_MB        Tamaño máximo en MB (default: 5)
  WEB_ASSET_WEBP_QUALITY  Calidad WebP 1-95 (default: 85)
"""
from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, UnidentifiedImageError
    _PILLOW_AVAILABLE = True
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    UnidentifiedImageError = Exception  # type: ignore[assignment,misc]
    _PILLOW_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
_MAX_FILE_BYTES = int(
    (os.environ.get("WEB_ASSET_MAX_MB") or "5").strip() or "5"
) * 1024 * 1024

_WEBP_QUALITY = int(
    (os.environ.get("WEB_ASSET_WEBP_QUALITY") or "85").strip() or "85"
)

# Extensiones permitidas por tipo de asset
ALLOWED_EXTENSIONS: dict[str, frozenset[str]] = {
    "favicon":      frozenset({".png", ".ico", ".svg"}),
    "logo_empresa": frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"}),
    "logo_usuario": frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"}),
    "svg_fondo":    frozenset({".svg"}),
    "svg_defecto":  frozenset({".svg"}),
}

# Dimensiones máximas recomendadas por asset (ancho, alto) — 0 = sin límite
ASSET_MAX_SIZES: dict[str, tuple[int, int]] = {
    "favicon":      (64,   64),
    "logo_empresa": (800,  400),
    "logo_usuario": (400,  400),
    "svg_fondo":    (0,    0),
    "svg_defecto":  (0,    0),
}

# Assets que deben mantenerse en PNG (no convertir a WebP)
_PNG_ONLY_ASSETS = frozenset({"favicon"})

# Formatos de imagen Pillow considerados válidos para subir
_ALLOWED_PIL_FORMATS = frozenset({
    "PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF", "ICO",
})


# ── Dataclass de resultado ────────────────────────────────────────────────────

@dataclass
class ProcessedAsset:
    """Resultado del procesamiento de un asset."""
    data:            bytes
    extension:       str          # extensión final ej. ".webp", ".png", ".svg"
    width:           int          # ancho en px (0 para SVG)
    height:          int          # alto en px (0 para SVG)
    original_format: str          # formato original detectado por Pillow
    size_bytes:      int          # tamaño final en bytes
    was_resized:     bool = False
    was_converted:   bool = False

    def to_info_dict(self) -> dict:
        """Serializable para incluir en el response JSON."""
        return {
            "extension":       self.extension,
            "width":           self.width,
            "height":          self.height,
            "original_format": self.original_format,
            "size_bytes":      self.size_bytes,
            "was_resized":     self.was_resized,
            "was_converted":   self.was_converted,
        }


class AssetValidationError(ValueError):
    """El archivo no pasó la validación de asset."""


# ── Funciones de validación ───────────────────────────────────────────────────

def pillow_available() -> bool:
    """True si Pillow está instalado y operativo."""
    return _PILLOW_AVAILABLE


def validate_extension(filename: str, asset_field: str) -> str:
    """
    Valida y devuelve la extensión del archivo para el asset dado.

    Returns:
        Extensión limpia en minúsculas con punto (ej. '.png').

    Raises:
        AssetValidationError: Si la extensión no está permitida.
    """
    ext = Path(filename or "").suffix.lower().strip()
    if not ext:
        raise AssetValidationError(
            f"El archivo '{filename}' no tiene extensión."
        )
    allowed = ALLOWED_EXTENSIONS.get(asset_field, frozenset())
    if allowed and ext not in allowed:
        raise AssetValidationError(
            f"Extensión '{ext}' no permitida para '{asset_field}'. "
            f"Formatos aceptados: {', '.join(sorted(allowed))}."
        )
    return ext


def validate_file_size(raw: bytes, filename: str = "") -> None:
    """
    Verifica que el archivo no supere el tamaño máximo configurado.

    Raises:
        AssetValidationError: Si el archivo es demasiado grande.
    """
    if len(raw) > _MAX_FILE_BYTES:
        mb = _MAX_FILE_BYTES // (1024 * 1024)
        actual = len(raw) / (1024 * 1024)
        raise AssetValidationError(
            f"El archivo '{filename}' supera el límite de {mb} MB "
            f"({actual:.1f} MB recibido)."
        )


# ── Procesamiento principal ───────────────────────────────────────────────────

def process_asset(
    raw: bytes,
    extension: str,
    asset_field: str,
    *,
    force_webp: bool = True,
    webp_quality: Optional[int] = None,
) -> ProcessedAsset:
    """
    Procesa un asset: valida que sea imagen real, redimensiona si es necesario
    y convierte al formato óptimo.

    Args:
        raw:          Bytes crudos del archivo subido.
        extension:    Extensión validada (ej. '.png', '.svg').
        asset_field:  Clave del asset para determinar restricciones.
        force_webp:   Convertir a WebP cuando sea posible (default: True).
        webp_quality: Calidad WebP 1-95. None usa WEB_ASSET_WEBP_QUALITY.

    Returns:
        ProcessedAsset con bytes finales y metadatos.

    Raises:
        AssetValidationError: Si el archivo no es una imagen válida.
    """
    quality = webp_quality if webp_quality is not None else _WEBP_QUALITY

    # ── SVG: pasar directo, Pillow no los procesa ─────────────────────────────
    if extension == ".svg":
        return ProcessedAsset(
            data=raw, extension=".svg",
            width=0, height=0,
            original_format="SVG",
            size_bytes=len(raw),
        )

    # ── Sin Pillow: guardar crudo con advertencia ─────────────────────────────
    if not _PILLOW_AVAILABLE:
        logger.warning(
            "asset_processor_service: Pillow no disponible, "
            "guardando '%s' sin validación ni optimización.", asset_field,
        )
        return ProcessedAsset(
            data=raw, extension=extension,
            width=0, height=0,
            original_format="UNKNOWN",
            size_bytes=len(raw),
        )

    # ── Verificar que sea imagen real ─────────────────────────────────────────
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()
        img = Image.open(io.BytesIO(raw))  # re-abrir tras verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise AssetValidationError(
            f"El archivo no es una imagen válida: {exc}"
        ) from exc

    original_format = (img.format or "PNG").upper()
    if original_format not in _ALLOWED_PIL_FORMATS:
        raise AssetValidationError(
            f"Formato de imagen '{original_format}' no permitido. "
            f"Usa: {', '.join(sorted(_ALLOWED_PIL_FORMATS))}."
        )

    # ── Normalizar modo de color ──────────────────────────────────────────────
    if img.mode not in ("RGB", "RGBA", "L", "P"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")

    original_w, original_h = img.width, img.height
    was_resized = False

    # ── Redimensionar si supera el máximo del asset ───────────────────────────
    max_w, max_h = ASSET_MAX_SIZES.get(asset_field, (1920, 1920))
    if max_w > 0 and max_h > 0 and (img.width > max_w or img.height > max_h):
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        was_resized = True
        logger.debug(
            "asset_processor_service: '%s' redimensionado %dx%d → %dx%d",
            asset_field, original_w, original_h, img.width, img.height,
        )

    # ── Elegir formato de salida ──────────────────────────────────────────────
    was_converted = False
    save_kwargs: dict = {}

    if asset_field in _PNG_ONLY_ASSETS:
        # Favicon: siempre PNG para compatibilidad máxima con browsers
        out_format = "PNG"
        out_ext = ".png"
        save_kwargs = {"optimize": True}
        was_converted = original_format != "PNG"

    elif force_webp and original_format not in ("ICO",):
        # Resto de assets: WebP para mejor compresión
        out_format = "WEBP"
        out_ext = ".webp"
        save_kwargs = {"quality": quality, "method": 4}
        if img.mode in ("P", "L"):
            img = img.convert("RGBA")
        was_converted = original_format != "WEBP"

    elif original_format == "JPEG":
        out_format = "JPEG"
        out_ext = ".jpg"
        save_kwargs = {"quality": quality, "optimize": True}
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

    else:
        out_format = "PNG"
        out_ext = ".png"
        save_kwargs = {"optimize": True}

    # ── Serializar ────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format=out_format, **save_kwargs)
    buf.seek(0)
    final_bytes = buf.read()

    logger.debug(
        "asset_processor_service: '%s' procesado — "
        "formato=%s ext=%s size=%d bytes %dx%d resized=%s converted=%s",
        asset_field, out_format, out_ext, len(final_bytes),
        img.width, img.height, was_resized, was_converted,
    )

    return ProcessedAsset(
        data=final_bytes,
        extension=out_ext,
        width=img.width,
        height=img.height,
        original_format=original_format,
        size_bytes=len(final_bytes),
        was_resized=was_resized,
        was_converted=was_converted,
    )


# ── Pipeline completo para UploadFile ─────────────────────────────────────────

async def process_upload(
    file_obj,
    asset_field: str,
    *,
    force_webp: bool = True,
) -> Optional[ProcessedAsset]:
    """
    Pipeline completo para un UploadFile de FastAPI:
      1. Validar que el upload no esté vacío
      2. Validar extensión permitida para el asset
      3. Leer bytes
      4. Validar tamaño máximo
      5. Procesar con Pillow (validar, redimensionar, convertir)

    Args:
        file_obj:    UploadFile de FastAPI.
        asset_field: Clave del asset (ej. 'favicon', 'logo_empresa').
        force_webp:  Convertir a WebP cuando sea posible.

    Returns:
        ProcessedAsset si el archivo es válido, None si el upload está vacío.

    Raises:
        AssetValidationError: Si el archivo no pasa alguna validación.
    """
    if not file_obj or not (getattr(file_obj, "filename", None) or "").strip():
        return None

    filename = file_obj.filename
    ext = validate_extension(filename, asset_field)
    raw = await file_obj.read()

    if not raw:
        return None

    validate_file_size(raw, filename)
    return process_asset(raw, ext, asset_field, force_webp=force_webp)


# ── Utilidades adicionales ────────────────────────────────────────────────────

def generate_favicon_pack(raw: bytes) -> dict[str, bytes]:
    """
    Genera versiones del favicon en 16x16, 32x32 y 64x64 como PNG.
    Útil para servir el tamaño correcto según el contexto
    (pestaña del browser, acceso directo a pantalla de inicio, etc.).

    Args:
        raw: Bytes de la imagen del favicon (ya validada con process_asset).

    Returns:
        dict con claves '16', '32', '64' y bytes PNG. Devuelve {} sin Pillow.
    """
    if not _PILLOW_AVAILABLE:
        return {}
    result: dict[str, bytes] = {}
    for size in (16, 32, 64):
        try:
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            buf.seek(0)
            result[str(size)] = buf.read()
        except Exception as exc:
            logger.warning(
                "asset_processor_service: error generando favicon %dx%d — %s",
                size, size, exc,
            )
    return result


def get_image_info(raw: bytes) -> dict[str, object]:
    """
    Devuelve metadatos básicos de una imagen sin procesarla.
    Útil para mostrar información del asset actual en el panel de personalización.

    Returns:
        dict con format, width, height, mode, size_bytes.
        Devuelve solo size_bytes si Pillow no está disponible.
    """
    info: dict[str, object] = {"size_bytes": len(raw)}
    if not _PILLOW_AVAILABLE or not raw:
        return info
    try:
        img = Image.open(io.BytesIO(raw))
        info.update({
            "format": img.format or "UNKNOWN",
            "width":  img.width,
            "height": img.height,
            "mode":   img.mode,
        })
    except Exception:
        pass
    return info
