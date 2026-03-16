from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmCampania


def campania_to_dict(obj: CrmCampania) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "nombre": obj.nombre,
        "tipo": obj.tipo,
        "estado": obj.estado,
        "fecha_inicio": obj.fecha_inicio.isoformat() if obj.fecha_inicio else "",
        "fecha_fin": obj.fecha_fin.isoformat() if obj.fecha_fin else "",
        "cerrado_por": obj.cerrado_por,
        "cerrado_en": obj.cerrado_en.isoformat() if obj.cerrado_en else "",
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "descripcion": obj.descripcion or "",
        "resultado": obj.resultado or "",
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
    }
