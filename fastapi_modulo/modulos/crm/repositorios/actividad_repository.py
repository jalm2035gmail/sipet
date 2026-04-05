from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.actividad_mapper import actividad_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad, CrmContacto, CrmOportunidad
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_actividades(
    tenant_id: str,
    contacto_id: Optional[int] = None,
    oportunidad_id: Optional[int] = None,
    completada: Optional[bool] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    db = get_db()
    try:
        query = db.query(CrmActividad).filter(CrmActividad.tenant_id == tenant_id, CrmActividad.activo == True)
        if contacto_id is not None:
            query = query.filter(CrmActividad.contacto_id == contacto_id)
        if oportunidad_id is not None:
            query = query.filter(CrmActividad.oportunidad_id == oportunidad_id)
        if completada is not None:
            query = query.filter(CrmActividad.completada == completada)
        if q:
            pattern = f"%{q}%"
            query = query.filter(func.lower(CrmActividad.titulo).like(func.lower(pattern)))
        if responsable:
            query = query.filter(CrmActividad.responsable == responsable)
        total = query.count()
        items = query.order_by(CrmActividad.fecha.desc()).offset(skip).limit(limit).all()
        return {"items": [actividad_to_dict(row) for row in items], "total": total, "skip": skip, "limit": limit}
    finally:
        db.close()


def create_actividad(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmActividad(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return actividad_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_actividad(tenant_id: str, actividad_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmActividad).filter(CrmActividad.tenant_id == tenant_id, CrmActividad.id == actividad_id).first()
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return actividad_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_actividad(tenant_id: str, actividad_id: int) -> bool:
    db = get_db()
    try:
        obj = db.query(CrmActividad).filter(CrmActividad.tenant_id == tenant_id, CrmActividad.id == actividad_id).first()
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


def contacto_exists(tenant_id: str, contacto_id: int) -> bool:
    db = get_db()
    try:
        return db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == contacto_id).first() is not None
    finally:
        db.close()


def oportunidad_exists(tenant_id: str, oportunidad_id: int) -> bool:
    db = get_db()
    try:
        return db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.id == oportunidad_id).first() is not None
    finally:
        db.close()


def get_actividad(tenant_id: str, actividad_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmActividad).filter(CrmActividad.tenant_id == tenant_id, CrmActividad.id == actividad_id).first()
        return actividad_to_dict(obj) if obj else None
    finally:
        db.close()


def archivar_actividad(tenant_id: str, actividad_id: int, actor: str = "") -> Optional[Dict[str, Any]]:
    from datetime import datetime
    db = get_db()
    try:
        obj = db.query(CrmActividad).filter(CrmActividad.tenant_id == tenant_id, CrmActividad.id == actividad_id).first()
        if not obj:
            return None
        obj.activo = False
        obj.archivado_en = datetime.utcnow()
        obj.archivado_por = actor
        db.commit()
        db.refresh(obj)
        return actividad_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
