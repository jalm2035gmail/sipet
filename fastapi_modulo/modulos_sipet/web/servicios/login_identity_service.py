from __future__ import annotations

import json
import logging
import os
import secrets
import threading
from typing import Dict, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.image_utils import optimize_image, profile_for_prefix
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.web.modelos.db_models import WebLoginIdentity
from fastapi_modulo.modulos_sipet.web.servicios.login_identity_constants import (
    DEFAULT_LOGIN_IDENTITY,
    LEGACY_LOGIN_IDENTITY_CONFIG_PATH,
    LOGIN_IDENTITY_IMAGE_DIR,
)

IDENTITY_UPLOAD_MAX_BYTES = int((os.environ.get("IDENTITY_UPLOAD_MAX_BYTES") or str(5 * 1024 * 1024)).strip() or str(5 * 1024 * 1024))
IDENTITY_UPLOAD_IMAGE_MAX_BYTES = int((os.environ.get("IDENTITY_UPLOAD_IMAGE_MAX_BYTES") or str(5 * 1024 * 1024)).strip() or str(5 * 1024 * 1024))
IDENTITY_UPLOAD_SVG_MAX_BYTES = int((os.environ.get("IDENTITY_UPLOAD_SVG_MAX_BYTES") or str(512 * 1024)).strip() or str(512 * 1024))
_READY_DATABASES: set[str] = set()
_READY_LOCK = threading.Lock()
_SINGLETON_KEY = "default"
logger = logging.getLogger(__name__)


def ensure_login_identity_paths() -> None:
    os.makedirs(LOGIN_IDENTITY_IMAGE_DIR, exist_ok=True)


def _ensure_store_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _build_login_asset_url(filename: Optional[str], default_filename: str) -> str:
    selected = filename or default_filename
    selected_path = os.path.join(LOGIN_IDENTITY_IMAGE_DIR, selected)
    if not os.path.exists(selected_path):
        selected = default_filename
        selected_path = os.path.join(LOGIN_IDENTITY_IMAGE_DIR, selected)
    version = int(os.path.getmtime(selected_path)) if os.path.exists(selected_path) else 0
    return f"/templates/imagenes/{selected}?v={version}"


def ensure_login_identity_schema(host: Optional[str] = None) -> None:
    engine = core_db.get_engine_for_host(host if host is not None else core_db.get_request_host())
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS web_login_identity (
                    id SERIAL PRIMARY KEY,
                    singleton_key VARCHAR(32) NOT NULL DEFAULT 'default',
                    favicon_filename VARCHAR(255) NOT NULL DEFAULT 'icon.png',
                    logo_filename VARCHAR(255) NOT NULL DEFAULT 'icon.png',
                    login_logo_filename VARCHAR(255) NOT NULL DEFAULT 'icon.png',
                    desktop_bg_filename VARCHAR(255) NOT NULL DEFAULT 'fondo.jpg',
                    mobile_bg_filename VARCHAR(255) NOT NULL DEFAULT 'movil.jpg',
                    company_short_name VARCHAR(60) NOT NULL DEFAULT 'AVAN',
                    login_message VARCHAR(200) NOT NULL DEFAULT 'Incrementando el nivel de eficiencia',
                    menu_position VARCHAR(16) NOT NULL DEFAULT 'arriba',
                    sidebar_style_variant VARCHAR(16) NOT NULL DEFAULT 'modern',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_web_login_identity_singleton_key
                ON web_login_identity (singleton_key)
                """
            )
        )
    inspector = inspect(engine)
    columns = {str(item.get("name") or "").strip() for item in inspector.get_columns("web_login_identity")}
    if "login_logo_filename" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE web_login_identity "
                    "ADD COLUMN login_logo_filename VARCHAR(255) NOT NULL DEFAULT 'icon.png'"
                )
            )
    if "sidebar_style_variant" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE web_login_identity "
                    "ADD COLUMN sidebar_style_variant VARCHAR(16) NOT NULL DEFAULT 'modern'"
                )
            )


def _database_ready_key(host: Optional[str]) -> str:
    info = core_db.get_current_database_info(host)
    db_url = str(info.get("url") or "").strip()
    if db_url:
        return db_url
    normalized_host = str(info.get("host") or host or "").strip().lower()
    return f"host:{normalized_host or 'default'}"


def _load_legacy_login_identity() -> Dict[str, str]:
    if not os.path.exists(LEGACY_LOGIN_IDENTITY_CONFIG_PATH):
        return {}
    try:
        with open(LEGACY_LOGIN_IDENTITY_CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: str(value).strip() for key, value in data.items() if isinstance(value, str)}


def _cleanup_legacy_login_identity_file() -> None:
    try:
        if os.path.exists(LEGACY_LOGIN_IDENTITY_CONFIG_PATH):
            os.remove(LEGACY_LOGIN_IDENTITY_CONFIG_PATH)
    except OSError:
        pass


def _migrate_legacy_login_identity(db: Session) -> None:
    has_identity = db.query(WebLoginIdentity.id).first() is not None
    if has_identity:
        return
    payload = DEFAULT_LOGIN_IDENTITY.copy()
    payload.update(_load_legacy_login_identity())
    row = WebLoginIdentity(
        singleton_key=_SINGLETON_KEY,
        favicon_filename=payload["favicon_filename"],
        logo_filename=payload["logo_filename"],
        login_logo_filename=payload["login_logo_filename"],
        desktop_bg_filename=payload["desktop_bg_filename"],
        mobile_bg_filename=payload["mobile_bg_filename"],
        company_short_name=payload["company_short_name"],
        login_message=payload["login_message"],
        menu_position=payload["menu_position"],
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    _cleanup_legacy_login_identity_file()


def _ensure_login_identity_storage_ready(host: Optional[str] = None) -> None:
    current_host = host if host is not None else core_db.get_request_host()
    ready_key = _database_ready_key(current_host)
    if ready_key in _READY_DATABASES:
        return
    with _READY_LOCK:
        if ready_key in _READY_DATABASES:
            return
        ensure_login_identity_schema(current_host)
        db = core_db.get_session_factory_for_host(current_host)()
        try:
            _migrate_legacy_login_identity(db)
        finally:
            db.close()
        _READY_DATABASES.add(ready_key)


def _db() -> Session:
    current_host = core_db.get_request_host()
    _ensure_login_identity_storage_ready(current_host)
    return core_db.get_session_factory_for_host(current_host)()


def _sanitize_identity_payload(data: Dict[str, str]) -> Dict[str, str]:
    payload = DEFAULT_LOGIN_IDENTITY.copy()
    logo_filename = str(data.get("logo_filename") or payload["logo_filename"]).strip() or payload["logo_filename"]
    login_logo_filename = str(data.get("login_logo_filename") or "").strip() or logo_filename
    payload.update({
        "favicon_filename": str(data.get("favicon_filename") or payload["favicon_filename"]).strip() or payload["favicon_filename"],
        "logo_filename": logo_filename,
        "login_logo_filename": login_logo_filename,
        "desktop_bg_filename": str(data.get("desktop_bg_filename") or payload["desktop_bg_filename"]).strip() or payload["desktop_bg_filename"],
        "mobile_bg_filename": str(data.get("mobile_bg_filename") or payload["mobile_bg_filename"]).strip() or payload["mobile_bg_filename"],
        "company_short_name": str(data.get("company_short_name") or payload["company_short_name"]).strip() or payload["company_short_name"],
        "login_message": str(data.get("login_message") or payload["login_message"]).strip() or payload["login_message"],
        "menu_position": "abajo" if str(data.get("menu_position") or payload["menu_position"]).strip().lower() == "abajo" else "arriba",
        "sidebar_style_variant": "original"
        if str(data.get("sidebar_style_variant") or "").strip().lower() == "original"
        else "modern",
    })
    return payload


def _load_login_identity() -> Dict[str, str]:
    try:
        _ensure_login_identity_storage_ready(core_db.get_request_host())
        db = _db()
        try:
            row = db.query(WebLoginIdentity).filter(WebLoginIdentity.singleton_key == _SINGLETON_KEY).first()
            if row is None:
                return _sanitize_identity_payload(DEFAULT_LOGIN_IDENTITY.copy())
            return _sanitize_identity_payload(
                {
                    "favicon_filename": row.favicon_filename,
                    "logo_filename": row.logo_filename,
                    "login_logo_filename": getattr(row, "login_logo_filename", DEFAULT_LOGIN_IDENTITY["login_logo_filename"]),
                    "desktop_bg_filename": row.desktop_bg_filename,
                    "mobile_bg_filename": row.mobile_bg_filename,
                    "company_short_name": row.company_short_name,
                    "login_message": row.login_message,
                    "menu_position": row.menu_position,
                    "sidebar_style_variant": getattr(row, "sidebar_style_variant", "modern"),
                }
            )
        finally:
            db.close()
    except Exception:
        logger.exception("login identity load failed")
        return _sanitize_identity_payload(DEFAULT_LOGIN_IDENTITY.copy())


def save_login_identity(data: Dict[str, str]) -> None:
    payload = _sanitize_identity_payload(data)
    db = _db()
    try:
        row = db.query(WebLoginIdentity).filter(WebLoginIdentity.singleton_key == _SINGLETON_KEY).first()
        if row is None:
            row = WebLoginIdentity(singleton_key=_SINGLETON_KEY)
            db.add(row)
        row.favicon_filename = payload["favicon_filename"]
        row.logo_filename = payload["logo_filename"]
        row.login_logo_filename = payload["login_logo_filename"]
        row.desktop_bg_filename = payload["desktop_bg_filename"]
        row.mobile_bg_filename = payload["mobile_bg_filename"]
        row.company_short_name = payload["company_short_name"]
        row.login_message = payload["login_message"]
        row.menu_position = payload["menu_position"]
        row.sidebar_style_variant = payload["sidebar_style_variant"]
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            row = db.query(WebLoginIdentity).filter(WebLoginIdentity.singleton_key == _SINGLETON_KEY).first()
            if row is None:
                raise
            row.favicon_filename = payload["favicon_filename"]
            row.logo_filename = payload["logo_filename"]
            row.login_logo_filename = payload["login_logo_filename"]
            row.desktop_bg_filename = payload["desktop_bg_filename"]
            row.mobile_bg_filename = payload["mobile_bg_filename"]
            row.company_short_name = payload["company_short_name"]
            row.login_message = payload["login_message"]
            row.menu_position = payload["menu_position"]
            row.sidebar_style_variant = payload["sidebar_style_variant"]
            db.commit()
    finally:
        db.close()
    _cleanup_legacy_login_identity_file()


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


def _looks_like_svg(data: bytes) -> bool:
    sample = data[:512].lstrip().lower()
    return sample.startswith(b"<?xml") or sample.startswith(b"<svg") or b"<svg" in sample


def _detect_image_kind(data: bytes) -> str:
    if _looks_like_svg(data):
        return "svg"
    try:
        from PIL import Image

        with Image.open(__import__("io").BytesIO(data)) as image:
            return str(image.format or "").strip().lower()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen valida.") from exc


def _validate_identity_upload(data: bytes, upload: UploadFile, prefix: str) -> tuple[str, int]:
    filename = os.path.basename((upload.filename or "").strip())
    if not filename:
        raise HTTPException(status_code=400, detail="El archivo no tiene un nombre valido.")
    detected_kind = _detect_image_kind(data)
    detected_ext = {
        "svg": ".svg",
        "png": ".png",
        "jpeg": ".jpg",
        "jpg": ".jpg",
        "webp": ".webp",
    }.get(detected_kind)
    if not detected_ext:
        raise HTTPException(status_code=400, detail="Formato de imagen no permitido.")
    allowed_by_prefix = {
        "favicon": {".png", ".jpg", ".webp", ".svg"},
        "logo_empresa": {".png", ".jpg", ".webp", ".svg"},
        "logo_login": {".png", ".jpg", ".webp", ".svg"},
        "fondo_escritorio": {".png", ".jpg", ".webp"},
        "fondo_movil": {".png", ".jpg", ".webp"},
    }
    allowed_exts = allowed_by_prefix.get(prefix, {".png", ".jpg", ".webp", ".svg"})
    if detected_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="El formato no es valido para este recurso visual.")
    max_bytes = IDENTITY_UPLOAD_SVG_MAX_BYTES if detected_ext == ".svg" else IDENTITY_UPLOAD_IMAGE_MAX_BYTES
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="La imagen supera el tamaño maximo permitido para este recurso.")
    return detected_ext, max_bytes


def remove_login_image_if_custom(filename: Optional[str]) -> None:
    if not filename or filename in {
        DEFAULT_LOGIN_IDENTITY["favicon_filename"],
        DEFAULT_LOGIN_IDENTITY["logo_filename"],
        DEFAULT_LOGIN_IDENTITY["login_logo_filename"],
        DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"],
        DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"],
    }:
        return
    path = os.path.join(LOGIN_IDENTITY_IMAGE_DIR, filename)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


async def store_login_image(upload: UploadFile, prefix: str) -> Optional[str]:
    if not upload or not upload.filename:
        return None
    data = await upload.read()
    if not data:
        return None
    if len(data) > max(1, IDENTITY_UPLOAD_MAX_BYTES):
        raise HTTPException(status_code=413, detail="La imagen supera el tamaño maximo permitido")
    ext, _ = _validate_identity_upload(data, upload, prefix)
    ensure_login_identity_paths()
    try:
        optimized, ext = optimize_image(data, ext, profile=profile_for_prefix(prefix))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("identity image optimization failed", extra={"prefix": prefix, "filename": os.path.basename(upload.filename or "")})
        raise HTTPException(status_code=500, detail="No se pudo procesar la imagen.") from exc
    new_filename = f"{prefix}_{secrets.token_hex(6)}{ext}"
    image_path = os.path.join(LOGIN_IDENTITY_IMAGE_DIR, new_filename)
    try:
        with open(image_path, "wb") as fh:
            fh.write(optimized)
    except OSError as exc:
        logger.exception("identity image write failed", extra={"prefix": prefix, "filename": new_filename})
        raise HTTPException(status_code=500, detail="No se pudo guardar la imagen en el servidor.") from exc
    return new_filename


def clear_frontend_page_cache() -> None:
    try:
        from fastapi_modulo.modulos_sipet.frontend.controladores import frontend as frontend_module

        frontend_module._page_cache.clear()
    except Exception:
        pass


__all__ = [
    "DEFAULT_LOGIN_IDENTITY",
    "LOGIN_IDENTITY_IMAGE_DIR",
    "_build_login_asset_url",
    "_load_login_identity",
    "clear_frontend_page_cache",
    "ensure_login_identity_schema",
    "remove_login_image_if_custom",
    "save_login_identity",
    "store_login_image",
]
