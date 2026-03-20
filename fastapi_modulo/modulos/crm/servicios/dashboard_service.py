from __future__ import annotations

import os
from collections import defaultdict
from datetime import date, datetime, time
from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmActividad,
    CrmCampania,
    CrmContacto,
    CrmContactoCampania,
    CrmEvento,
    CrmNota,
    CrmOportunidad,
)
from fastapi_modulo.modulos.crm.modelos.enums import EstadoCampania, EtapaOportunidad
from fastapi_modulo.modulos.crm.repositorios.common import ensure_crm_schema, get_db
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id


DEFAULT_STAGE_PROBABILITY = {
    EtapaOportunidad.PROSPECTO.value: 25,
    EtapaOportunidad.NEGOCIACION.value: 60,
    EtapaOportunidad.PROPUESTA.value: 80,
}


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def get_crm_resumen(tenant_id: str | None = None) -> Dict[str, Any]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    ensure_crm_schema()
    db = get_db()
    try:
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)

        contactos = db.query(CrmContacto).filter(CrmContacto.tenant_id == normalized_tenant).all()
        oportunidades = db.query(CrmOportunidad).filter(CrmOportunidad.tenant_id == normalized_tenant).all()
        actividades = db.query(CrmActividad).filter(CrmActividad.tenant_id == normalized_tenant).all()
        campanias = db.query(CrmCampania).filter(CrmCampania.tenant_id == normalized_tenant).all()
        contacto_campanias = db.query(CrmContactoCampania).filter(CrmContactoCampania.tenant_id == normalized_tenant).all()
        notas = db.query(CrmNota).filter(CrmNota.tenant_id == normalized_tenant).all()
        eventos = db.query(CrmEvento).filter(CrmEvento.tenant_id == normalized_tenant).order_by(CrmEvento.creado_en.desc()).limit(20).all()

        open_stages = {
            EtapaOportunidad.PROSPECTO.value,
            EtapaOportunidad.NEGOCIACION.value,
            EtapaOportunidad.PROPUESTA.value,
        }
        won_stage = EtapaOportunidad.CERRADO_GANADO.value
        lost_stage = EtapaOportunidad.CERRADO_PERDIDO.value

        total_contactos = len(contactos)
        meta_ventas_periodo = round(float(os.environ.get("CRM_SALES_TARGET", "100000")), 2)
        oportunidades_abiertas = [o for o in oportunidades if o.etapa in open_stages]
        oportunidades_ganadas = [o for o in oportunidades if o.etapa == won_stage]
        oportunidades_perdidas = [o for o in oportunidades if o.etapa == lost_stage]
        actividades_pendientes_rows = [a for a in actividades if not a.completada]
        campanias_activas = [c for c in campanias if c.estado == EstadoCampania.ACTIVA.value]
        clientes_count = sum(1 for contacto in contactos if contacto.tipo == "cliente")
        total_pipeline_monto = round(sum(float(o.valor_estimado or 0) for o in oportunidades_abiertas), 2)
        valor_ganado_periodo = round(
            sum(
                float(o.valor_estimado or 0)
                for o in oportunidades_ganadas
                if (_coerce_datetime(o.cerrado_en) or datetime.min) >= period_start
            ),
            2,
        )
        actividades_vencidas = sum(
            1
            for actividad in actividades_pendientes_rows
            if (_coerce_datetime(actividad.fecha) or datetime.max) < now
        )
        actividades_proximas = [
            (actividad, fecha_dt)
            for actividad in actividades_pendientes_rows
            for fecha_dt in [_coerce_datetime(actividad.fecha)]
            if fecha_dt and fecha_dt >= now
        ]
        actividades_proximas.sort(key=lambda item: item[1])
        proximos_vencimientos = [
            {
                "actividad_id": actividad.id,
                "titulo": actividad.titulo,
                "fecha": fecha_dt.isoformat() if fecha_dt else "",
                "responsable": (actividad.responsable or actividad.asignado_a or "Sin responsable").strip() or "Sin responsable",
            }
            for actividad, fecha_dt in actividades_proximas[:5]
        ]
        recordatorios_seguimiento = [
            item for item in proximos_vencimientos
            if (_coerce_datetime(item["fecha"]) or datetime.max)
            <= now.replace(hour=23, minute=59, second=59, microsecond=0)
        ]

        monto_por_etapa_raw: dict[str, float] = defaultdict(float)
        for oportunidad in oportunidades:
            monto_por_etapa_raw[oportunidad.etapa] += float(oportunidad.valor_estimado or 0)
        monto_por_etapa = [
            {"etapa": etapa, "monto": round(monto, 2)}
            for etapa, monto in sorted(monto_por_etapa_raw.items())
        ]
        embudo_comercial = [
            {"etapa": EtapaOportunidad.PROSPECTO.value, "total": sum(1 for o in oportunidades if o.etapa == EtapaOportunidad.PROSPECTO.value)},
            {"etapa": EtapaOportunidad.NEGOCIACION.value, "total": sum(1 for o in oportunidades if o.etapa == EtapaOportunidad.NEGOCIACION.value)},
            {"etapa": EtapaOportunidad.PROPUESTA.value, "total": sum(1 for o in oportunidades if o.etapa == EtapaOportunidad.PROPUESTA.value)},
            {"etapa": won_stage, "total": len(oportunidades_ganadas)},
            {"etapa": lost_stage, "total": len(oportunidades_perdidas)},
        ]

        actividades_por_responsable_raw: dict[str, int] = defaultdict(int)
        for actividad in actividades_pendientes_rows:
            responsable = (actividad.responsable or actividad.asignado_a or "Sin responsable").strip() or "Sin responsable"
            actividades_por_responsable_raw[responsable] += 1
        actividades_por_responsable = [
            {"responsable": responsable, "total": total}
            for responsable, total in sorted(
                actividades_por_responsable_raw.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

        contactos_por_fuente_raw: dict[str, int] = defaultdict(int)
        for contacto in contactos:
            contactos_por_fuente_raw[contacto.fuente or "sin_fuente"] += 1
        contactos_por_fuente = [
            {"fuente": fuente, "total": total}
            for fuente, total in sorted(
                contactos_por_fuente_raw.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]
        origen_leads_detallado_raw: dict[str, int] = defaultdict(int)
        for contacto in contactos:
            origen = (contacto.fuente_detalle or contacto.fuente or "sin_fuente").strip() or "sin_fuente"
            origen_leads_detallado_raw[origen] += 1
        origen_leads_detallado = [
            {"origen": origen, "total": total}
            for origen, total in sorted(origen_leads_detallado_raw.items(), key=lambda item: (-item[1], item[0]))
        ]

        pipeline_por_sucursal_raw: dict[str, float] = defaultdict(float)
        pipeline_por_ejecutivo_raw: dict[str, float] = defaultdict(float)
        oportunidades_sin_movimiento = []
        for oportunidad in oportunidades_abiertas:
            sucursal = (oportunidad.sucursal or "Sin sucursal").strip() or "Sin sucursal"
            ejecutivo = (oportunidad.responsable or oportunidad.asignado_a or "Sin responsable").strip() or "Sin responsable"
            pipeline_por_sucursal_raw[sucursal] += float(oportunidad.valor_estimado or 0)
            pipeline_por_ejecutivo_raw[ejecutivo] += float(oportunidad.valor_estimado or 0)
            ref_date = _coerce_datetime(
                oportunidad.ultimo_movimiento_en or oportunidad.actualizado_en or oportunidad.creado_en
            )
            days = max(0, (now - ref_date).days) if ref_date else 0
            semaforo = "verde"
            if days >= 14:
                semaforo = "rojo"
            elif days >= 7:
                semaforo = "amarillo"
            oportunidades_sin_movimiento.append(
                {
                    "oportunidad_id": oportunidad.id,
                    "nombre": oportunidad.nombre,
                    "responsable": ejecutivo,
                    "dias": days,
                    "semaforo": semaforo,
                }
            )
        pipeline_por_sucursal = [
            {"sucursal": sucursal, "monto": round(monto, 2)}
            for sucursal, monto in sorted(pipeline_por_sucursal_raw.items(), key=lambda item: (-item[1], item[0]))
        ]
        pipeline_por_ejecutivo = [
            {"ejecutivo": ejecutivo, "monto": round(monto, 2)}
            for ejecutivo, monto in sorted(pipeline_por_ejecutivo_raw.items(), key=lambda item: (-item[1], item[0]))
        ]
        oportunidades_sin_movimiento.sort(key=lambda item: (-item["dias"], item["nombre"]))

        scoring_leads = [
            {
                "contacto_id": contacto.id,
                "nombre": contacto.nombre,
                "score": int(contacto.lead_score or 0),
                "sucursal": contacto.sucursal or "",
            }
            for contacto in sorted(contactos, key=lambda item: (-int(item.lead_score or 0), item.nombre))[:5]
        ]

        observaciones_cronologicas = [
            {
                "tipo": "nota",
                "fecha": nota.creado_en.isoformat() if nota.creado_en else "",
                "descripcion": nota.contenido,
                "autor": nota.autor or nota.creado_por or "",
            }
            for nota in sorted(
                notas,
                key=lambda item: _coerce_datetime(item.creado_en) or datetime.min,
                reverse=True,
            )[:10]
        ]
        historial_cambios = [
            {
                "tipo": evento.tipo_evento,
                "fecha": evento.creado_en.isoformat() if evento.creado_en else "",
                "descripcion": evento.descripcion,
                "actor": evento.actor,
            }
            for evento in eventos
        ]

        responsables_cierre_raw: dict[str, dict[str, float]] = defaultdict(lambda: {"cierres": 0, "monto": 0.0})
        for oportunidad in oportunidades_ganadas:
            responsable = (oportunidad.cerrado_por or oportunidad.responsable or oportunidad.asignado_a or "Sin responsable").strip() or "Sin responsable"
            responsables_cierre_raw[responsable]["cierres"] += 1
            responsables_cierre_raw[responsable]["monto"] += float(oportunidad.valor_estimado or 0)
        top_responsables_por_cierre = [
            {
                "responsable": responsable,
                "cierres": int(data["cierres"]),
                "monto": round(float(data["monto"]), 2),
            }
            for responsable, data in sorted(
                responsables_cierre_raw.items(),
                key=lambda item: (-item[1]["cierres"], -item[1]["monto"], item[0]),
            )
        ]
        dashboard_por_asesor_raw: dict[str, dict[str, float]] = defaultdict(lambda: {"pipeline": 0.0, "ganado": 0.0, "oportunidades": 0})
        dashboard_por_sucursal_raw: dict[str, dict[str, float]] = defaultdict(lambda: {"pipeline": 0.0, "ganado": 0.0, "oportunidades": 0})
        for oportunidad in oportunidades:
            asesor = (oportunidad.responsable or oportunidad.asignado_a or "Sin responsable").strip() or "Sin responsable"
            sucursal = (oportunidad.sucursal or "Sin sucursal").strip() or "Sin sucursal"
            if oportunidad.etapa in open_stages:
                dashboard_por_asesor_raw[asesor]["pipeline"] += float(oportunidad.valor_estimado or 0)
                dashboard_por_sucursal_raw[sucursal]["pipeline"] += float(oportunidad.valor_estimado or 0)
            if oportunidad.etapa == won_stage:
                dashboard_por_asesor_raw[asesor]["ganado"] += float(oportunidad.valor_estimado or 0)
                dashboard_por_sucursal_raw[sucursal]["ganado"] += float(oportunidad.valor_estimado or 0)
            dashboard_por_asesor_raw[asesor]["oportunidades"] += 1
            dashboard_por_sucursal_raw[sucursal]["oportunidades"] += 1
        dashboard_por_asesor = [
            {
                "asesor": asesor,
                "pipeline": round(data["pipeline"], 2),
                "ganado": round(data["ganado"], 2),
                "oportunidades": int(data["oportunidades"]),
            }
            for asesor, data in sorted(dashboard_por_asesor_raw.items(), key=lambda item: (-item[1]["pipeline"], -item[1]["ganado"], item[0]))
        ]
        dashboard_por_sucursal = [
            {
                "sucursal": sucursal,
                "pipeline": round(data["pipeline"], 2),
                "ganado": round(data["ganado"], 2),
                "oportunidades": int(data["oportunidades"]),
            }
            for sucursal, data in sorted(dashboard_por_sucursal_raw.items(), key=lambda item: (-item[1]["pipeline"], -item[1]["ganado"], item[0]))
        ]

        oportunidades_por_contacto: dict[int, list[CrmOportunidad]] = defaultdict(list)
        for oportunidad in oportunidades:
            oportunidades_por_contacto[int(oportunidad.contacto_id or 0)].append(oportunidad)

        campanias_por_efectividad = []
        tasa_cierre_por_campania = []
        dashboard_por_campania = []
        for campania in campanias:
            relaciones = [row for row in contacto_campanias if row.campania_id == campania.id]
            total_relaciones = len(relaciones)
            contactados = sum(1 for row in relaciones if row.estado == "contactado")
            convertidos = sum(1 for row in relaciones if row.estado == "convertido")
            efectividad = round((convertidos / total_relaciones) * 100, 2) if total_relaciones else 0.0
            campanias_por_efectividad.append(
                {
                    "campania_id": campania.id,
                    "nombre": campania.nombre,
                    "contactos": total_relaciones,
                    "contactados": contactados,
                    "convertidos": convertidos,
                    "efectividad": efectividad,
                }
            )

            campania_oportunidades = []
            seen = set()
            for relacion in relaciones:
                for oportunidad in oportunidades_por_contacto.get(int(relacion.contacto_id or 0), []):
                    if oportunidad.id in seen:
                        continue
                    seen.add(oportunidad.id)
                    campania_oportunidades.append(oportunidad)
            total_ops = len(campania_oportunidades)
            won_ops = sum(1 for oportunidad in campania_oportunidades if oportunidad.etapa == won_stage)
            tasa_cierre = round((won_ops / total_ops) * 100, 2) if total_ops else 0.0
            tasa_cierre_por_campania.append(
                {
                    "campania_id": campania.id,
                    "nombre": campania.nombre,
                    "oportunidades": total_ops,
                    "ganadas": won_ops,
                    "tasa_cierre": tasa_cierre,
                }
            )
            dashboard_por_campania.append(
                {
                    "campania_id": campania.id,
                    "nombre": campania.nombre,
                    "efectividad": efectividad,
                    "tasa_cierre": tasa_cierre,
                    "contactos": total_relaciones,
                }
            )

        campanias_por_efectividad.sort(key=lambda item: (-item["efectividad"], -item["convertidos"], item["nombre"]))
        tasa_cierre_por_campania.sort(key=lambda item: (-item["tasa_cierre"], -item["ganadas"], item["nombre"]))
        dashboard_por_campania.sort(key=lambda item: (-item["efectividad"], -item["tasa_cierre"], item["nombre"]))
        forecast_periodo = round(
            sum(
                float(o.valor_estimado or 0)
                * (
                    float(
                        o.probabilidad
                        if float(o.probabilidad or 0) > 0
                        else DEFAULT_STAGE_PROBABILITY.get(o.etapa, 0)
                    ) / 100.0
                )
                for o in oportunidades_abiertas
            ),
            2,
        )
        avance_meta_ventas = round((valor_ganado_periodo / meta_ventas_periodo) * 100, 2) if meta_ventas_periodo else 0.0

        return {
            "total_contactos": total_contactos,
            "total_oportunidades": len(oportunidades),
            "oportunidades_abiertas": len(oportunidades_abiertas),
            "actividades_pendientes": len(actividades_pendientes_rows),
            "campanias_activas": len(campanias_activas),
            "meta_ventas_periodo": meta_ventas_periodo,
            "avance_meta_ventas": avance_meta_ventas,
            "total_pipeline_monto": total_pipeline_monto,
            "forecast_periodo": forecast_periodo,
            "monto_por_etapa": monto_por_etapa,
            "embudo_comercial": embudo_comercial,
            "tasa_conversion_prospecto_cliente": round((clientes_count / total_contactos) * 100, 2) if total_contactos else 0.0,
            "oportunidades_ganadas": len(oportunidades_ganadas),
            "oportunidades_perdidas": len(oportunidades_perdidas),
            "valor_ganado_periodo": valor_ganado_periodo,
            "actividades_vencidas": actividades_vencidas,
            "actividades_por_responsable": actividades_por_responsable,
            "contactos_por_fuente": contactos_por_fuente,
            "origen_leads_detallado": origen_leads_detallado,
            "campanias_por_efectividad": campanias_por_efectividad,
            "top_responsables_por_cierre": top_responsables_por_cierre,
            "tasa_cierre_por_campania": tasa_cierre_por_campania,
            "pipeline_por_sucursal": pipeline_por_sucursal,
            "pipeline_por_ejecutivo": pipeline_por_ejecutivo,
            "dashboard_por_asesor": dashboard_por_asesor,
            "dashboard_por_sucursal": dashboard_por_sucursal,
            "dashboard_por_campania": dashboard_por_campania,
            "oportunidades_sin_movimiento": oportunidades_sin_movimiento[:5],
            "scoring_leads": scoring_leads,
            "recordatorios_seguimiento": recordatorios_seguimiento,
            "proximos_vencimientos": proximos_vencimientos,
            "observaciones_cronologicas": observaciones_cronologicas,
            "historial_cambios": historial_cambios,
        }
    finally:
        db.close()
