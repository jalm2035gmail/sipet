"""
modelos/frontend_store.py
─────────────────────────────────────────────────────────────────────────────
Capa de acceso a datos para el módulo frontend.

Mejoras aplicadas:
  • _migrate_legacy_files_if_needed() se ejecuta UNA sola vez en startup,
    no en cada llamada a _db(). Se usa un flag de módulo protegido por lock.
  • _db() ahora es una función limpia que solo abre la sesión.
  • Nuevas funciones para Contactos y Brand (migrados desde JSON a BD).
  • ensure_frontend_schema() crea todas las tablas nuevas también.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_db_models import (
    FrontendBrand,
    FrontendContact,
    FrontendPage,
    FrontendPageVersion,
)

logger = logging.getLogger(__name__)

# ── Rutas de archivos legacy (solo para migración one-shot) ───────────────────
_STORE_PATH    = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "pages_store.json")
_VERSIONS_PATH = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "versions_store.json")
_CONTACT_PATH  = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "contact_store.json")
_BRAND_PATH    = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "brand_store.json")

_MAX_VERSIONS = 5

# ── Flag de migración: se ejecuta como máximo una vez por proceso ─────────────
_migration_done = False
_migration_lock = threading.Lock()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — SCHEMA Y MIGRACIÓN (startup)
# ══════════════════════════════════════════════════════════════════════════════

def ensure_frontend_schema() -> None:
    """
    Crea todas las tablas del módulo si no existen.
    Incluye las nuevas tablas FrontendContact y FrontendBrand.
    Se llama una sola vez al importar el módulo.
    """
    engine = core_db.get_engine_for_host(core_db.get_request_host())
    MAIN.metadata.create_all(
        bind=engine,
        tables=[
            FrontendPage.__table__,
            FrontendPageVersion.__table__,
            FrontendContact.__table__,
            FrontendBrand.__table__,
        ],
        checkfirst=True,
    )


def run_startup_migration() -> None:
    """
    Ejecuta la migración de archivos JSON → BD exactamente una vez por proceso.
    Llamar desde el lifespan/startup de FastAPI, NO desde _db().

    El lock garantiza que si dos workers arrancan simultáneamente,
    solo uno ejecuta la migración.
    """
    global _migration_done
    if _migration_done:
        return
    with _migration_lock:
        if _migration_done:   # double-checked locking
            return
        db = core_db.get_session_factory_for_host(core_db.get_request_host())()
        try:
            _migrate_all_legacy_files(db)
            _migration_done = True
        except Exception as exc:
            logger.error("Error en migración legacy → BD: %s", exc)
        finally:
            db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — HELPERS INTERNOS
# ══════════════════════════════════════════════════════════════════════════════

def _db() -> Session:
    """
    Abre y devuelve una nueva sesión SQLAlchemy.
    Ya NO ejecuta la migración — eso ocurre en startup.
    El caller es responsable de llamar db.close() en un bloque finally.
    """
    return core_db.get_session_factory_for_host(core_db.get_request_host())()


def _load_legacy_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, type(default)) else default
    except (OSError, json.JSONDecodeError):
        return default


def _page_dict(row: FrontendPage) -> Dict[str, Any]:
    return {
        "id":       row.id,
        "title":    row.title,
        "slug":     row.slug,
        "status":   row.status,
        "is_home":  bool(row.is_home),
        "gjs_html": row.gjs_html or "",
        "gjs_css":  row.gjs_css or "",
        "blocks":   row.blocks if isinstance(row.blocks, list) else [],
        "meta":     row.meta if isinstance(row.meta, dict) else {},
    }


def _version_dict(row: FrontendPageVersion) -> Dict[str, Any]:
    return {
        "saved_at": row.saved_at.strftime("%Y-%m-%d %H:%M UTC") if row.saved_at else "",
        "title":    row.title,
        "status":   row.status,
        "gjs_html": row.gjs_html or "",
        "gjs_css":  row.gjs_css or "",
        "meta":     row.meta if isinstance(row.meta, dict) else {},
    }


def _contact_dict(row: FrontendContact) -> Dict[str, Any]:
    return {
        "id":         row.id,
        "name":       row.name,
        "email":      row.email,
        "message":    row.message,
        "read":       bool(row.read),
        "created_at": row.created_at.isoformat() + "Z" if row.created_at else "",
    }


def _brand_dict(rows: List[FrontendBrand]) -> Dict[str, str]:
    """Convierte las filas clave-valor de FrontendBrand a un dict plano."""
    return {row.key: row.value for row in rows}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — MIGRACIÓN LEGACY (one-shot, invocada desde run_startup_migration)
# ══════════════════════════════════════════════════════════════════════════════

def _migrate_all_legacy_files(db: Session) -> None:
    """
    Migra TODOS los archivos JSON legacy a BD en una sola transacción.
    Solo se ejecuta si la tabla de páginas está vacía (primera vez).
    """
    _migrate_pages_and_versions(db)
    _migrate_contacts(db)
    _migrate_brand(db)


def _migrate_pages_and_versions(db: Session) -> None:
    """Migra pages_store.json y versions_store.json → BD."""
    has_pages = db.query(FrontendPage.id).first() is not None
    if has_pages:
        return

    pages    = _load_legacy_json(_STORE_PATH, [])
    versions = _load_legacy_json(_VERSIONS_PATH, {})
    if not pages:
        return

    logger.info("Migrando %d páginas desde JSON a BD…", len(pages))
    for page in pages:
        row = FrontendPage(
            id=str(page.get("id") or ""),
            title=str(page.get("title") or "Sin título").strip(),
            slug=str(page.get("slug") or "").strip(),
            status=str(page.get("status") or "draft").strip(),
            is_home=bool(page.get("is_home", False)),
            gjs_html=str(page.get("gjs_html") or ""),
            gjs_css=str(page.get("gjs_css") or ""),
            blocks=page.get("blocks") if isinstance(page.get("blocks"), list) else [],
            meta=page.get("meta") if isinstance(page.get("meta"), dict) else {},
        )
        db.add(row)
        for snap in versions.get(row.id, [])[:_MAX_VERSIONS]:
            db.add(FrontendPageVersion(
                page_id=row.id,
                title=str(snap.get("title") or row.title),
                status=str(snap.get("status") or row.status),
                gjs_html=str(snap.get("gjs_html") or ""),
                gjs_css=str(snap.get("gjs_css") or ""),
                meta=snap.get("meta") if isinstance(snap.get("meta"), dict) else {},
            ))
    db.commit()
    logger.info("Migración de páginas completada.")


def _migrate_contacts(db: Session) -> None:
    """Migra contact_store.json → tabla frontend_contacts."""
    has_contacts = db.query(FrontendContact.id).first() is not None
    if has_contacts:
        return

    contacts = _load_legacy_json(_CONTACT_PATH, [])
    if not contacts:
        return

    logger.info("Migrando %d contactos desde JSON a BD…", len(contacts))
    for c in contacts:
        created_raw = c.get("created_at") or ""
        try:
            created_at = datetime.fromisoformat(created_raw.rstrip("Z"))
        except (ValueError, AttributeError):
            created_at = datetime.utcnow()

        db.add(FrontendContact(
            id=str(c.get("id") or ""),
            name=str(c.get("name") or "").strip(),
            email=str(c.get("email") or "").strip(),
            message=str(c.get("message") or "").strip(),
            read=bool(c.get("read", False)),
            created_at=created_at,
        ))
    db.commit()
    logger.info("Migración de contactos completada.")


def _migrate_brand(db: Session) -> None:
    """Migra brand_store.json → tabla frontend_brand (clave-valor)."""
    has_brand = db.query(FrontendBrand.key).first() is not None
    if has_brand:
        return

    brand = _load_legacy_json(_BRAND_PATH, {})
    if not brand:
        return

    logger.info("Migrando configuración de brand desde JSON a BD…")
    for key, value in brand.items():
        if isinstance(value, str):
            db.add(FrontendBrand(key=key, value=value))
    db.commit()
    logger.info("Migración de brand completada.")


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

def list_pages() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = db.query(FrontendPage).order_by(FrontendPage.created_at.asc(), FrontendPage.id.asc()).all()
        return [_page_dict(row) for row in rows]
    finally:
        db.close()


def get_page(page_id: str) -> Optional[Dict[str, Any]]:
    db = _db()
    try:
        row = db.query(FrontendPage).filter(FrontendPage.id == page_id).first()
        return _page_dict(row) if row else None
    finally:
        db.close()


def get_page_by_slug(slug: str, published_only: bool = False) -> Optional[Dict[str, Any]]:
    db = _db()
    try:
        q = db.query(FrontendPage).filter(FrontendPage.slug == slug)
        if published_only:
            q = q.filter(FrontendPage.status == "published")
        row = q.first()
        return _page_dict(row) if row else None
    finally:
        db.close()


def _snapshot_version(db: Session, page: FrontendPage) -> None:
    """Guarda una snapshot de la página y elimina versiones antiguas sobre el límite."""
    db.add(FrontendPageVersion(
        page_id=page.id,
        title=page.title,
        status=page.status,
        gjs_html=page.gjs_html or "",
        gjs_css=page.gjs_css or "",
        meta=page.meta if isinstance(page.meta, dict) else {},
    ))
    # Eliminar versiones que superan el límite (mantener las _MAX_VERSIONS más recientes)
    extra = (
        db.query(FrontendPageVersion)
        .filter(FrontendPageVersion.page_id == page.id)
        .order_by(FrontendPageVersion.saved_at.desc(), FrontendPageVersion.id.desc())
        .offset(_MAX_VERSIONS)
        .all()
    )
    for row in extra:
        db.delete(row)


def upsert_page(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        page_id = str(payload.get("id") or "").strip()
        row = db.query(FrontendPage).filter(FrontendPage.id == page_id).first() if page_id else None
        if row is None:
            row = FrontendPage(id=page_id)
            db.add(row)

        row.title    = str(payload.get("title") or "Sin título").strip()
        row.slug     = str(payload.get("slug") or "").strip()
        row.status   = str(payload.get("status") or "draft").strip()
        row.is_home  = bool(payload.get("is_home", False))
        row.gjs_html = str(payload.get("gjs_html") or "")
        row.gjs_css  = str(payload.get("gjs_css") or "")
        row.blocks   = payload.get("blocks") if isinstance(payload.get("blocks"), list) else []
        row.meta     = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        db.flush()

        # Si esta página es home, quita el flag a las demás
        if row.is_home:
            (db.query(FrontendPage)
               .filter(FrontendPage.id != row.id)
               .update({"is_home": False}, synchronize_session=False))

        _snapshot_version(db, row)
        db.commit()
        db.refresh(row)

        pages = db.query(FrontendPage).order_by(FrontendPage.created_at.asc(), FrontendPage.id.asc()).all()
        return {"page": _page_dict(row), "pages": [_page_dict(item) for item in pages]}
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_page(page_id: str) -> List[Dict[str, Any]]:
    db = _db()
    try:
        row = db.query(FrontendPage).filter(FrontendPage.id == page_id).first()
        if row:
            db.query(FrontendPageVersion).filter(FrontendPageVersion.page_id == row.id).delete()
            db.delete(row)
            db.commit()
        rows = db.query(FrontendPage).order_by(FrontendPage.created_at.asc(), FrontendPage.id.asc()).all()
        return [_page_dict(item) for item in rows]
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def publish_page(page_id: str) -> Optional[Dict[str, Any]]:
    db = _db()
    try:
        row = db.query(FrontendPage).filter(FrontendPage.id == page_id).first()
        if not row:
            return None
        row.status = "published"
        db.commit()
        db.refresh(row)
        return _page_dict(row)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — VERSIONES
# ══════════════════════════════════════════════════════════════════════════════

def list_versions(page_id: str) -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(FrontendPageVersion)
            .filter(FrontendPageVersion.page_id == page_id)
            .order_by(FrontendPageVersion.saved_at.desc(), FrontendPageVersion.id.desc())
            .all()
        )
        return [_version_dict(row) for row in rows]
    finally:
        db.close()


def restore_version(page_id: str, version_idx: int) -> Optional[Dict[str, Any]]:
    db = _db()
    try:
        page = db.query(FrontendPage).filter(FrontendPage.id == page_id).first()
        if not page:
            return None
        rows = (
            db.query(FrontendPageVersion)
            .filter(FrontendPageVersion.page_id == page_id)
            .order_by(FrontendPageVersion.saved_at.desc(), FrontendPageVersion.id.desc())
            .all()
        )
        if version_idx < 0 or version_idx >= len(rows):
            return None
        snap          = rows[version_idx]
        page.gjs_html = snap.gjs_html or ""
        page.gjs_css  = snap.gjs_css or ""
        page.meta     = snap.meta if isinstance(snap.meta, dict) else {}
        db.commit()
        db.refresh(page)
        return _page_dict(page)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — CONTACTOS (migrado desde JSON)
# ══════════════════════════════════════════════════════════════════════════════

def list_contacts() -> List[Dict[str, Any]]:
    """Devuelve todos los mensajes de contacto, más recientes primero."""
    db = _db()
    try:
        rows = (
            db.query(FrontendContact)
            .order_by(FrontendContact.created_at.desc())
            .all()
        )
        return [_contact_dict(row) for row in rows]
    finally:
        db.close()


def create_contact(id: str, name: str, email: str, message: str) -> Dict[str, Any]:
    """Inserta un nuevo mensaje de contacto."""
    db = _db()
    try:
        row = FrontendContact(
            id=id,
            name=name,
            email=email,
            message=message,
            read=False,
            created_at=datetime.utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _contact_dict(row)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def mark_contact_read(contact_id: str) -> bool:
    """
    Marca un mensaje de contacto como leído.
    Devuelve True si encontró el registro, False si no existe.
    """
    db = _db()
    try:
        row = db.query(FrontendContact).filter(FrontendContact.id == contact_id).first()
        if not row:
            return False
        row.read = True
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_contact(contact_id: str) -> bool:
    """Elimina un mensaje de contacto. Devuelve True si existía."""
    db = _db()
    try:
        row = db.query(FrontendContact).filter(FrontendContact.id == contact_id).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — BRAND (migrado desde JSON)
# ══════════════════════════════════════════════════════════════════════════════

def get_brand() -> Dict[str, str]:
    """Devuelve la configuración de marca como dict {clave: valor}."""
    db = _db()
    try:
        rows = db.query(FrontendBrand).all()
        return _brand_dict(rows)
    finally:
        db.close()


def save_brand(updates: Dict[str, str]) -> Dict[str, str]:
    """
    Actualiza o inserta claves de marca (upsert por clave).
    Solo acepta valores de tipo str para evitar corrupción del store.
    Devuelve el brand completo actualizado.
    """
    db = _db()
    try:
        for key, value in updates.items():
            if not isinstance(value, str):
                continue
            row = db.query(FrontendBrand).filter(FrontendBrand.key == key).first()
            if row:
                row.value = value
            else:
                db.add(FrontendBrand(key=key, value=value))
        db.commit()
        rows = db.query(FrontendBrand).all()
        return _brand_dict(rows)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ── Llamada de inicialización al importar el módulo ───────────────────────────
# ensure_frontend_schema() crea las tablas si no existen.
# run_startup_migration() debe llamarse explícitamente desde el lifespan
# de FastAPI para no bloquear importaciones en tests.
ensure_frontend_schema()
