from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi_modulo.modulos.crm.modelos.db_models import CrmOportunidad


def _calcular_semaforo(ultimo_movimiento_en: Any) -> str:
    if not ultimo_movimiento_en:
        return "rojo"
    if isinstance(ultimo_movimiento_en, str):
        try:
            ultimo_movimiento_en = datetime.fromisoformat(ultimo_movimiento_en)
        except ValueError:
            return "verde"
    dias = max(0, (datetime.utcnow() - ultimo_movimiento_en).days)
    if dias >= 14:
        return "rojo"
    if dias >= 7:
        return "amarillo"
    return "verde"


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
        "monto_real": round(float(obj.monto_real), 2) if obj.monto_real is not None else None,
        "producto_vendido": obj.producto_vendido or "",
        "motivo_perdida_id": obj.motivo_perdida_id,
        "motivo_ganancia_id": obj.motivo_ganancia_id,
        "probabilidad": obj.probabilidad,
        "probabilidad_sistema": round(float(obj.probabilidad_sistema), 2) if getattr(obj, "probabilidad_sistema", None) is not None else None,
        "probabilidad_usuario": round(float(obj.probabilidad_usuario), 2) if getattr(obj, "probabilidad_usuario", None) is not None else None,
        "cerrado_por": obj.cerrado_por,
        "cerrado_en": obj.cerrado_en.isoformat() if obj.cerrado_en else "",
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "asignado_a": obj.asignado_a,
        "responsable": obj.responsable,
        "descripcion": obj.descripcion or "",
        "ultimo_movimiento_en": obj.ultimo_movimiento_en.isoformat() if obj.ultimo_movimiento_en else "",
        "semaforo": _calcular_semaforo(obj.ultimo_movimiento_en),
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else "",
        "activo": getattr(obj, "activo", True),
        "archivado_en": obj.archivado_en.isoformat() if getattr(obj, "archivado_en", None) else None,
        "archivado_por": getattr(obj, "archivado_por", None),
        "version": getattr(obj, "version", 1) or 1,
    }
