from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import case, func, or_

from fastapi_modulo.modulos.multiempresa.modelos.me_db_models import MeEmpresa


def find_by_id(db, empresa_id: int, tenant_filter: Optional[str] = None) -> Optional[MeEmpresa]:
    q = db.query(MeEmpresa).filter(MeEmpresa.id == empresa_id)
    if tenant_filter:
        q = q.filter(MeEmpresa.tenant_id == tenant_filter)
    return q.first()


def find_by_tenant(db, tenant_id: str) -> Optional[MeEmpresa]:
    return db.query(MeEmpresa).filter(MeEmpresa.tenant_id == tenant_id).first()


def find_all(
    db,
    tenant_filter: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    sort: str = "nombre",
    limit: int = 100,
    offset: int = 0,
) -> Tuple[int, List[MeEmpresa]]:
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
    return total, items


def aggregate_kpis(db, tenant_filter: Optional[str] = None) -> Tuple:
    q = db.query(
        func.count(MeEmpresa.id),
        func.sum(case((MeEmpresa.estado == "activa", 1), else_=0)),
        func.sum(case((MeEmpresa.logo_filename.isnot(None), 1), else_=0)),
    )
    if tenant_filter:
        q = q.filter(MeEmpresa.tenant_id == tenant_filter)
    return q.one()


def insert(db, data: Dict[str, Any]) -> MeEmpresa:
    obj = MeEmpresa(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db, obj: MeEmpresa, data: Dict[str, Any]) -> MeEmpresa:
    data["actualizado_en"] = datetime.utcnow()
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db, obj: MeEmpresa) -> None:
    db.delete(obj)
    db.commit()
