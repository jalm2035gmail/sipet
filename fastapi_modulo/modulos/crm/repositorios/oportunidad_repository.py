from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.mappers.oportunidad_mapper import oportunidad_to_dict
from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad, CrmContacto, CrmHistorialEtapa, CrmNota, CrmOportunidad
from fastapi_modulo.modulos.crm.repositorios.common import get_db


def list_oportunidades(
    tenant_id: str,
    contacto_id: Optional[int] = None,
    etapa: Optional[str] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    sucursal: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    db = get_db()
    try:
        query = db.query(CrmOportunidad, CrmContacto.nombre).outerjoin(
            CrmContacto, CrmOportunidad.contacto_id == CrmContacto.id
        ).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.activo == True)
        if contacto_id:
            query = query.filter(CrmOportunidad.contacto_id == contacto_id)
        if etapa:
            query = query.filter(CrmOportunidad.etapa == etapa)
        if q:
            pattern = f"%{q}%"
            query = query.filter(
                func.lower(CrmOportunidad.nombre).like(func.lower(pattern))
                | func.lower(CrmContacto.nombre).like(func.lower(pattern))
            )
        if responsable:
            query = query.filter(CrmOportunidad.responsable == responsable)
        if sucursal:
            query = query.filter(CrmOportunidad.sucursal == sucursal)
        total = query.count()
        rows = query.order_by(CrmOportunidad.creado_en.desc()).offset(skip).limit(limit).all()
        return {"items": [oportunidad_to_dict(obj, nombre or "") for obj, nombre in rows], "total": total, "skip": skip, "limit": limit}
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


def registrar_historial_etapa(
    tenant_id: str,
    oportunidad_id: int,
    etapa_anterior: Optional[str],
    etapa_nueva: str,
    actor: str = "",
    comentario: Optional[str] = None,
    motivo: Optional[str] = None,
) -> None:
    from datetime import datetime
    db = get_db()
    try:
        entrada = CrmHistorialEtapa(
            tenant_id=tenant_id,
            oportunidad_id=oportunidad_id,
            etapa_anterior=etapa_anterior,
            etapa_nueva=etapa_nueva,
            fecha_cambio=datetime.utcnow(),
            actor=actor,
            comentario=comentario,
            motivo=motivo,
        )
        db.add(entrada)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_historial_etapas(tenant_id: str, oportunidad_id: int) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        rows = (
            db.query(CrmHistorialEtapa)
            .filter(
                CrmHistorialEtapa.tenant_id == tenant_id,
                CrmHistorialEtapa.oportunidad_id == oportunidad_id,
            )
            .order_by(CrmHistorialEtapa.fecha_cambio.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "oportunidad_id": r.oportunidad_id,
                "etapa_anterior": r.etapa_anterior,
                "etapa_nueva": r.etapa_nueva,
                "fecha_cambio": r.fecha_cambio.isoformat() if r.fecha_cambio else "",
                "actor": r.actor,
                "comentario": r.comentario,
                "motivo": r.motivo,
            }
            for r in rows
        ]
    finally:
        db.close()


def archivar_oportunidad(tenant_id: str, oportunidad_id: int, actor: str = "") -> Optional[Dict[str, Any]]:
    from datetime import datetime
    db = get_db()
    try:
        obj = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id, CrmOportunidad.id == oportunidad_id).first()
        if not obj:
            return None
        obj.activo = False
        obj.archivado_en = datetime.utcnow()
        obj.archivado_por = actor
        db.commit()
        db.refresh(obj)
        contacto = db.query(CrmContacto).filter(CrmContacto.tenant_id == tenant_id, CrmContacto.id == obj.contacto_id).first()
        return oportunidad_to_dict(obj, contacto.nombre if contacto else "")
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
