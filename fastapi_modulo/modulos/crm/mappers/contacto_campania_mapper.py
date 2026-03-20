from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmContactoCampania


def contacto_campania_to_dict(obj: CrmContactoCampania) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "contacto_id": obj.contacto_id,
        "campania_id": obj.campania_id,
        "estado": obj.estado,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
    }
