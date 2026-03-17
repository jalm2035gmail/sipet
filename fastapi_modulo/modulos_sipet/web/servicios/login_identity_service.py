from __future__ import annotations

import json
import os
import secrets
from typing import Dict, Optional

from fastapi import HTTPException, UploadFile

from fastapi_modulo.core.image_utils import optimize_image, profile_for_prefix
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import (
    DEFAULT_LOGIN_IDENTITY,
    IDENTIDAD_LOGIN_CONFIG_PATH,
    IDENTIDAD_LOGIN_IMAGE_DIR,
    _build_login_asset_url,
    _load_login_identity,
)

IDENTITY_UPLOAD_MAX_BYTES = int((os.environ.get("IDENTITY_UPLOAD_MAX_BYTES") or str(5 * 1024 * 1024)).strip() or str(5 * 1024 * 1024))


def ensure_login_identity_paths() -> None:
    os.makedirs(IDENTIDAD_LOGIN_IMAGE_DIR, exist_ok=True)


def _ensure_store_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def save_login_identity(data: Dict[str, str]) -> None:
    _ensure_store_parent_dir(IDENTIDAD_LOGIN_CONFIG_PATH)
    with open(IDENTIDAD_LOGIN_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _get_upload_ext(upload: UploadFile) -> str:
    filename = (upload.filename or "").lower()
    ext = os.path.splitext(filename)[1]
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        return ext
    content_type = (upload.content_type or "").lower()
    if "svg" in content_type:
        return ".svg"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    return ".png"


def remove_login_image_if_custom(filename: Optional[str]) -> None:
    if not filename or filename in {
        DEFAULT_LOGIN_IDENTITY["favicon_filename"],
        DEFAULT_LOGIN_IDENTITY["logo_filename"],
        DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"],
        DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"],
    }:
        return
    path = os.path.join(IDENTIDAD_LOGIN_IMAGE_DIR, filename)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


async def store_login_image(upload: UploadFile, prefix: str) -> Optional[str]:
    if not upload or not upload.filename:
        return None
    content_type = (upload.content_type or "").lower().strip()
    filename = (upload.filename or "").lower()
    ext = os.path.splitext(filename)[1]
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    if content_type and not content_type.startswith("image/") and ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes para identidad institucional")
    data = await upload.read()
    if not data:
        return None
    if len(data) > max(1, IDENTITY_UPLOAD_MAX_BYTES):
        raise HTTPException(status_code=413, detail="La imagen supera el tamaño máximo permitido")
    ensure_login_identity_paths()
    ext = _get_upload_ext(upload)
    optimized, ext = optimize_image(data, ext, profile=profile_for_prefix(prefix))
    new_filename = f"{prefix}_{secrets.token_hex(6)}{ext}"
    image_path = os.path.join(IDENTIDAD_LOGIN_IMAGE_DIR, new_filename)
    with open(image_path, "wb") as fh:
        fh.write(optimized)
    return new_filename


def clear_frontend_page_cache() -> None:
    try:
        from fastapi_modulo.modulos.frontend.controladores import frontend as frontend_module

        frontend_module._page_cache.clear()
    except Exception:
        pass


__all__ = [
    "DEFAULT_LOGIN_IDENTITY",
    "_build_login_asset_url",
    "_load_login_identity",
    "clear_frontend_page_cache",
    "remove_login_image_if_custom",
    "save_login_identity",
    "store_login_image",
]
