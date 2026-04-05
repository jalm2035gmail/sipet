from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.multiempresa.modelos.me_db_models import MeEmpresa


def empresa_dict(obj: MeEmpresa) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "codigo": obj.codigo,
        "nombre": obj.nombre,
        "tenant_id": obj.tenant_id,
        "descripcion": obj.descripcion,
        "email_contacto": obj.email_contacto,
        "telefono": obj.telefono,
        "direccion": obj.direccion,
        "rfc": obj.rfc,
        "color_primario": obj.color_primario or "#0f172a",
        "estado": obj.estado,
        "logo_filename": obj.logo_filename,
        "logo_url": f"/api/multiempresa/logos/{obj.logo_filename}" if obj.logo_filename else None,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else None,
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else None,
    }
