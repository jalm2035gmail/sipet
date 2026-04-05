from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.nota_repository import (
    archivar_nota as repo_archivar_nota,
    create_nota as repo_create_nota,
    delete_nota as repo_delete_nota,
    list_notas as repo_list_notas,
)


def list_notas(contacto_id: Optional[int] = None, oportunidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
    return repo_list_notas(normalize_tenant_id(None), contacto_id, oportunidad_id)


def list_notas_by_tenant(tenant_id: Optional[str], contacto_id: Optional[int] = None, oportunidad_id: Optional[int] = None) -> List[Dict[str, Any]]:
    return repo_list_notas(normalize_tenant_id(tenant_id), contacto_id, oportunidad_id)


def create_nota(data: Dict[str, Any], tenant_id: Optional[str] = None, *, actor: str = "") -> Dict[str, Any]:
    data["tenant_id"] = normalize_tenant_id(tenant_id)
    data["creado_por"] = actor
    data["actualizado_por"] = actor
    created = repo_create_nota(data)
    registrar_evento(
        tenant_id,
        entidad="nota",
        entidad_id=created["id"],
        tipo_evento="nota_creada",
        actor=actor,
        descripcion="Nota creada",
        payload={"nota_id": created["id"]},
    )
    return created


def delete_nota(nota_id: int, tenant_id: Optional[str] = None) -> bool:
    return repo_delete_nota(normalize_tenant_id(tenant_id), nota_id)


def archivar_nota(nota_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    result = repo_archivar_nota(normalized_tenant, nota_id, actor)
    if result:
        registrar_evento(
            normalized_tenant,
            entidad="nota",
            entidad_id=nota_id,
            tipo_evento="nota_archivada",
            actor=actor,
            descripcion="Nota archivada",
            payload={"nota_id": nota_id},
        )
    return result
