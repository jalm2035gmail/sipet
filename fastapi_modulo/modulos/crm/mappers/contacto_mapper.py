from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmContacto


def contacto_to_dict(obj: CrmContacto) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "nombre": obj.nombre,
        "email": obj.email or "",
        "telefono": obj.telefono,
        "empresa": obj.empresa,
        "puesto": obj.puesto,
        "sucursal": obj.sucursal,
        "tipo": obj.tipo,
        "fuente": obj.fuente,
        "fuente_detalle": obj.fuente_detalle,
        "lead_score": obj.lead_score,
        "lead_temperatura": getattr(obj, "lead_temperatura", None) or "frio",
        "notas": obj.notas or "",
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else "",
        "activo": getattr(obj, "activo", True),
        "archivado_en": obj.archivado_en.isoformat() if getattr(obj, "archivado_en", None) else None,
        "archivado_por": getattr(obj, "archivado_por", None),
    }
