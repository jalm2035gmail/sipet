from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad
from fastapi_modulo.modulos.crm.modelos.enums import EstadoActividad


def _calcular_estado(obj: CrmActividad) -> str:
    """Devuelve el estado efectivo: si ya tiene estado explícito lo usa,
    si está completada sin estado explícito devuelve completada,
    si está vencida (fecha < now y no completada) fuerza vencida."""
    estado = getattr(obj, "estado", None) or EstadoActividad.PENDIENTE.value
    if estado in {EstadoActividad.COMPLETADA.value, EstadoActividad.CANCELADA.value}:
        return estado
    if not obj.completada and obj.fecha and obj.fecha < datetime.utcnow():
        return EstadoActividad.VENCIDA.value
    if obj.completada and estado == EstadoActividad.PENDIENTE.value:
        return EstadoActividad.COMPLETADA.value
    return estado


def actividad_to_dict(obj: CrmActividad) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "contacto_id": obj.contacto_id,
        "oportunidad_id": obj.oportunidad_id,
        "tipo": obj.tipo,
        "titulo": obj.titulo,
        "descripcion": obj.descripcion or "",
        "fecha": obj.fecha.isoformat() if obj.fecha else "",
        "completada": obj.completada,
        "fecha_completada": obj.fecha_completada.isoformat() if obj.fecha_completada else "",
        "prioridad": getattr(obj, "prioridad", "media") or "media",
        "estado": _calcular_estado(obj),
        "tipo_resultado": getattr(obj, "tipo_resultado", None),
        "sla_horas": getattr(obj, "sla_horas", None),
        "siguiente_accion": getattr(obj, "siguiente_accion", None),
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "responsable": obj.responsable,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
        "activo": getattr(obj, "activo", True),
        "archivado_en": obj.archivado_en.isoformat() if getattr(obj, "archivado_en", None) else None,
        "archivado_por": getattr(obj, "archivado_por", None),
    }
