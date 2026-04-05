"""Servicio de analítica de campañas: atribución, ROI y KPIs."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmAtribucionCampania,
    CrmCampania,
    CrmContactoCampania,
)
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id


# ---------------------------------------------------------------------------
# Atribución
# ---------------------------------------------------------------------------

def registrar_atribucion(
    campania_id: int,
    contacto_id: int,
    tenant_id: Optional[str] = None,
    *,
    oportunidad_id: Optional[int] = None,
    etapa_alcanzada: Optional[str] = None,
    convertido: bool = False,
    monto_ganado: Optional[float] = None,
) -> Dict[str, Any]:
    """Registra (o actualiza) la atribución de un contacto a una campaña."""
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        obj = (
            db.query(CrmAtribucionCampania)
            .filter(
                CrmAtribucionCampania.tenant_id == normalized,
                CrmAtribucionCampania.campania_id == campania_id,
                CrmAtribucionCampania.contacto_id == contacto_id,
            )
            .first()
        )
        if obj:
            if etapa_alcanzada is not None:
                obj.etapa_alcanzada = etapa_alcanzada
            if convertido:
                obj.convertido = True
            if monto_ganado is not None:
                obj.monto_ganado = (obj.monto_ganado or 0.0) + monto_ganado
            if oportunidad_id is not None:
                obj.oportunidad_id = oportunidad_id
        else:
            obj = CrmAtribucionCampania(
                tenant_id=normalized,
                campania_id=campania_id,
                contacto_id=contacto_id,
                oportunidad_id=oportunidad_id,
                etapa_alcanzada=etapa_alcanzada,
                convertido=convertido,
                monto_ganado=monto_ganado,
                fecha_atribucion=datetime.utcnow(),
            )
            db.add(obj)
        db.commit()
        db.refresh(obj)
        return _atribucion_to_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def _atribucion_to_dict(obj: CrmAtribucionCampania) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "campania_id": obj.campania_id,
        "contacto_id": obj.contacto_id,
        "oportunidad_id": obj.oportunidad_id,
        "etapa_alcanzada": obj.etapa_alcanzada,
        "convertido": obj.convertido,
        "monto_ganado": obj.monto_ganado,
        "fecha_atribucion": obj.fecha_atribucion.isoformat() if obj.fecha_atribucion else "",
    }


# ---------------------------------------------------------------------------
# KPIs y ROI
# ---------------------------------------------------------------------------

def get_kpis_campania(campania_id: int, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Calcula los KPIs y ROI de una campaña."""
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        campania = (
            db.query(CrmCampania)
            .filter(CrmCampania.tenant_id == normalized, CrmCampania.id == campania_id)
            .first()
        )
        if not campania:
            return {}

        # Contactos en campaña
        total_contactos = (
            db.query(CrmContactoCampania)
            .filter(
                CrmContactoCampania.tenant_id == normalized,
                CrmContactoCampania.campania_id == campania_id,
            )
            .count()
        )

        contactados = (
            db.query(CrmContactoCampania)
            .filter(
                CrmContactoCampania.tenant_id == normalized,
                CrmContactoCampania.campania_id == campania_id,
                CrmContactoCampania.estado != "pendiente",
            )
            .count()
        )

        # Atribución
        atribuciones: List[CrmAtribucionCampania] = (
            db.query(CrmAtribucionCampania)
            .filter(
                CrmAtribucionCampania.tenant_id == normalized,
                CrmAtribucionCampania.campania_id == campania_id,
            )
            .all()
        )

        oportunidades_abiertas = sum(
            1 for a in atribuciones if not a.convertido and a.oportunidad_id is not None
        )
        convertidos = sum(1 for a in atribuciones if a.convertido)
        monto_ganado_total = sum(a.monto_ganado or 0.0 for a in atribuciones)

        # ROI
        costo = campania.costo_campania or 0.0
        roi: Optional[float] = None
        if costo > 0:
            roi = round((monto_ganado_total - costo) / costo * 100, 2)

        tasa_respuesta = round(contactados / total_contactos * 100, 2) if total_contactos else 0.0
        tasa_conversion = round(convertidos / total_contactos * 100, 2) if total_contactos else 0.0

        return {
            "campania_id": campania_id,
            "nombre": campania.nombre,
            "tipo_objetivo": campania.tipo_objetivo or "",
            "estado": campania.estado,
            "leads_generados": total_contactos,
            "leads_contactados": contactados,
            "oportunidades_abiertas": oportunidades_abiertas,
            "convertidos": convertidos,
            "monto_ganado": monto_ganado_total,
            "costo_campania": costo,
            "roi_porcentaje": roi,
            "tasa_respuesta": tasa_respuesta,
            "tasa_conversion": tasa_conversion,
        }
    finally:
        db.close()


def list_atribuciones(campania_id: int, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todas las atribuciones de una campaña."""
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        rows = (
            db.query(CrmAtribucionCampania)
            .filter(
                CrmAtribucionCampania.tenant_id == normalized,
                CrmAtribucionCampania.campania_id == campania_id,
            )
            .order_by(CrmAtribucionCampania.fecha_atribucion.desc())
            .all()
        )
        return [_atribucion_to_dict(r) for r in rows]
    finally:
        db.close()
