from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmActividad


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
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "responsable": obj.responsable,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
    }
