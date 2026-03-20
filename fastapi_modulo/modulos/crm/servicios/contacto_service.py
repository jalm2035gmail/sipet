from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import TipoContacto
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import (
    get_contacto_by_email,
)
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import (
    create_contacto as repo_create_contacto,
    delete_contacto as repo_delete_contacto,
    get_contacto as repo_get_contacto,
    list_contactos as repo_list_contactos,
    update_contacto as repo_update_contacto,
)


def normalize_tenant_id(tenant_id: Optional[str]) -> str:
    value = str(tenant_id or "default").strip().lower()
    return value or "default"


def calculate_lead_score(data: Dict[str, Any]) -> int:
    score = 0
    if data.get("email"):
        score += 20
    if data.get("telefono"):
        score += 10
    if data.get("empresa"):
        score += 15
    if data.get("puesto"):
        score += 10
    if data.get("sucursal"):
        score += 10
    if data.get("fuente") in {"referido", "campania"}:
        score += 15
    if data.get("fuente_detalle"):
        score += 10
    if data.get("tipo") == TipoContacto.CLIENTE.value:
        score += 10
    return max(0, min(score, 100))


def list_contactos(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_contactos(normalize_tenant_id(None), tipo)


def list_contactos_by_tenant(tenant_id: Optional[str], tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_contactos(normalize_tenant_id(tenant_id), tipo)


def get_contacto(contacto_id: int, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return repo_get_contacto(normalize_tenant_id(tenant_id), contacto_id)


def create_contacto(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    if data.get("email"):
        existing = get_contacto_by_email(str(data["email"]).strip().lower(), normalized_tenant)
        if existing:
            raise ValueError("Ya existe un contacto con ese email para este tenant")
    data["tenant_id"] = normalized_tenant
    data["fuente_detalle"] = str(data.get("fuente_detalle") or "").strip()
    data["sucursal"] = str(data.get("sucursal") or "").strip()
    data["lead_score"] = calculate_lead_score(data)
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    created = repo_create_contacto(data)
    registrar_evento(
        normalized_tenant,
        entidad="contacto",
        entidad_id=created["id"],
        tipo_evento="contacto_creado",
        actor=actor,
        descripcion=f"Contacto creado: {created['nombre']}",
        payload={"contacto_id": created["id"], "email": created.get("email", "")},
    )
    return created


def update_contacto(contacto_id: int, data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_contacto(normalized_tenant, contacto_id)
    if not current:
        return None
    if data.get("email"):
        existing = get_contacto_by_email(str(data["email"]).strip().lower(), normalized_tenant)
        if existing and int(existing["id"]) != int(contacto_id):
            raise ValueError("Ya existe un contacto con ese email para este tenant")
    if "fuente_detalle" in data:
        data["fuente_detalle"] = str(data.get("fuente_detalle") or "").strip()
    if "sucursal" in data:
        data["sucursal"] = str(data.get("sucursal") or "").strip()
    data["lead_score"] = calculate_lead_score({**current, **data})
    data["actualizado_por"] = actor
    updated = repo_update_contacto(normalized_tenant, contacto_id, data)
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="contacto",
            entidad_id=updated["id"],
            tipo_evento="contacto_actualizado",
            actor=actor,
            descripcion=f"Contacto actualizado: {updated['nombre']}",
            payload={"contacto_id": updated["id"]},
        )
    return updated


def delete_contacto(contacto_id: int, tenant_id: Optional[str] = None) -> bool:
    return repo_delete_contacto(normalize_tenant_id(tenant_id), contacto_id)


def convertir_contacto_a_cliente(contacto_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    updated = repo_update_contacto(
        normalized_tenant,
        contacto_id,
        {
            "tipo": TipoContacto.CLIENTE.value,
            "lead_score": 100,
            "actualizado_por": actor,
        },
    )
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="contacto",
            entidad_id=updated["id"],
            tipo_evento="contacto_convertido_a_cliente",
            actor=actor,
            descripcion=f"Contacto convertido a cliente: {updated['nombre']}",
            payload={"contacto_id": updated["id"], "tipo": updated["tipo"]},
        )
    return updated
