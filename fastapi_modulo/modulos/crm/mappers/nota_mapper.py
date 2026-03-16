from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmNota


def nota_to_dict(obj: CrmNota) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "contacto_id": obj.contacto_id,
        "oportunidad_id": obj.oportunidad_id,
        "contenido": obj.contenido,
        "autor": obj.autor,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
    }
