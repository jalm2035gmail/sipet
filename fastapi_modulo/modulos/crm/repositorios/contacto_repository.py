from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.contacto_mapper import contacto_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmActividad,
    CrmContacto,
    CrmContactoCampania,
    CrmNota,
    CrmOportunidad,
)
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_contactos(
    tenant_id: str,
    tipo: Optional[str] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    sucursal: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    db = get_db()
    try:
        query = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.activo == True)
        if tipo:
            query = query.filter(CrmContacto.tipo == tipo)
        if q:
            pattern = f"%{q}%"
            query = query.filter(
                func.lower(CrmContacto.nombre).like(func.lower(pattern))
                | func.lower(CrmContacto.email).like(func.lower(pattern))
                | func.lower(CrmContacto.empresa).like(func.lower(pattern))
            )
        if responsable:
            query = query.filter(CrmContacto.asignado_a == responsable)
        if sucursal:
            query = query.filter(CrmContacto.sucursal == sucursal)
        total = query.count()
        items = query.order_by(CrmContacto.nombre).offset(skip).limit(limit).all()
        return {"items": [contacto_to_dict(row) for row in items], "total": total, "skip": skip, "limit": limit}
    finally:
        db.close()


def get_contacto(tenant_id: str, contacto_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == contacto_id).first()
        return contacto_to_dict(obj) if obj else None
    finally:
        db.close()


def get_contacto_by_email(email: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = (
            db.query(CrmContacto)
            .filter(func.lower(CrmContacto.email) == email.lower())
            .filter(CrmContacto.tenant_id == tenant_id)
            .first()
        )
        return contacto_to_dict(obj) if obj else None
    finally:
        db.close()


def create_contacto(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmContacto(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return contacto_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_contacto(tenant_id: str, contacto_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == contacto_id).first()
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return contacto_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_contacto(tenant_id: str, contacto_id: int) -> bool:
    db = get_db()
    try:
        obj = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == contacto_id).first()
        if not obj:
            return False
        oportunidad_ids = [
            row[0]
            for row in db.query(CrmOportunidad.id)
            .filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.contacto_id == contacto_id)
            .all()
        ]
        if oportunidad_ids:
            db.query(CrmActividad).filter(
                CrmActividad.tenant_id == tenant_id,
                CrmActividad.oportunidad_id.in_(oportunidad_ids),
            ).delete(synchronize_session=False)
            db.query(CrmNota).filter(
                CrmNota.tenant_id == tenant_id,
                CrmNota.oportunidad_id.in_(oportunidad_ids),
            ).delete(synchronize_session=False)
            db.query(CrmOportunidad).filter(
                CrmOportunidad.tenant_id == tenant_id,
                CrmOportunidad.id.in_(oportunidad_ids),
            ).delete(synchronize_session=False)
        db.query(CrmActividad).filter(
            CrmActividad.tenant_id == tenant_id,
            CrmActividad.contacto_id == contacto_id,
        ).delete(synchronize_session=False)
        db.query(CrmNota).filter(
            CrmNota.tenant_id == tenant_id,
            CrmNota.contacto_id == contacto_id,
        ).delete(synchronize_session=False)
        db.query(CrmContactoCampania).filter(
            CrmContactoCampania.tenant_id == tenant_id,
            CrmContactoCampania.contacto_id == contacto_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def archivar_contacto(tenant_id: str, contacto_id: int, actor: str = "") -> Optional[Dict[str, Any]]:
    from datetime import datetime
    db = get_db()
    try:
        obj = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == contacto_id).first()
        if not obj:
            return None
        obj.activo = False
        obj.archivado_en = datetime.utcnow()
        obj.archivado_por = actor
        db.commit()
        db.refresh(obj)
        return contacto_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
