from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.oportunidad_mapper import oportunidad_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad, CrmContacto, CrmNota, CrmOportunidad
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_oportunidades(tenant_id: str, contacto_id: Optional[int] = None, etapa: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        query = db.query(CrmOportunidad, CrmContacto.nombre).outerjoin(
            CrmContacto, CrmOportunidad.contacto_id == CrmContacto.id
        ).filter(CrmOportunidad.tenant_id == tenant_id)
        if contacto_id:
            query = query.filter(CrmOportunidad.contacto_id == contacto_id)
        if etapa:
            query = query.filter(CrmOportunidad.etapa == etapa)
        return [oportunidad_to_dict(obj, nombre or "") for obj, nombre in query.order_by(CrmOportunidad.creado_en.desc()).all()]
    finally:
        db.close()


def create_oportunidad(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmOportunidad(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        contacto = db.query(CrmContacto).filter(CrmContacto.tenant_id == obj.tenant_id, CrmContacto.id == obj.contacto_id).first()
        return oportunidad_to_dict(obj, contacto.nombre if contacto else "")
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_oportunidad(tenant_id: str, oportunidad_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.id == oportunidad_id).first()
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        contacto = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == obj.contacto_id).first()
        return oportunidad_to_dict(obj, contacto.nombre if contacto else "")
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_oportunidad(tenant_id: str, oportunidad_id: int) -> bool:
    db = get_db()
    try:
        obj = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.id == oportunidad_id).first()
        if not obj:
            return False
        db.query(CrmActividad).filter(
            CrmActividad.tenant_id == tenant_id,
            CrmActividad.oportunidad_id == oportunidad_id,
        ).delete(synchronize_session=False)
        db.query(CrmNota).filter(
            CrmNota.tenant_id == tenant_id,
            CrmNota.oportunidad_id == oportunidad_id,
        ).delete(synchronize_session=False)
        db.delete(obj)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_oportunidad(tenant_id: str, oportunidad_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        obj = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.id == oportunidad_id).first()
        if not obj:
            return None
        contacto = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == obj.contacto_id).first()
        return oportunidad_to_dict(obj, contacto.nombre if contacto else "")
    finally:
        db.close()
