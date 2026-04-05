from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.multiempresa.modelos import me_logo_service as logo_svc
from fastapi_modulo.modulos.multiempresa.modelos import me_repository as repo
from fastapi_modulo.modulos.multiempresa.modelos.me_db_models import MeEmpresa
from fastapi_modulo.modulos.multiempresa.modelos.me_serializer import empresa_dict

_ME_TABLES = [MeEmpresa.__table__]


def ensure_me_schema() -> None:
    MAIN.metadata.create_all(bind=core_db.get_admin_engine(), tables=_ME_TABLES, checkfirst=True)


def _db():
    return core_db.get_admin_session_factory()()


# ── Public API ────────────────────────────────────────────────────────────────

def list_empresas(
    estado: Optional[str] = None,
    tenant_filter: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort: str = "nombre",
) -> Dict[str, Any]:
    db = _db()
    try:
        total, items = repo.find_all(db, tenant_filter=tenant_filter, estado=estado, q=q, sort=sort, limit=limit, offset=offset)
        return {"total": total, "items": [empresa_dict(o) for o in items], "limit": limit, "offset": offset}
    finally:
        db.close()


def get_empresa(empresa_id: int, tenant_filter: Optional[str] = None) -> Optional[Dict]:
    db = _db()
    try:
        obj = repo.find_by_id(db, empresa_id, tenant_filter)
        return empresa_dict(obj) if obj else None
    finally:
        db.close()


def get_empresa_by_tenant(tenant_id: str) -> Optional[Dict]:
    db = _db()
    try:
        obj = repo.find_by_tenant(db, tenant_id)
        return empresa_dict(obj) if obj else None
    finally:
        db.close()


def create_empresa(data: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        obj = repo.insert(db, data)
        return empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_empresa(empresa_id: int, data: Dict[str, Any], tenant_filter: Optional[str] = None) -> Optional[Dict]:
    db = _db()
    try:
        obj = repo.find_by_id(db, empresa_id, tenant_filter)
        if not obj:
            return None
        obj = repo.update(db, obj, data)
        return empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_empresa(empresa_id: int, tenant_filter: Optional[str] = None) -> bool:
    db = _db()
    try:
        obj = repo.find_by_id(db, empresa_id, tenant_filter)
        if not obj:
            return False
        if obj.logo_filename:
            logo_svc.remove(obj.logo_filename)
        repo.delete(db, obj)
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def save_logo(
    empresa_id: int,
    data: bytes,
    content_type: str,
    tenant_filter: Optional[str] = None,
) -> Optional[Dict]:
    logo_svc.validate(data, content_type)
    db = _db()
    try:
        obj = repo.find_by_id(db, empresa_id, tenant_filter)
        if not obj:
            return None
        if obj.logo_filename:
            logo_svc.remove(obj.logo_filename)
        new_filename = logo_svc.build_filename(obj.id, content_type)
        logo_svc.save(new_filename, data)
        obj = repo.update(db, obj, {"logo_filename": new_filename})
        return empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_logo_path(filename: str):
    return logo_svc.get_path(filename)


def get_me_kpis(tenant_filter: Optional[str] = None) -> Dict[str, Any]:
    db = _db()
    try:
        total, activas, con_logo = repo.aggregate_kpis(db, tenant_filter)
        total = total or 0
        activas = int(activas or 0)
        con_logo = int(con_logo or 0)
        return {
            "total_empresas": total,
            "empresas_activas": activas,
            "empresas_inactivas": total - activas,
            "empresas_con_logo": con_logo,
        }
    finally:
        db.close()


def get_me_consolidado(tenant_filter: Optional[str] = None) -> Dict[str, Any]:
    db = _db()
    try:
        _, items = repo.find_all(db, tenant_filter=tenant_filter, limit=10000)
        return {"empresas": [empresa_dict(e) for e in items]}
    finally:
        db.close()


_ME_TABLES = [MeEmpresa.__table__]

UPLOADS_DIR = pathlib.Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_me_schema() -> None:
    MAIN.metadata.create_all(bind=core_db.get_admin_engine(), tables=_ME_TABLES, checkfirst=True)


def _db():
    return core_db.get_admin_session_factory()()


# ── Serializer ────────────────────────────────────────────────────────────────

def _empresa_dict(obj: MeEmpresa) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "codigo": obj.codigo,
        "nombre": obj.nombre,
        "tenant_id": obj.tenant_id,
        "descripcion": obj.descripcion,
        "email_contacto": obj.email_contacto,
        "telefono": obj.telefono,
        "direccion": obj.direccion,
        "rfc": obj.rfc,
        "color_primario": obj.color_primario or "#0f172a",
        "estado": obj.estado,
        "logo_filename": obj.logo_filename,
        "logo_url": f"/api/multiempresa/logos/{obj.logo_filename}" if obj.logo_filename else None,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else None,
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else None,
    }


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_empresas(
    estado: Optional[str] = None,
    tenant_filter: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort: str = "nombre",
) -> Dict[str, Any]:
    db = _db()
    try:
        query = db.query(MeEmpresa)
        if tenant_filter:
            query = query.filter(MeEmpresa.tenant_id == tenant_filter)
        if estado:
            query = query.filter(MeEmpresa.estado == estado)
        if q:
            pattern = f"%{q}%"
            query = query.filter(
                or_(MeEmpresa.nombre.ilike(pattern), MeEmpresa.codigo.ilike(pattern))
            )
        total = query.count()
        sort_col = {
            "nombre": MeEmpresa.nombre,
            "codigo": MeEmpresa.codigo,
            "estado": MeEmpresa.estado,
            "creado_en": MeEmpresa.creado_en,
        }.get(sort, MeEmpresa.nombre)
        items = query.order_by(sort_col).offset(offset).limit(limit).all()
        return {
            "total": total,
            "items": [_empresa_dict(o) for o in items],
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()


def get_empresa(empresa_id: int, tenant_filter: Optional[str] = None) -> Optional[Dict]:
    db = _db()
    try:
        q = db.query(MeEmpresa).filter(MeEmpresa.id == empresa_id)
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        obj = q.first()
        return _empresa_dict(obj) if obj else None
    finally:
        db.close()


def get_empresa_by_tenant(tenant_id: str) -> Optional[Dict]:
    db = _db()
    try:
        obj = db.query(MeEmpresa).filter(MeEmpresa.tenant_id == tenant_id).first()
        return _empresa_dict(obj) if obj else None
    finally:
        db.close()


def create_empresa(data: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        obj = MeEmpresa(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_empresa(empresa_id: int, data: Dict[str, Any], tenant_filter: Optional[str] = None) -> Optional[Dict]:
    db = _db()
    try:
        q = db.query(MeEmpresa).filter(MeEmpresa.id == empresa_id)
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        obj = q.first()
        if not obj:
            return None
        data["actualizado_en"] = datetime.utcnow()
        for k, v in data.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return _empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_empresa(empresa_id: int, tenant_filter: Optional[str] = None) -> bool:
    db = _db()
    try:
        q = db.query(MeEmpresa).filter(MeEmpresa.id == empresa_id)
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        obj = q.first()
        if not obj:
            return False
        # Remove logo file if present
        if obj.logo_filename:
            _remove_logo_file(obj.logo_filename)
        db.delete(obj)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ── Logo management ───────────────────────────────────────────────────────────

def _remove_logo_file(filename: str) -> None:
    path = UPLOADS_DIR / filename
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


_ALLOWED_LOGO_MIME = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"}
_MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB


def save_logo(
    empresa_id: int,
    data: bytes,
    content_type: str,
    tenant_filter: Optional[str] = None,
) -> Optional[Dict]:
    """Persist the logo file and update the empresa record. Returns updated empresa dict."""
    if content_type not in _ALLOWED_LOGO_MIME:
        raise ValueError(f"Tipo de archivo no soportado: {content_type}")
    if len(data) > _MAX_LOGO_BYTES:
        raise ValueError("El archivo excede el tamaño máximo de 2 MB")

    db = _db()
    try:
        q = db.query(MeEmpresa).filter(MeEmpresa.id == empresa_id)
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        obj = q.first()
        if not obj:
            return None

        # Remove old logo
        if obj.logo_filename:
            _remove_logo_file(obj.logo_filename)

        # Determine extension
        ext = mimetypes.guess_extension(content_type) or ".bin"
        # Normalise common aliases
        ext = {".jpe": ".jpg", ".jpeg": ".jpg", ".webp": ".webp"}.get(ext, ext)
        ts = int(time.time())
        new_filename = f"empresa_{obj.id}_{ts}{ext}"

        file_path = UPLOADS_DIR / new_filename
        file_path.write_bytes(data)

        obj.logo_filename = new_filename
        obj.actualizado_en = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return _empresa_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_logo_path(filename: str) -> Optional[pathlib.Path]:
    """Return the absolute Path of a logo file if it exists, otherwise None."""
    # Prevent path traversal
    safe = pathlib.Path(filename).name
    path = UPLOADS_DIR / safe
    return path if path.exists() else None


# ── KPIs (SQL aggregates) ─────────────────────────────────────────────────────

def get_me_kpis(tenant_filter: Optional[str] = None) -> Dict[str, Any]:
    """Return KPI counts computed entirely in SQL."""
    db = _db()
    try:
        q = db.query(
            func.count(MeEmpresa.id),
            func.sum(case((MeEmpresa.estado == "activa", 1), else_=0)),
            func.sum(case((MeEmpresa.logo_filename.isnot(None), 1), else_=0)),
        )
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        total, activas, con_logo = q.one()
        total = total or 0
        activas = int(activas or 0)
        con_logo = int(con_logo or 0)
        return {
            "total_empresas": total,
            "empresas_activas": activas,
            "empresas_inactivas": total - activas,
            "empresas_con_logo": con_logo,
        }
    finally:
        db.close()


# ── Consolidado ────────────────────────────────────────────────────────────────

def get_me_consolidado(tenant_filter: Optional[str] = None) -> Dict[str, Any]:
    """Return full empresa list for the consolidado panel."""
    db = _db()
    try:
        q = db.query(MeEmpresa)
        if tenant_filter:
            q = q.filter(MeEmpresa.tenant_id == tenant_filter)
        empresas = q.order_by(MeEmpresa.nombre).all()
        return {"empresas": [_empresa_dict(e) for e in empresas]}
    finally:
        db.close()
