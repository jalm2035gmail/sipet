from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmOportunidad


def oportunidad_to_dict(obj: CrmOportunidad, contacto_nombre: str = "") -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "contacto_id": obj.contacto_id,
        "contacto_nombre": contacto_nombre,
        "nombre": obj.nombre,
        "sucursal": obj.sucursal,
        "etapa": obj.etapa,
        "valor_estimado": round(float(obj.valor_estimado or 0), 2),
        "probabilidad": obj.probabilidad,
        "fecha_cierre_est": obj.fecha_cierre_est.isoformat() if obj.fecha_cierre_est else "",
        "fecha_cierre_real": obj.fecha_cierre_real.isoformat() if obj.fecha_cierre_real else "",
        "cerrado_por": obj.cerrado_por,
        "cerrado_en": obj.cerrado_en.isoformat() if obj.cerrado_en else "",
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "responsable": obj.responsable,
        "descripcion": obj.descripcion or "",
        "ultimo_movimiento_en": obj.ultimo_movimiento_en.isoformat() if obj.ultimo_movimiento_en else "",
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else "",
    }
