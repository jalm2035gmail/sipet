from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import EtapaOportunidad
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import get_contacto as repo_get_contacto
from fastapi_modulo.modulos.crm.repositorios.oportunidad_repository import (
    create_oportunidad as repo_create_oportunidad,
    delete_oportunidad as repo_delete_oportunidad,
    get_oportunidad as repo_get_oportunidad,
    list_oportunidades as repo_list_oportunidades,
    update_oportunidad as repo_update_oportunidad,
)


STAGE_ACTIVITY_MAP = {
    EtapaOportunidad.PROSPECTO.value: "Calificar oportunidad",
    EtapaOportunidad.NEGOCIACION.value: "Seguimiento de negociación",
    EtapaOportunidad.PROPUESTA.value: "Enviar y revisar propuesta",
}


def list_oportunidades(contacto_id: Optional[int] = None, etapa: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_oportunidades(normalize_tenant_id(None), contacto_id, etapa)


def list_oportunidades_by_tenant(tenant_id: Optional[str], contacto_id: Optional[int] = None, etapa: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_oportunidades(normalize_tenant_id(tenant_id), contacto_id, etapa)


def create_oportunidad(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    contacto = repo_get_contacto(normalized_tenant, int(data["contacto_id"]))
    if not contacto:
        raise ValueError("El contacto no existe")
    data["tenant_id"] = normalized_tenant
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    data["asignado_a"] = data.get("asignado_a") or data.get("responsable") or ""
    data["sucursal"] = str(data.get("sucursal") or contacto.get("sucursal") or "").strip()
    data["ultimo_movimiento_en"] = datetime.utcnow()
    if data.get("etapa") in {
        EtapaOportunidad.CERRADO_GANADO.value,
        EtapaOportunidad.CERRADO_PERDIDO.value,
    } and not data.get("fecha_cierre_real"):
        data["fecha_cierre_real"] = date.today()
        data["cerrado_por"] = actor
    created = repo_create_oportunidad(data)
    registrar_evento(
        normalized_tenant,
        entidad="oportunidad",
        entidad_id=created["id"],
        tipo_evento="oportunidad_creada",
        actor=actor,
        descripcion=f"Oportunidad creada: {created['nombre']}",
        payload={"oportunidad_id": created["id"], "etapa": created["etapa"]},
    )
    _ensure_stage_activity(created, actor=actor)
    return created


def update_oportunidad(oportunidad_id: int, data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_oportunidad(normalized_tenant, oportunidad_id)
    if not current:
        return None
    current_stage = current.get("etapa")
    next_stage = data.get("etapa", current_stage)
    is_currently_closed = current_stage in {
        EtapaOportunidad.CERRADO_GANADO.value,
        EtapaOportunidad.CERRADO_PERDIDO.value,
    }
    is_next_closed = next_stage in {
        EtapaOportunidad.CERRADO_GANADO.value,
        EtapaOportunidad.CERRADO_PERDIDO.value,
    }
    if is_currently_closed and next_stage == current_stage:
        raise ValueError("La oportunidad está cerrada y no puede editarse sin reabrirse")
    if is_next_closed and not data.get("fecha_cierre_real") and not current.get("fecha_cierre_real"):
        data["fecha_cierre_real"] = date.today()
        data["cerrado_por"] = actor
        data["cerrado_en"] = data.get("cerrado_en") or datetime.utcnow()
    if not is_next_closed and "fecha_cierre_real" not in data and current.get("fecha_cierre_real"):
        data["fecha_cierre_real"] = None
        data["cerrado_por"] = ""
        data["cerrado_en"] = None
    if "asignado_a" not in data and data.get("responsable"):
        data["asignado_a"] = data["responsable"]
    if "sucursal" in data:
        data["sucursal"] = str(data.get("sucursal") or "").strip()
    data["ultimo_movimiento_en"] = datetime.utcnow()
    data["actualizado_por"] = actor
    updated = repo_update_oportunidad(normalized_tenant, oportunidad_id, data)
    if updated:
        if current.get("etapa") != updated.get("etapa"):
            registrar_evento(
                normalized_tenant,
                entidad="oportunidad",
                entidad_id=updated["id"],
                tipo_evento="oportunidad_etapa_cambiada",
                actor=actor,
                descripcion=f"Cambio de etapa: {current.get('etapa')} -> {updated.get('etapa')}",
                payload={"oportunidad_id": updated["id"], "anterior": current.get("etapa"), "actual": updated.get("etapa")},
            )
            _ensure_stage_activity(updated, actor=actor)
        if updated.get("etapa") in {EtapaOportunidad.CERRADO_GANADO.value, EtapaOportunidad.CERRADO_PERDIDO.value}:
            registrar_evento(
                normalized_tenant,
                entidad="oportunidad",
                entidad_id=updated["id"],
                tipo_evento="oportunidad_cerrada",
                actor=actor,
                descripcion=f"Oportunidad cerrada: {updated['nombre']}",
                payload={"oportunidad_id": updated["id"], "etapa": updated["etapa"]},
            )
    return updated


def delete_oportunidad(oportunidad_id: int, tenant_id: Optional[str] = None) -> bool:
    return repo_delete_oportunidad(normalize_tenant_id(tenant_id), oportunidad_id)


def _ensure_stage_activity(oportunidad: Dict[str, Any], *, actor: str = "") -> None:
    title = STAGE_ACTIVITY_MAP.get(oportunidad.get("etapa"))
    if not title:
        return
    from fastapi_modulo.modulos.crm.servicios.actividad_service import create_actividad

    create_actividad(
        {
            "contacto_id": oportunidad["contacto_id"],
            "oportunidad_id": oportunidad["id"],
            "tipo": "tarea",
            "titulo": title,
            "descripcion": f"Actividad automática para etapa {oportunidad['etapa']}",
            "fecha": datetime.utcnow() + timedelta(days=1),
            "responsable": oportunidad.get("responsable") or oportunidad.get("asignado_a") or actor,
        },
        oportunidad.get("tenant_id"),
        actor=actor,
    )


def cambiar_etapa_oportunidad(
    oportunidad_id: int,
    etapa: str,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    return update_oportunidad(oportunidad_id, {"etapa": etapa}, tenant_id, actor=actor)


def marcar_oportunidad_ganada(oportunidad_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    return update_oportunidad(
        oportunidad_id,
        {"etapa": EtapaOportunidad.CERRADO_GANADO.value},
        tenant_id,
        actor=actor,
    )


def marcar_oportunidad_perdida(oportunidad_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    return update_oportunidad(
        oportunidad_id,
        {"etapa": EtapaOportunidad.CERRADO_PERDIDO.value},
        tenant_id,
        actor=actor,
    )
