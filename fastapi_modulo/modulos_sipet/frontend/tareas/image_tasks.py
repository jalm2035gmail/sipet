"""
tareas/image_tasks.py
─────────────────────────────────────────────────────────────────────────────
Tareas Celery para procesamiento asíncrono de imágenes del módulo frontend.

Responsabilidades:
  • Optimizar imágenes subidas a la galería (redimensionar, convertir a WebP).
  • Generar thumbnails para la vista previa del builder.
  • Limpiar imágenes huérfanas (archivos sin referencia en ninguna página).
  • Reoptimizar toda la galería en lote (tarea administrativa).

Variables de entorno:
  REDIS_URL              Broker de Celery (requerido para tareas async).
  GALLERY_DIR            Ruta de la galería (default: static/gallery).
  GALLERY_MAX_WIDTH      Ancho máximo de imagen optimizada (default: 1200).
  GALLERY_MAX_HEIGHT     Alto máximo de imagen optimizada (default: 1200).
  GALLERY_WEBP_QUALITY   Calidad WebP 1-100 (default: 82).
  THUMBNAIL_WIDTH        Ancho del thumbnail (default: 320).
  THUMBNAIL_HEIGHT       Alto del thumbnail (default: 240).

Uso desde el controlador (llamada async):
    from fastapi_modulo.modulos.frontend.tareas.image_tasks import (
        optimize_gallery_image,
        generate_thumbnail,
    )

    # Dispara la tarea en background y devuelve inmediatamente
    task = optimize_gallery_image.delay(filename="abc123.png")

    # Con callback para actualizar la URL en BD cuando termine
    optimize_gallery_image.apply_async(
        args=["abc123.png"],
        link=notify_upload_complete.s(),
    )

Uso síncrono (tests / fallback):
    result = optimize_gallery_image.apply(args=["abc123.png"])
    print(result.get())
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from celery import Celery
from celery.utils.log import get_task_logger

# ── Configuración ─────────────────────────────────────────────────────────────
_REDIS_URL         = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_GALLERY_DIR       = os.environ.get("GALLERY_DIR", os.path.join("static", "gallery"))
_THUMBS_DIR        = os.environ.get("THUMBS_DIR", os.path.join("static", "gallery", "_thumbs"))
_MAX_WIDTH         = int(os.environ.get("GALLERY_MAX_WIDTH", "1200"))
_MAX_HEIGHT        = int(os.environ.get("GALLERY_MAX_HEIGHT", "1200"))
_WEBP_QUALITY      = int(os.environ.get("GALLERY_WEBP_QUALITY", "82"))
_THUMB_WIDTH       = int(os.environ.get("THUMBNAIL_WIDTH", "320"))
_THUMB_HEIGHT      = int(os.environ.get("THUMBNAIL_HEIGHT", "240"))
_ALLOWED_EXTS      = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_SKIP_OPTIMIZE_EXT = {".svg", ".gif"}   # SVG no se rasteriza; GIF pierde animación

logger       = logging.getLogger(__name__)
task_logger  = get_task_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — INSTANCIA CELERY
# ══════════════════════════════════════════════════════════════════════════════

celery_app = Celery(
    "frontend_image_tasks",
    broker=_REDIS_URL,
    backend=_REDIS_URL,
)

celery_app.conf.update(
    # Serialización
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Zona horaria
    timezone="UTC",
    enable_utc=True,

    # Reintentos automáticos ante fallos transitorios
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Resultados: expirar después de 1 hora
    result_expires=3600,

    # Rutas de tareas de este módulo
    task_routes={
        "fastapi_modulo.modulos.frontend.tareas.image_tasks.*": {
            "queue": "frontend_images"
        }
    },
)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — HELPERS INTERNOS DE IMAGEN (Pillow)
# ══════════════════════════════════════════════════════════════════════════════

def _open_image(path: Path):
    """Abre una imagen con Pillow y la convierte a RGB si es necesario."""
    from PIL import Image
    img = Image.open(path)
    # Convertir paleta (P) y transparencia (RGBA) a RGB para WebP estándar
    if img.mode in ("P", "RGBA"):
        img = img.convert("RGBA")   # mantener alpha para WebP con transparencia
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def _resize_image(img, max_width: int, max_height: int):
    """
    Redimensiona la imagen respetando el aspect ratio si supera los límites.
    Devuelve la imagen (modificada o intacta).
    """
    w, h = img.size
    if w <= max_width and h <= max_height:
        return img
    ratio  = min(max_width / w, max_height / h)
    new_w  = max(1, int(w * ratio))
    new_h  = max(1, int(h * ratio))
    from PIL import Image
    return img.resize((new_w, new_h), Image.LANCZOS)


def _save_as_webp(img, dest: Path, quality: int) -> Path:
    """
    Guarda la imagen como WebP en dest (con extensión .webp).
    Devuelve la ruta del archivo guardado.
    """
    webp_path = dest.with_suffix(".webp")
    img.save(webp_path, format="WEBP", quality=quality, method=4)
    return webp_path


def _make_thumb(img, width: int, height: int):
    """Crea un thumbnail centrado con crop inteligente (thumbnail + crop)."""
    from PIL import Image, ImageOps
    # thumbnail preserva aspect ratio dentro del bounding box
    img_copy = img.copy()
    img_copy.thumbnail((width * 2, height * 2), Image.LANCZOS)
    return ImageOps.fit(img_copy, (width, height), Image.LANCZOS)


def _file_size_kb(path: Path) -> float:
    return path.stat().st_size / 1024 if path.exists() else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — TAREA: OPTIMIZAR IMAGEN DE GALERÍA
# ══════════════════════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    name="frontend.gallery.optimize_image",
    max_retries=3,
    default_retry_delay=10,   # segundos entre reintentos
    soft_time_limit=60,       # mata la tarea si tarda más de 60s
    time_limit=90,
)
def optimize_gallery_image(
    self,
    filename: str,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: Optional[int] = None,
    convert_to_webp: bool = True,
) -> Dict:
    """
    Optimiza una imagen de la galería en background:
      1. Redimensiona a máx max_width × max_height manteniendo aspect ratio.
      2. Convierte a WebP (si convert_to_webp=True y el formato lo permite).
      3. Elimina el archivo original si se guardó con un nombre distinto.
      4. Devuelve un dict con la nueva URL y métricas de ahorro.

    Args:
        filename:        Nombre del archivo en _GALLERY_DIR (ej. "abc123.png").
        max_width:       Override del ancho máximo (default: _MAX_WIDTH).
        max_height:      Override del alto máximo (default: _MAX_HEIGHT).
        quality:         Override de calidad WebP 1-100 (default: _WEBP_QUALITY).
        convert_to_webp: Si False, guarda en el formato original.

    Returns:
        {
          "status":        "optimized" | "skipped" | "error",
          "original_file": "abc123.png",
          "final_file":    "abc123.webp",
          "final_url":     "/static/gallery/abc123.webp",
          "original_kb":   245.3,
          "final_kb":      87.1,
          "saved_pct":     64.5,
        }
    """
    src_path = Path(_GALLERY_DIR) / filename
    ext      = src_path.suffix.lower()

    task_logger.info("optimize_gallery_image: procesando '%s'", filename)

    # ── Validaciones previas ──────────────────────────────────────────────────
    if not src_path.exists():
        task_logger.warning("optimize_gallery_image: archivo no encontrado: %s", src_path)
        return {"status": "error", "error": f"Archivo no encontrado: {filename}"}

    if ext in _SKIP_OPTIMIZE_EXT:
        task_logger.info("optimize_gallery_image: formato %s omitido (sin optimización)", ext)
        return {
            "status":        "skipped",
            "original_file": filename,
            "final_file":    filename,
            "final_url":     f"/static/gallery/{filename}",
            "reason":        f"Formato {ext} no optimizable",
        }

    original_kb = _file_size_kb(src_path)

    try:
        img = _open_image(src_path)

        # Redimensionar
        img = _resize_image(
            img,
            max_width  or _MAX_WIDTH,
            max_height or _MAX_HEIGHT,
        )

        # Determinar destino
        dest_path = src_path
        if convert_to_webp and ext not in (".webp",):
            dest_path = _save_as_webp(img, src_path, quality or _WEBP_QUALITY)
            # Eliminar original si se guardó con nombre distinto
            if src_path.exists() and src_path != dest_path:
                src_path.unlink()
        else:
            # Guardar en formato original con optimización
            save_kwargs: Dict = {}
            if ext in (".jpg", ".jpeg"):
                save_kwargs = {"format": "JPEG", "quality": quality or _WEBP_QUALITY,
                               "optimize": True, "progressive": True}
            elif ext == ".png":
                save_kwargs = {"format": "PNG", "optimize": True}
            elif ext == ".webp":
                save_kwargs = {"format": "WEBP", "quality": quality or _WEBP_QUALITY}
            img.save(dest_path, **save_kwargs)

        final_kb  = _file_size_kb(dest_path)
        saved_pct = round((1 - final_kb / original_kb) * 100, 1) if original_kb > 0 else 0.0

        task_logger.info(
            "optimize_gallery_image: '%s' → '%s' | %.1fKB → %.1fKB (%.1f%% ahorrado)",
            filename, dest_path.name, original_kb, final_kb, saved_pct,
        )

        return {
            "status":        "optimized",
            "original_file": filename,
            "final_file":    dest_path.name,
            "final_url":     f"/static/gallery/{dest_path.name}",
            "original_kb":   round(original_kb, 1),
            "final_kb":      round(final_kb, 1),
            "saved_pct":     saved_pct,
        }

    except Exception as exc:
        task_logger.error("optimize_gallery_image: error procesando '%s': %s", filename, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "original_file": filename, "error": str(exc)}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — TAREA: GENERAR THUMBNAIL
# ══════════════════════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    name="frontend.gallery.generate_thumbnail",
    max_retries=2,
    default_retry_delay=5,
    soft_time_limit=30,
    time_limit=45,
)
def generate_thumbnail(
    self,
    filename: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Dict:
    """
    Genera un thumbnail de una imagen de la galería y lo guarda en
    _THUMBS_DIR con el mismo nombre de archivo.

    El builder puede usar la URL del thumb para la vista previa rápida
    sin cargar la imagen original de alta resolución.

    Args:
        filename: Nombre del archivo en _GALLERY_DIR.
        width:    Ancho del thumbnail (default: _THUMB_WIDTH).
        height:   Alto del thumbnail (default: _THUMB_HEIGHT).

    Returns:
        {
          "status":      "created" | "skipped" | "error",
          "filename":    "abc123.webp",
          "thumb_url":   "/static/gallery/_thumbs/abc123.webp",
        }
    """
    src_path   = Path(_GALLERY_DIR) / filename
    ext        = src_path.suffix.lower()
    thumb_dir  = Path(_THUMBS_DIR)
    thumb_path = thumb_dir / filename

    task_logger.info("generate_thumbnail: procesando '%s'", filename)

    if not src_path.exists():
        return {"status": "error", "error": f"Archivo no encontrado: {filename}"}

    if ext in _SKIP_OPTIMIZE_EXT:
        return {
            "status":    "skipped",
            "filename":  filename,
            "thumb_url": f"/static/gallery/{filename}",
            "reason":    f"Formato {ext} omitido",
        }

    try:
        thumb_dir.mkdir(parents=True, exist_ok=True)
        img   = _open_image(src_path)
        thumb = _make_thumb(img, width or _THUMB_WIDTH, height or _THUMB_HEIGHT)

        # Guardar thumb como WebP para máxima compresión
        if ext not in (".svg", ".gif"):
            thumb_path = thumb_dir / (src_path.stem + ".webp")
            thumb.save(thumb_path, format="WEBP", quality=75, method=4)
        else:
            thumb.save(thumb_path)

        task_logger.info("generate_thumbnail: thumb creado en '%s'", thumb_path)

        return {
            "status":    "created",
            "filename":  thumb_path.name,
            "thumb_url": f"/static/gallery/_thumbs/{thumb_path.name}",
        }

    except Exception as exc:
        task_logger.error("generate_thumbnail: error con '%s': %s", filename, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "filename": filename, "error": str(exc)}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — TAREA: REOPTIMIZAR GALERÍA COMPLETA (batch)
# ══════════════════════════════════════════════════════════════════════════════

@celery_app.task(
    name="frontend.gallery.reoptimize_all",
    soft_time_limit=600,   # 10 min máximo
    time_limit=660,
)
def reoptimize_gallery_all(
    convert_to_webp: bool = True,
    generate_thumbs: bool = True,
) -> Dict:
    """
    Tarea administrativa: reoptimiza todas las imágenes de la galería.
    Lanza optimize_gallery_image y generate_thumbnail como sub-tareas
    independientes (chord / group) para procesamiento paralelo.

    Args:
        convert_to_webp: Convertir imágenes a WebP durante la reoptimización.
        generate_thumbs: Generar thumbnails al mismo tiempo.

    Returns:
        {
          "status":       "dispatched",
          "total_files":  42,
          "task_ids":     ["uuid1", "uuid2", ...],
        }
    """
    gallery_path = Path(_GALLERY_DIR)
    if not gallery_path.exists():
        return {"status": "error", "error": f"Directorio no encontrado: {_GALLERY_DIR}"}

    files = [
        f.name for f in gallery_path.iterdir()
        if f.is_file()
        and f.suffix.lower() in _ALLOWED_EXTS
        and not f.name.startswith("_")   # excluir thumbs u otros prefijados
    ]

    if not files:
        return {"status": "skipped", "reason": "Galería vacía", "total_files": 0}

    task_logger.info(
        "reoptimize_gallery_all: lanzando tareas para %d imágenes "
        "(webp=%s, thumbs=%s)",
        len(files), convert_to_webp, generate_thumbs,
    )

    task_ids = []
    for filename in files:
        t = optimize_gallery_image.delay(
            filename=filename,
            convert_to_webp=convert_to_webp,
        )
        task_ids.append(t.id)

        if generate_thumbs:
            generate_thumbnail.delay(filename=filename)

    return {
        "status":      "dispatched",
        "total_files": len(files),
        "task_ids":    task_ids,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — TAREA: LIMPIAR IMÁGENES HUÉRFANAS
# ══════════════════════════════════════════════════════════════════════════════

@celery_app.task(
    name="frontend.gallery.cleanup_orphans",
    soft_time_limit=120,
    time_limit=150,
)
def cleanup_orphan_images() -> Dict:
    """
    Elimina imágenes de la galería que no están referenciadas en ninguna
    página publicada ni en borrador.

    Proceso:
      1. Lista todos los archivos en _GALLERY_DIR.
      2. Obtiene el HTML de todas las páginas desde la BD.
      3. Marca como huérfanas las que no aparecen en ningún HTML.
      4. Las mueve a _GALLERY_DIR/_trash/ (no elimina directamente).

    Returns:
        {
          "status":       "done",
          "total_files":  55,
          "orphans":      3,
          "moved_to":     "static/gallery/_trash",
          "filenames":    ["old1.webp", "old2.webp"],
        }
    """
    gallery_path = Path(_GALLERY_DIR)
    trash_path   = gallery_path / "_trash"

    if not gallery_path.exists():
        return {"status": "error", "error": f"Directorio no encontrado: {_GALLERY_DIR}"}

    # Obtener todos los archivos de imagen de la galería (excluir subdirs)
    all_files = {
        f.name: f
        for f in gallery_path.iterdir()
        if f.is_file() and f.suffix.lower() in _ALLOWED_EXTS
    }

    if not all_files:
        return {"status": "skipped", "reason": "Galería vacía", "orphans": 0}

    # Recopilar todo el HTML de páginas desde la BD
    try:
        from fastapi_modulo.modulos.frontend.modelos.frontend_store import list_pages
        pages    = list_pages()
        all_html = " ".join(
            (p.get("gjs_html") or "") + " ".join(
                str(b) for b in (p.get("blocks") or [])
            )
            for p in pages
        )
    except Exception as exc:
        task_logger.error("cleanup_orphan_images: no se pudo acceder a páginas: %s", exc)
        return {"status": "error", "error": str(exc)}

    # Detectar huérfanas: archivos cuyo nombre no aparece en ningún HTML
    orphans = [
        fname for fname in all_files
        if fname not in all_html
    ]

    if not orphans:
        task_logger.info("cleanup_orphan_images: sin huérfanas encontradas.")
        return {
            "status":      "done",
            "total_files": len(all_files),
            "orphans":     0,
            "moved_to":    str(trash_path),
            "filenames":   [],
        }

    # Mover huérfanas a _trash (no eliminar directamente por seguridad)
    trash_path.mkdir(parents=True, exist_ok=True)
    moved = []
    for fname in orphans:
        try:
            src = all_files[fname]
            dst = trash_path / fname
            src.rename(dst)
            moved.append(fname)
            task_logger.info("cleanup_orphan_images: movida '%s' → trash", fname)
        except Exception as exc:
            task_logger.warning("cleanup_orphan_images: no se pudo mover '%s': %s", fname, exc)

    return {
        "status":      "done",
        "total_files": len(all_files),
        "orphans":     len(moved),
        "moved_to":    str(trash_path),
        "filenames":   moved,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — HELPER SÍNCRONO (fallback para cuando Celery no está disponible)
# ══════════════════════════════════════════════════════════════════════════════

def optimize_image_sync(
    data: bytes,
    ext: str,
    max_width: int = _MAX_WIDTH,
    max_height: int = _MAX_HEIGHT,
    quality: int = _WEBP_QUALITY,
    convert_to_webp: bool = True,
) -> Tuple[bytes, str]:
    """
    Versión síncrona de la optimización para usar directamente en el
    endpoint de upload cuando Celery no está disponible o se prefiere
    el procesamiento inmediato.

    Args:
        data:            Bytes del archivo original.
        ext:             Extensión con punto, ej. '.png'.
        max_width:       Ancho máximo.
        max_height:      Alto máximo.
        quality:         Calidad de compresión.
        convert_to_webp: Convertir a WebP.

    Returns:
        Tuple (bytes_optimizados, extension_final)
        Si falla, devuelve (data, ext) sin modificar.
    """
    if ext.lower() in _SKIP_OPTIMIZE_EXT:
        return data, ext

    try:
        from io import BytesIO
        from PIL import Image

        img = Image.open(BytesIO(data))
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        img = _resize_image(img, max_width, max_height)

        buf = BytesIO()
        if convert_to_webp and ext.lower() not in (".webp",):
            img.save(buf, format="WEBP", quality=quality, method=4)
            return buf.getvalue(), ".webp"
        else:
            fmt = {
                ".jpg": "JPEG", ".jpeg": "JPEG",
                ".png": "PNG",  ".webp": "WEBP",
            }.get(ext.lower(), "JPEG")
            save_kwargs: Dict = {"format": fmt}
            if fmt == "JPEG":
                save_kwargs.update({"quality": quality, "optimize": True, "progressive": True})
            elif fmt == "WEBP":
                save_kwargs.update({"quality": quality})
            img.save(buf, **save_kwargs)
            return buf.getvalue(), ext.lower()

    except Exception as exc:
        logger.warning("optimize_image_sync: falló para ext=%s: %s — devolviendo original", ext, exc)
        return data, ext
        