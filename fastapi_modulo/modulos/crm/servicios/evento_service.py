from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.repositorios.evento_repository import create_evento as repo_create_evento, list_eventos as repo_list_eventos


def _normalize_tenant_id(tenant_id: Optional[str]) -> str:
    value = str(tenant_id or "default").strip().lower()
    return value or "default"


def registrar_evento(
    tenant_id: Optional[str],
    *,
    entidad: str,
    entidad_id: Optional[int],
    tipo_evento: str,
    actor: str,
    descripcion: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return repo_create_evento(
        {
            "tenant_id": _normalize_tenant_id(tenant_id),
            "entidad": entidad,
            "entidad_id": entidad_id,
            "tipo_evento": tipo_evento,
            "actor": str(actor or "").strip(),
            "descripcion": descripcion,
            "payload": payload or {},
        }
    )


def list_eventos_by_tenant(
    tenant_id: Optional[str],
    *,
    entidad: Optional[str] = None,
    entidad_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    return repo_list_eventos(_normalize_tenant_id(tenant_id), entidad, entidad_id, limit)


def list_seguimiento_by_tenant(
    tenant_id: Optional[str],
    *,
    contacto_id: Optional[int] = None,
    oportunidad_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    normalized_tenant = _normalize_tenant_id(tenant_id)
    from fastapi_modulo.modulos.crm.servicios.nota_service import list_notas_by_tenant

    eventos = repo_list_eventos(normalized_tenant, None, oportunidad_id or contacto_id, limit)
    notas = list_notas_by_tenant(normalized_tenant, contacto_id=contacto_id, oportunidad_id=oportunidad_id)
    rows: List[Dict[str, Any]] = []
    for evento in eventos:
        payload = evento.get("payload") or {}
        if contacto_id and payload.get("contacto_id") not in {None, contacto_id} and evento.get("entidad_id") != contacto_id:
            continue
        if oportunidad_id and payload.get("oportunidad_id") not in {None, oportunidad_id} and evento.get("entidad_id") != oportunidad_id:
            continue
        rows.append(
            {
                "tipo": "evento",
                "fecha": evento.get("creado_en", ""),
                "descripcion": evento.get("descripcion", ""),
                "actor": evento.get("actor", ""),
                "detalle": evento.get("tipo_evento", ""),
            }
        )
    for nota in notas:
        rows.append(
            {
                "tipo": "nota",
                "fecha": nota.get("creado_en", ""),
                "descripcion": nota.get("contenido", ""),
                "actor": nota.get("autor") or nota.get("creado_por", ""),
                "detalle": "nota",
            }
        )
    rows.sort(key=lambda item: item.get("fecha", ""), reverse=True)
    return rows[: max(1, min(limit, 200))]
