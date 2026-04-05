from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.evento_mapper import evento_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmEvento
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def create_evento(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmEvento(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return evento_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_eventos(
    tenant_id: str,
    entidad: Optional[str] = None,
    entidad_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        query = db.query(CrmEvento).filter(CrmEvento.tenant_id == tenant_id)
        if entidad:
            query = query.filter(CrmEvento.entidad == entidad)
        if entidad_id is not None:
            query = query.filter(CrmEvento.entidad_id == entidad_id)
        rows = query.order_by(CrmEvento.creado_en.desc()).limit(max(1, min(limit, 200))).all()
        return [evento_to_dict(row) for row in rows]
    finally:
        db.close()
