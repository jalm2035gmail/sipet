from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.nota_mapper import nota_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmNota
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_notas(tenant_id: str, contacto_id: Optional[int] = None, oportunidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        query = db.query(CrmNota).filter(CrmNota.tenant_id == tenant_id, CrmNota.activo == True)
        if contacto_id is not None:
            query = query.filter(CrmNota.contacto_id == contacto_id)
        if oportunidad_id is not None:
            query = query.filter(CrmNota.oportunidad_id == oportunidad_id)
        return [nota_to_dict(row) for row in query.order_by(CrmNota.creado_en.desc()).all()]
    finally:
        db.close()


def create_nota(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmNota(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return nota_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_nota(tenant_id: str, nota_id: int) -> bool:
    db = get_db()
    try:
        obj = db.query(CrmNota).filter(CrmNota.tenant_id == tenant_id, CrmNota.id == nota_id).first()
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


def archivar_nota(tenant_id: str, nota_id: int, actor: str = "") -> Optional[Dict[str, Any]]:
    from datetime import datetime
    db = get_db()
    try:
        obj = db.query(CrmNota).filter(CrmNota.tenant_id == tenant_id, CrmNota.id == nota_id).first()
        if not obj:
            return None
        obj.activo = False
        obj.archivado_en = datetime.utcnow()
        obj.archivado_por = actor
        db.commit()
        db.refresh(obj)
        return nota_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
