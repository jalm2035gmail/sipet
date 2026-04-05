"""Análisis y métricas del pipeline comercial CRM."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import (
    ETAPAS_ABIERTAS,
    ETAPAS_CERRADAS,
    ORDEN_EMBUDO,
    EtapaOportunidad,
)
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad, CrmContacto, CrmOportunidad
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id

_DEFAULT_PROB = {
    EtapaOportunidad.NUEVO_LEAD.value: 5,
    EtapaOportunidad.POR_CONTACTAR.value: 10,
    EtapaOportunidad.CONTACTADO.value: 20,
    EtapaOportunidad.CALIFICADO.value: 30,
    EtapaOportunidad.DIAGNOSTICO.value: 40,
    EtapaOportunidad.NEGOCIACION.value: 55,
    EtapaOportunidad.PROPUESTA_ENVIADA.value: 65,
    EtapaOportunidad.SEGUIMIENTO_PROPUESTA.value: 75,
    EtapaOportunidad.DECISION.value: 85,
    EtapaOportunidad.CERRADO_GANADO.value: 100,
    EtapaOportunidad.CERRADO_PERDIDO.value: 0,
    EtapaOportunidad.PROSPECTO.value: 25,
    EtapaOportunidad.PROPUESTA.value: 60,
}


def _load_oportunidades(tenant_id: str, solo_abiertas: bool = False):
    db = get_db()
    try:
        query = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == tenant_id)
        if solo_abiertas:
            query = query.filter(CrmOportunidad.etapa.in_(list(ETAPAS_ABIERTAS)))
        return query.all()
    finally:
        db.close()


def get_pipeline_por_etapa(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Agrupa oportunidades abiertas por etapa con conteo y monto total."""
    normalized = normalize_tenant_id(tenant_id)
    oportunidades = _load_oportunidades(normalized, solo_abiertas=True)

    conteo: Dict[str, int] = {e: 0 for e in ORDEN_EMBUDO}
    monto: Dict[str, float] = {e: 0.0 for e in ORDEN_EMBUDO}
    prob_sistema: Dict[str, float] = {e: 0.0 for e in ORDEN_EMBUDO}

    for op in oportunidades:
        etapa = op.etapa
        conteo[etapa] = conteo.get(etapa, 0) + 1
        monto[etapa] = monto.get(etapa, 0.0) + float(op.valor_estimado or 0)
        ps = getattr(op, "probabilidad_sistema", None) or _DEFAULT_PROB.get(etapa, 0)
        prob_sistema[etapa] = prob_sistema.get(etapa, 0.0) + float(ps)

    resultado = []
    for etapa in ORDEN_EMBUDO:
        if not conteo.get(etapa):
            continue
        n = conteo[etapa]
        resultado.append({
            "etapa": etapa,
            "total": n,
            "monto_total": round(monto[etapa], 2),
            "probabilidad_promedio": round(prob_sistema[etapa] / n, 1) if n else 0,
            "forecast_ponderado": round(monto[etapa] * prob_sistema[etapa] / n / 100, 2) if n else 0,
        })
    return resultado


def get_pipeline_por_ejecutivo(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Pipeline abierto agrupado por ejecutivo responsable."""
    normalized = normalize_tenant_id(tenant_id)
    oportunidades = _load_oportunidades(normalized, solo_abiertas=True)

    grupos: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0, "monto_total": 0.0, "forecast": 0.0})
    for op in oportunidades:
        ej = (op.responsable or op.asignado_a or "Sin responsable").strip() or "Sin responsable"
        grupos[ej]["total"] += 1
        monto = float(op.valor_estimado or 0)
        grupos[ej]["monto_total"] += monto
        ps = float(getattr(op, "probabilidad_sistema", None) or _DEFAULT_PROB.get(op.etapa, 0))
        grupos[ej]["forecast"] += monto * ps / 100

    return [
        {
            "ejecutivo": ej,
            "total": v["total"],
            "monto_total": round(v["monto_total"], 2),
            "forecast_ponderado": round(v["forecast"], 2),
        }
        for ej, v in sorted(grupos.items(), key=lambda x: -x[1]["monto_total"])
    ]


def get_pipeline_por_sucursal(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Pipeline abierto agrupado por sucursal."""
    normalized = normalize_tenant_id(tenant_id)
    oportunidades = _load_oportunidades(normalized, solo_abiertas=True)

    grupos: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0, "monto_total": 0.0, "forecast": 0.0})
    for op in oportunidades:
        suc = (op.sucursal or "Sin sucursal").strip() or "Sin sucursal"
        grupos[suc]["total"] += 1
        monto = float(op.valor_estimado or 0)
        grupos[suc]["monto_total"] += monto
        ps = float(getattr(op, "probabilidad_sistema", None) or _DEFAULT_PROB.get(op.etapa, 0))
        grupos[suc]["forecast"] += monto * ps / 100

    return [
        {
            "sucursal": suc,
            "total": v["total"],
            "monto_total": round(v["monto_total"], 2),
            "forecast_ponderado": round(v["forecast"], 2),
        }
        for suc, v in sorted(grupos.items(), key=lambda x: -x[1]["monto_total"])
    ]


def get_forecast_ponderado(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Forecast ponderado total y por etapa usando probabilidad del sistema o manual."""
    normalized = normalize_tenant_id(tenant_id)
    oportunidades = _load_oportunidades(normalized, solo_abiertas=True)

    total_pipeline = 0.0
    total_forecast = 0.0
    por_etapa: Dict[str, float] = defaultdict(float)

    for op in oportunidades:
        monto = float(op.valor_estimado or 0)
        # Usar probabilidad_usuario si existe, sino sistema, sino base de etapa
        ps = (
            float(op.probabilidad_usuario)
            if getattr(op, "probabilidad_usuario", None) is not None
            else float(getattr(op, "probabilidad_sistema", None) or _DEFAULT_PROB.get(op.etapa, 0))
        )
        forecast = monto * ps / 100
        total_pipeline += monto
        total_forecast += forecast
        por_etapa[op.etapa] += forecast

    return {
        "total_pipeline": round(total_pipeline, 2),
        "forecast_ponderado_total": round(total_forecast, 2),
        "por_etapa": [
            {"etapa": etapa, "forecast": round(monto, 2)}
            for etapa, monto in sorted(por_etapa.items(), key=lambda x: -x[1])
        ],
    }


def get_aging_pipeline(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tiempo promedio de permanencia en la etapa actual para oportunidades abiertas."""
    normalized = normalize_tenant_id(tenant_id)
    oportunidades = _load_oportunidades(normalized, solo_abiertas=True)
    now = datetime.utcnow()

    resultado = []
    for op in oportunidades:
        ref = op.ultimo_movimiento_en or op.creado_en
        dias = max(0, (now - ref).days) if ref else 0
        resultado.append({
            "id": op.id,
            "nombre": op.nombre,
            "etapa": op.etapa,
            "responsable": (op.responsable or op.asignado_a or "Sin responsable").strip() or "Sin responsable",
            "sucursal": op.sucursal or "",
            "valor_estimado": round(float(op.valor_estimado or 0), 2),
            "dias_en_etapa": dias,
            "semaforo": "rojo" if dias >= 14 else ("amarillo" if dias >= 7 else "verde"),
        })

    resultado.sort(key=lambda x: -x["dias_en_etapa"])
    return resultado


def get_oportunidades_en_riesgo(tenant_id: Optional[str] = None, dias_inactividad: int = 14) -> List[Dict[str, Any]]:
    """Oportunidades abiertas con alto valor pero con señales de riesgo:
    - sin movimiento > dias_inactividad
    - sin actividad futura programada
    - probabilidad_sistema < 30%
    """
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        oportunidades = (
            db.query(CrmOportunidad)
            .filter(
                CrmOportunidad.tenant_id == normalized,
                CrmOportunidad.etapa.in_(list(ETAPAS_ABIERTAS)),
            )
            .all()
        )
        # IDs con actividad futura
        now = datetime.utcnow()
        acts_futuras = (
            db.query(CrmActividad.oportunidad_id)
            .filter(
                CrmActividad.tenant_id == normalized,
                CrmActividad.completada.is_(False),
                CrmActividad.fecha > now,
            )
            .distinct()
            .all()
        )
        ids_con_actividad = {r[0] for r in acts_futuras}
    finally:
        db.close()

    resultado = []
    for op in oportunidades:
        ref = op.ultimo_movimiento_en or op.creado_en
        dias = max(0, (now - ref).days) if ref else 999
        ps = float(getattr(op, "probabilidad_sistema", None) or _DEFAULT_PROB.get(op.etapa, 0))
        monto = float(op.valor_estimado or 0)

        riesgo_inactividad = dias >= dias_inactividad
        riesgo_sin_actividad = op.id not in ids_con_actividad
        riesgo_prob_baja = ps < 30

        if not (riesgo_inactividad or riesgo_sin_actividad or riesgo_prob_baja):
            continue

        factores = []
        if riesgo_inactividad:
            factores.append(f"sin movimiento {dias}d")
        if riesgo_sin_actividad:
            factores.append("sin actividad futura")
        if riesgo_prob_baja:
            factores.append(f"prob. sistema {ps}%")

        resultado.append({
            "id": op.id,
            "nombre": op.nombre,
            "etapa": op.etapa,
            "responsable": (op.responsable or op.asignado_a or "Sin responsable").strip() or "Sin responsable",
            "sucursal": op.sucursal or "",
            "valor_estimado": round(monto, 2),
            "probabilidad_sistema": ps,
            "dias_sin_movimiento": dias,
            "factores_riesgo": factores,
        })

    resultado.sort(key=lambda x: -x["valor_estimado"])
    return resultado
