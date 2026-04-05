from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.campania_mapper import campania_to_dict
from fastapi_modulo.modulos.crm.mappers.contacto_campania_mapper import contacto_campania_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmCampania, CrmContactoCampania
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_campanias(
    tenant_id: str,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    db = get_db()
    try:
        query = db.query(CrmCampania).filter(CrmCampania.tenant_id == tenant_id, CrmCampania.activo == True)
        if estado:
            query = query.filter(CrmCampania.estado == estado)
        if q:
            pattern = f"%{q}%"
            query = query.filter(func.lower(CrmCampania.nombre).like(func.lower(pattern)))
        if responsable:
            query = query.filter(CrmCampania.asignado_a == responsable)
        total = query.count()
        items = query.order_by(CrmCampania.creado_en.desc()).offset(skip).limit(limit).all()
        return {"items": [campania_to_dict(row) for row in items], "total": total, "skip": skip, "limit": limit}
    finally:
        db.close()


def create_campania(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmCampania(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return campania_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_campania(tenant_id: str, campania_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmCampania).filter(CrmCampania.tenant_id == tenant_id, CrmCampania.id == campania_id).first()
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return campania_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_contactos_campania(tenant_id: str, campania_id: int) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = db.query(CrmContactoCampania).filter(CrmContactoCampania.tenant_id == tenant_id, CrmContactoCampania.campania_id == campania_id).all()
        return [contacto_campania_to_dict(row) for row in rows]
    finally:
        db.close()


def add_contacto_campania(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmContactoCampania(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return contacto_campania_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def remove_contacto_campania(tenant_id: str, campania_id: int, contacto_id: int) -> bool:
    db = get_db()
    try:
        obj = (
            db.query(CrmContactoCampania)
            .filter(CrmContactoCampania.tenant_id == tenant_id)
            .filter(CrmContactoCampania.campania_id == campania_id)
            .filter(CrmContactoCampania.contacto_id == contacto_id)
            .first()
        )
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def contacto_campania_exists(tenant_id: str, contacto_id: int, campania_id: int) -> bool:
    db = get_db()
    try:
        return (
            db.query(CrmContactoCampania)
            .filter(CrmContactoCampania.tenant_id == tenant_id)
            .filter(CrmContactoCampania.contacto_id == contacto_id)
            .filter(CrmContactoCampania.campania_id == campania_id)
            .first()
            is not None
        )
    finally:
        db.close()


def get_campania(tenant_id: str, campania_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmCampania).filter(CrmCampania.tenant_id == tenant_id, CrmCampania.id == campania_id).first()
        return campania_to_dict(obj) if obj else None
    finally:
        db.close()


def archivar_campania(tenant_id: str, campania_id: int, actor: str = "") -> Optional[Dict[str, Any]]:
    from datetime import datetime
    db = get_db()
    try:
        obj = db.query(CrmCampania).filter(CrmCampania.tenant_id == tenant_id, CrmCampania.id == campania_id).first()
        if not obj:
            return None
        obj.activo = False
        obj.archivado_en = datetime.utcnow()
        obj.archivado_por = actor
        db.commit()
        db.refresh(obj)
        return campania_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
