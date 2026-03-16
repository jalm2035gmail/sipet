from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmEvento


def evento_to_dict(obj: CrmEvento) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "entidad": obj.entidad,
        "entidad_id": obj.entidad_id,
        "tipo_evento": obj.tipo_evento,
        "actor": obj.actor,
        "descripcion": obj.descripcion,
        "payload": obj.payload or {},
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
    }
