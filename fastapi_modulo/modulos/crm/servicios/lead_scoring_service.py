"""Scoring multicapa de leads: completitud + interacción + intención."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from fastapi_modulo.modulos.crm.modelos.enums import EtapaOportunidad, ORDEN_EMBUDO
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmActividad,
    CrmContactoCampania,
    CrmNota,
    CrmOportunidad,
)

# Ponderación: A=40% completitud, B=35% interacción, C=25% intención
_WEIGHT_A = 0.40
_WEIGHT_B = 0.35
_WEIGHT_C = 0.25


def score_completitud(data: Dict[str, Any]) -> int:
    """A. Score de completitud del perfil del contacto (0-100)."""
    score = 0
    if data.get("email"):
        score += 25
    if data.get("telefono"):
        score += 15
    if data.get("empresa"):
        score += 20
    if data.get("puesto"):
        score += 10
    if data.get("sucursal"):
        score += 10
    if data.get("fuente_detalle"):
        score += 10
    if data.get("fuente") in {"referido", "campania"}:
        score += 10
    return min(score, 100)


def score_interaccion(contacto_id: int, tenant_id: str) -> int:
    """B. Score de interacción comercial (0-100).

    Considera actividades realizadas/vencidas, notas, campañas y recencia.
    """
    db = get_db()
    try:
        actividades = (
            db.query(CrmActividad)
            .filter(
                CrmActividad.tenant_id == tenant_id,
                CrmActividad.contacto_id == contacto_id,
            )
            .all()
        )
        notas = (
            db.query(CrmNota)
            .filter(
                CrmNota.tenant_id == tenant_id,
                CrmNota.contacto_id == contacto_id,
            )
            .all()
        )
        campanias = (
            db.query(CrmContactoCampania)
            .filter(
                CrmContactoCampania.tenant_id == tenant_id,
                CrmContactoCampania.contacto_id == contacto_id,
            )
            .all()
        )
    finally:
        db.close()

    now = datetime.utcnow()
    completadas = [a for a in actividades if a.completada]
    vencidas = [
        a for a in actividades
        if not a.completada and a.fecha and a.fecha < now
    ]

    score = 0
    # Actividades completadas (hasta 40 pts)
    score += min(len(completadas) * 8, 40)
    # Penalización por vencidas (hasta -15 pts)
    score -= min(len(vencidas) * 3, 15)
    # Notas registradas (hasta 20 pts)
    score += min(len(notas) * 5, 20)
    # Campañas vinculadas (hasta 15 pts)
    score += min(len(campanias) * 5, 15)
    # Actividad reciente en últimos 30 días (bonus 20 pts)
    recientes = [
        a for a in completadas
        if a.fecha_completada and (now - a.fecha_completada).days <= 30
    ]
    if recientes:
        score += 20

    return max(0, min(score, 100))


def score_intencion(contacto_id: int, tenant_id: str) -> int:
    """C. Score de intención de compra (0-100).

    Considera existencia de oportunidades, etapa máxima alcanzada y monto.
    """
    db = get_db()
    try:
        oportunidades = (
            db.query(CrmOportunidad)
            .filter(
                CrmOportunidad.tenant_id == tenant_id,
                CrmOportunidad.contacto_id == contacto_id,
            )
            .all()
        )
    finally:
        db.close()

    if not oportunidades:
        return 0

    score = 0
    # Tiene al menos una oportunidad (20 pts)
    score += 20

    # Etapa máxima alcanzada en el embudo (hasta 40 pts)
    etapas_reached = {o.etapa for o in oportunidades}
    max_index = 0
    for i, etapa in enumerate(ORDEN_EMBUDO):
        if etapa in etapas_reached:
            max_index = i
    score += min(max_index * 4, 40)

    # Monto potencial (hasta 20 pts)
    max_monto = max((float(o.valor_estimado or 0) for o in oportunidades), default=0.0)
    if max_monto > 100_000:
        score += 20
    elif max_monto > 10_000:
        score += 12
    elif max_monto > 1_000:
        score += 6

    # Si ya ganó alguna oportunidad (bonus 20 pts)
    if any(o.etapa == EtapaOportunidad.CERRADO_GANADO.value for o in oportunidades):
        score += 20

    return max(0, min(score, 100))


def _temperatura(total_score: int) -> str:
    if total_score >= 61:
        return "caliente"
    if total_score >= 31:
        return "tibio"
    return "frio"


def calcular_lead_score_completo(
    data: Dict[str, Any],
    contacto_id: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> Tuple[int, str]:
    """Calcula lead_score_total y temperatura del lead.

    Returns:
        Tuple[int, str]: (score 0-100, temperatura: frio|tibio|caliente)
    """
    a = score_completitud(data)
    b = score_interaccion(contacto_id, tenant_id) if contacto_id and tenant_id else 0
    c = score_intencion(contacto_id, tenant_id) if contacto_id and tenant_id else 0
    total = round(_WEIGHT_A * a + _WEIGHT_B * b + _WEIGHT_C * c)
    total = max(0, min(total, 100))
    return total, _temperatura(total)
