from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.modelos.db_models import CrmMotivoGanancia, CrmMotivoPerdida
from fastapi_modulo.modulos.crm.repositorios.common import get_db


# ── Motivos de pérdida ──────────────────────────────────────────────────────

def list_motivos_perdida(tenant_id: str, solo_activos: bool = True) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        q = db.query(CrmMotivoPerdida).filter(CrmMotivoPerdida.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(CrmMotivoPerdida.activo.is_(True))
        return [{"id": r.id, "nombre": r.nombre, "activo": r.activo} for r in q.order_by(CrmMotivoPerdida.nombre).all()]
    finally:
        db.close()


def create_motivo_perdida(tenant_id: str, nombre: str) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmMotivoPerdida(tenant_id=tenant_id, nombre=nombre.strip())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return {"id": obj.id, "nombre": obj.nombre, "activo": obj.activo}
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_motivo_perdida(tenant_id: str, motivo_id: int) -> bool:
    """Desactiva el motivo (soft-disable) en lugar de eliminarlo."""
    db = get_db()
    try:
        obj = db.query(CrmMotivoPerdida).filter(
            CrmMotivoPerdida.tenant_id == tenant_id,
            CrmMotivoPerdida.id == motivo_id,
        ).first()
        if not obj:
            return False
        obj.activo = False
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ── Motivos de ganancia ─────────────────────────────────────────────────────

def list_motivos_ganancia(tenant_id: str, solo_activos: bool = True) -> List[Dict[str, Any]]:
    db = get_db()
    try:
        q = db.query(CrmMotivoGanancia).filter(CrmMotivoGanancia.tenant_id == tenant_id)
        if solo_activos:
            q = q.filter(CrmMotivoGanancia.activo.is_(True))
        return [{"id": r.id, "nombre": r.nombre, "activo": r.activo} for r in q.order_by(CrmMotivoGanancia.nombre).all()]
    finally:
        db.close()


def create_motivo_ganancia(tenant_id: str, nombre: str) -> Dict[str, Any]:
    db = get_db()
    try:
        obj = CrmMotivoGanancia(tenant_id=tenant_id, nombre=nombre.strip())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return {"id": obj.id, "nombre": obj.nombre, "activo": obj.activo}
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_motivo_ganancia(tenant_id: str, motivo_id: int) -> bool:
    db = get_db()
    try:
        obj = db.query(CrmMotivoGanancia).filter(
            CrmMotivoGanancia.tenant_id == tenant_id,
            CrmMotivoGanancia.id == motivo_id,
        ).first()
        if not obj:
            return False
        obj.activo = False
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
