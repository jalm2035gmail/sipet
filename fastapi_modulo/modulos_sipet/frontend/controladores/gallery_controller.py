"""
controladores/gallery_controller.py
─────────────────────────────────────────────────────────────────────────────
Galería de imágenes del módulo frontend.

Rutas:
  GET    /api/frontend/gallery
  POST   /api/frontend/gallery/upload
  DELETE /api/frontend/gallery/{filename}
"""

from __future__ import annotations

import logging
import os
import uuid as _uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    create_gallery_image,
    delete_gallery_image,
    get_gallery_image_by_filename,
    list_gallery_images,
    update_gallery_image,
)
from fastapi_modulo.modulos_sipet.frontend.servicios import cache_service
from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/frontend", tags=["Gallery"])

_GALLERY_DIR        = os.path.join("static", "gallery")
_GALLERY_MAX_MB     = 5
_ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
_FRONTEND_BUILDER_SCREEN = "frontend.builder"
_GALLERY_CACHE_KEY  = "gallery:list"


@router.get("/gallery")
def api_gallery_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")

    # Serve from cache if available
    cached = cache_service.get(_GALLERY_CACHE_KEY)
    if cached is not None:
        return {"success": True, "data": cached}

    items = list_gallery_images()
    # Fallback: filesystem scan for images not yet in DB (legacy / direct uploads)
    os.makedirs(_GALLERY_DIR, exist_ok=True)
    db_filenames = {item["filename"] for item in items}
    for fname in sorted(os.listdir(_GALLERY_DIR)):
        if os.path.splitext(fname)[1].lower() in _ALLOWED_IMAGE_EXTS and fname not in db_filenames:
            items.append({
                "id": None,
                "filename": fname,
                "orig_name": fname,
                "status": "optimized",
                "url": f"/static/gallery/{fname}",
                "size_kb": 0.0,
                "error": None,
            })

    cache_service.set(_GALLERY_CACHE_KEY, items)
    return {"success": True, "data": items}


@router.post("/gallery/upload")
async def api_gallery_upload(
    request: Request,
    file:  Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    files: Optional[UploadFile] = File(None),
):
    require_write(request)
    upload = file or image or files
    form_error  = None
    form_debug: list[str] = []

    if upload is None or not getattr(upload, "filename", None):
        try:
            form = await request.form()
            for _, value in form.multi_items():
                form_debug.append(
                    f"{type(value).__name__}:"
                    f"{getattr(value, 'filename', '') or getattr(value, '__class__', type(value)).__name__}"
                )
                if getattr(value, "filename", None):
                    upload = value
                    break
        except Exception as exc:
            form_error = str(exc) or exc.__class__.__name__
            logger.exception("frontend gallery upload: failed to parse multipart form")
            upload = None

    if upload is None or not getattr(upload, "filename", None):
        error_message  = "No se recibió ninguna imagen multipart en la solicitud."
        if form_error:
            error_message = f"{error_message} Detalle: {form_error}"
        content_type   = request.headers.get("content-type") or "(sin content-type)"
        content_length = request.headers.get("content-length") or "(sin content-length)"
        debug_fields   = ", ".join(form_debug) if form_debug else "(sin campos parseados)"
        error_message  = (
            f"{error_message} Content-Type: {content_type}. "
            f"Content-Length: {content_length}. Campos: {debug_fields}."
        )
        return JSONResponse({"success": False, "error": error_message}, status_code=400)

    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        return JSONResponse(
            {"success": False, "error": f"Tipo no permitido. Usa: {', '.join(_ALLOWED_IMAGE_EXTS)}"},
            status_code=415,
        )

    data = await upload.read()
    if len(data) > _GALLERY_MAX_MB * 1024 * 1024:
        return JSONResponse(
            {"success": False, "error": f"Imagen demasiado grande (máx {_GALLERY_MAX_MB} MB)"},
            status_code=413,
        )

    orig_name  = upload.filename or f"upload{ext}"
    image_id   = _uuid.uuid4().hex
    safe_name  = f"{image_id}{ext}"
    final_ext  = ext
    final_name = safe_name
    status     = "uploaded"

    # ── Intentar optimización síncrona (inline) ───────────────────────────────
    try:
        from fastapi_modulo.core.image_utils import optimize_image
        data, final_ext = optimize_image(data, ext, profile="asset")
        final_name = f"{image_id}{final_ext}"
        status     = "optimized"
    except Exception:
        pass  # Guarda el original; la tarea Celery optimizará en background

    os.makedirs(_GALLERY_DIR, exist_ok=True)
    dest_path = os.path.join(_GALLERY_DIR, final_name)
    with open(dest_path, "wb") as fh:
        fh.write(data)

    size_kb = len(data) / 1024
    url     = f"/static/gallery/{final_name}"

    # ── Registrar en BD ───────────────────────────────────────────────────────
    try:
        create_gallery_image(
            image_id=image_id,
            filename=final_name,
            url=url,
            orig_name=orig_name,
            size_kb=size_kb,
            status=status,
        )
    except Exception:
        logger.exception("gallery upload: no se pudo registrar imagen en BD (image_id=%s)", image_id)

    # ── Si no se optimizó inline, encolar tarea Celery ────────────────────────
    if status == "uploaded":
        try:
            from fastapi_modulo.modulos_sipet.frontend.tareas.image_tasks import optimize_gallery_image
            optimize_gallery_image.delay(filename=final_name, image_id=image_id)
            update_gallery_image(image_id, status="processing")
            status = "processing"
        except Exception:
            logger.warning("gallery upload: Celery no disponible — imagen guardada sin optimizar")

    # Invalidar caché de galería
    cache_service.delete(_GALLERY_CACHE_KEY)

    return {
        "success":  True,
        "id":       image_id,
        "filename": final_name,
        "url":      url,
        "status":   status,
    }


@router.delete("/gallery/{filename}")
def api_gallery_delete(request: Request, filename: str):
    require_write(request)
    # Validar que el filename no escape del directorio (path traversal)
    safe = os.path.basename(filename)
    if safe != filename or ".." in filename:
        return JSONResponse({"success": False, "error": "Nombre de archivo inválido"}, status_code=400)

    # Eliminar de BD (por filename)
    record = get_gallery_image_by_filename(safe)
    if record and record.get("id"):
        try:
            delete_gallery_image(record["id"])
        except Exception:
            logger.exception("gallery delete: error eliminando registro BD para '%s'", safe)

    # Eliminar de disco
    path = os.path.join(_GALLERY_DIR, safe)
    deleted = False
    if os.path.isfile(path):
        try:
            os.remove(path)
            deleted = True
        except OSError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    # Invalidar caché
    cache_service.delete(_GALLERY_CACHE_KEY)

    return {"success": True, "deleted": deleted}
