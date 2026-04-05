from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import TipoContacto
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import (
    get_contacto_by_email,
)
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import (
    archivar_contacto as repo_archivar_contacto,
    create_contacto as repo_create_contacto,
    delete_contacto as repo_delete_contacto,
    get_contacto as repo_get_contacto,
    list_contactos as repo_list_contactos,
    update_contacto as repo_update_contacto,
)


def normalize_tenant_id(tenant_id: Optional[str]) -> str:
    value = str(tenant_id or "default").strip().lower()
    return value or "default"


def calculate_lead_score(data: Dict[str, Any], contacto_id: Optional[int] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Calcula lead_score y lead_temperatura usando scoring multicapa.

    Returns dict with 'lead_score' and 'lead_temperatura'.
    Falls back to simple profile score if no contacto_id is provided.
    """
    from fastapi_modulo.modulos.crm.servicios.lead_scoring_service import calcular_lead_score_completo
    try:
        score, temperatura = calcular_lead_score_completo(data, contacto_id, tenant_id)
    except Exception:
        # Fallback: basic profile-only score
        from fastapi_modulo.modulos.crm.servicios.lead_scoring_service import score_completitud
        score = score_completitud(data)
        from fastapi_modulo.modulos.crm.servicios.lead_scoring_service import _temperatura
        temperatura = _temperatura(score)
    return {"lead_score": score, "lead_temperatura": temperatura}


def list_contactos(tipo: Optional[str] = None, q: Optional[str] = None, responsable: Optional[str] = None, sucursal: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    return repo_list_contactos(normalize_tenant_id(None), tipo, q, responsable, sucursal, skip, limit)


def list_contactos_by_tenant(tenant_id: Optional[str], tipo: Optional[str] = None, q: Optional[str] = None, responsable: Optional[str] = None, sucursal: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    return repo_list_contactos(normalize_tenant_id(tenant_id), tipo, q, responsable, sucursal, skip, limit)


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
    scoring = calculate_lead_score(data)
    data["lead_score"] = scoring["lead_score"]
    data["lead_temperatura"] = scoring["lead_temperatura"]
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
    scoring = calculate_lead_score({**current, **data}, contacto_id=contacto_id, tenant_id=normalized_tenant)
    data["lead_score"] = scoring["lead_score"]
    data["lead_temperatura"] = scoring["lead_temperatura"]
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
            "lead_temperatura": "caliente",
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


def archivar_contacto(contacto_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    result = repo_archivar_contacto(normalized_tenant, contacto_id, actor)
    if result:
        registrar_evento(
            normalized_tenant,
            entidad="contacto",
            entidad_id=contacto_id,
            tipo_evento="contacto_archivado",
            actor=actor,
            descripcion=f"Contacto archivado: {result.get('nombre', '')}",
            payload={"contacto_id": contacto_id},
        )
    return result
