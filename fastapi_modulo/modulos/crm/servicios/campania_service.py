from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import EstadoCampania
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.campania_repository import (
    add_contacto_campania as repo_add_contacto_campania,
    contacto_campania_exists,
    create_campania as repo_create_campania,
    get_campania as repo_get_campania,
    list_campanias as repo_list_campanias,
    list_contactos_campania as repo_list_contactos_campania,
    remove_contacto_campania as repo_remove_contacto_campania,
    update_campania as repo_update_campania,
)


def list_campanias(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_campanias(normalize_tenant_id(None), estado)


def list_campanias_by_tenant(tenant_id: Optional[str], estado: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_campanias(normalize_tenant_id(tenant_id), estado)


def create_campania(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    data["tenant_id"] = normalize_tenant_id(tenant_id)
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    created = repo_create_campania(data)
    registrar_evento(
        tenant_id,
        entidad="campania",
        entidad_id=created["id"],
        tipo_evento="campania_creada",
        actor=actor,
        descripcion=f"Campaña creada: {created['nombre']}",
        payload={"campania_id": created["id"]},
    )
    return created


def update_campania(campania_id: int, data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_campania(normalized_tenant, campania_id)
    if not current:
        return None
    fecha_inicio = data.get("fecha_inicio") or current.get("fecha_inicio")
    fecha_fin = data.get("fecha_fin") or current.get("fecha_fin")
    if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
        raise ValueError("La fecha fin no puede ser menor que la fecha inicio")
    data["actualizado_por"] = actor
    if data.get("estado") == EstadoCampania.FINALIZADA.value:
        data["cerrado_por"] = actor
    updated = repo_update_campania(normalized_tenant, campania_id, data)
    if updated:
        registrar_evento(
            tenant_id,
            entidad="campania",
            entidad_id=updated["id"],
            tipo_evento="campania_actualizada",
            actor=actor,
            descripcion=f"Campaña actualizada: {updated['nombre']}",
            payload={"campania_id": updated["id"], "estado": updated["estado"]},
        )
    return updated


def list_contactos_campania(campania_id: int, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_contactos_campania(normalize_tenant_id(tenant_id), campania_id)


def add_contacto_campania(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    data["tenant_id"] = normalized_tenant
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    if contacto_campania_exists(normalized_tenant, int(data["contacto_id"]), int(data["campania_id"])):
        raise ValueError("El contacto ya está asociado a la campaña")
    created = repo_add_contacto_campania(data)
    registrar_evento(
        tenant_id,
        entidad="campania",
        entidad_id=created["campania_id"],
        tipo_evento="contacto_incorporado_a_campania",
        actor=actor,
        descripcion="Contacto incorporado a campaña",
        payload={"contacto_id": created["contacto_id"], "campania_id": created["campania_id"]},
    )
    return created


def remove_contacto_de_campania(
    campania_id: int,
    contacto_id: int,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
) -> bool:
    normalized_tenant = normalize_tenant_id(tenant_id)
    removed = repo_remove_contacto_campania(normalized_tenant, campania_id, contacto_id)
    if removed:
        registrar_evento(
            normalized_tenant,
            entidad="campania",
            entidad_id=campania_id,
            tipo_evento="contacto_removido_de_campania",
            actor=actor,
            descripcion="Contacto removido de campaña",
            payload={"contacto_id": contacto_id, "campania_id": campania_id},
        )
    return removed


def duplicar_campania(campania_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_campania(normalized_tenant, campania_id)
    if not current:
        return None
    base_name = f"{current['nombre']} (copia)"
    candidate = base_name
    suffix = 2
    existing_names = {campania["nombre"] for campania in repo_list_campanias(normalized_tenant)}
    while candidate in existing_names:
        candidate = f"{base_name} {suffix}"
        suffix += 1
    created = repo_create_campania(
        {
            "tenant_id": normalized_tenant,
            "nombre": candidate,
            "tipo": current["tipo"],
            "estado": EstadoCampania.BORRADOR.value,
            "fecha_inicio": current["fecha_inicio"] or None,
            "fecha_fin": current["fecha_fin"] or None,
            "asignado_a": current.get("asignado_a", ""),
            "descripcion": current.get("descripcion") or "",
            "resultado": current.get("resultado") or "",
            "creado_por": actor,
            "actualizado_por": actor,
        }
    )
    registrar_evento(
        normalized_tenant,
        entidad="campania",
        entidad_id=created["id"],
        tipo_evento="campania_duplicada",
        actor=actor,
        descripcion=f"Campaña duplicada desde {current['nombre']}",
        payload={"campania_id": created["id"], "origen_id": campania_id},
    )
    return created


def cerrar_campania(campania_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    updated = update_campania(
        campania_id,
        {
            "estado": EstadoCampania.FINALIZADA.value,
            "cerrado_por": actor,
            "cerrado_en": datetime.utcnow(),
        },
        normalized_tenant,
        actor=actor,
    )
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="campania",
            entidad_id=updated["id"],
            tipo_evento="campania_cerrada",
            actor=actor,
            descripcion=f"Campaña cerrada: {updated['nombre']}",
            payload={"campania_id": updated["id"], "estado": updated["estado"]},
        )
    return updated


def registrar_resultado_campania(
    campania_id: int,
    resultado: str,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    updated = update_campania(
        campania_id,
        {"resultado": resultado},
        normalized_tenant,
        actor=actor,
    )
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="campania",
            entidad_id=updated["id"],
            tipo_evento="campania_resultado_registrado",
            actor=actor,
            descripcion=f"Resultado registrado para campaña: {updated['nombre']}",
            payload={"campania_id": updated["id"], "resultado": updated["resultado"]},
        )
    return updated
