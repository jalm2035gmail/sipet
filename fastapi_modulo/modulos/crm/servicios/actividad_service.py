from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.actividad_repository import (
    contacto_exists,
    create_actividad as repo_create_actividad,
    delete_actividad as repo_delete_actividad,
    get_actividad as repo_get_actividad,
    list_actividades as repo_list_actividades,
    oportunidad_exists,
    update_actividad as repo_update_actividad,
)


def list_actividades(
    contacto_id: Optional[int] = None,
    oportunidad_id: Optional[int] = None,
    completada: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    return repo_list_actividades(normalize_tenant_id(None), contacto_id, oportunidad_id, completada)


def list_actividades_by_tenant(
    tenant_id: Optional[str],
    contacto_id: Optional[int] = None,
    oportunidad_id: Optional[int] = None,
    completada: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    return repo_list_actividades(normalize_tenant_id(tenant_id), contacto_id, oportunidad_id, completada)


def create_actividad(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    data["tenant_id"] = normalized_tenant
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    data["asignado_a"] = data.get("asignado_a") or data.get("responsable") or ""
    if data.get("contacto_id") is None and data.get("oportunidad_id") is None:
        raise ValueError("La actividad requiere contacto u oportunidad")
    if data.get("fecha") is None:
        raise ValueError("La actividad requiere fecha")
    if data.get("contacto_id") is not None and not contacto_exists(normalized_tenant, int(data["contacto_id"])):
        raise ValueError("El contacto no existe")
    if data.get("oportunidad_id") is not None and not oportunidad_exists(normalized_tenant, int(data["oportunidad_id"])):
        raise ValueError("La oportunidad no existe")
    if data.get("completada") and not data.get("fecha_completada"):
        data["fecha_completada"] = datetime.utcnow()
    created = repo_create_actividad(data)
    registrar_evento(
        normalized_tenant,
        entidad="actividad",
        entidad_id=created["id"],
        tipo_evento="actividad_creada",
        actor=actor,
        descripcion=f"Actividad creada: {created['titulo']}",
        payload={"actividad_id": created["id"], "tipo": created["tipo"]},
    )
    return created


def update_actividad(actividad_id: int, data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_actividad(normalized_tenant, actividad_id)
    if not current:
        return None
    if data.get("fecha") is None and "fecha" in data:
        raise ValueError("La actividad requiere fecha")
    completed = data.get("completada")
    if completed is True and not data.get("fecha_completada"):
        data["fecha_completada"] = datetime.utcnow()
    if completed is False:
        data["fecha_completada"] = None
    if "asignado_a" not in data and data.get("responsable"):
        data["asignado_a"] = data["responsable"]
    data["actualizado_por"] = actor
    updated = repo_update_actividad(normalized_tenant, actividad_id, data)
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="actividad",
            entidad_id=updated["id"],
            tipo_evento="actividad_actualizada" if current.get("completada") == updated.get("completada") else "actividad_completada",
            actor=actor,
            descripcion=f"Actividad actualizada: {updated['titulo']}",
            payload={"actividad_id": updated["id"], "completada": updated["completada"]},
        )
    return updated


def delete_actividad(actividad_id: int, tenant_id: Optional[str] = None) -> bool:
    return repo_delete_actividad(normalize_tenant_id(tenant_id), actividad_id)


def completar_actividad(actividad_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    return update_actividad(actividad_id, {"completada": True}, tenant_id, actor=actor)


def reprogramar_actividad(
    actividad_id: int,
    fecha: datetime,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    updated = update_actividad(
        actividad_id,
        {"fecha": fecha, "completada": False, "fecha_completada": None},
        normalized_tenant,
        actor=actor,
    )
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="actividad",
            entidad_id=updated["id"],
            tipo_evento="actividad_reprogramada",
            actor=actor,
            descripcion=f"Actividad reprogramada: {updated['titulo']}",
            payload={"actividad_id": updated["id"], "fecha": updated["fecha"]},
        )
    return updated


def list_actividades_vencidas(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        actividad
        for actividad in list_actividades_by_tenant(tenant_id, completada=False)
        if actividad.get("fecha") and datetime.fromisoformat(actividad["fecha"]) < now
    ]
