from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import SLA_POR_TIPO, TipoActividad
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.actividad_repository import (
    archivar_actividad as repo_archivar_actividad,
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
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    return repo_list_actividades(normalize_tenant_id(None), contacto_id, oportunidad_id, completada, q, responsable, skip, limit)


def list_actividades_by_tenant(
    tenant_id: Optional[str],
    contacto_id: Optional[int] = None,
    oportunidad_id: Optional[int] = None,
    completada: Optional[bool] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    return repo_list_actividades(normalize_tenant_id(tenant_id), contacto_id, oportunidad_id, completada, q, responsable, skip, limit)


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
    # Auto-assign SLA hours from tipo if not provided
    if not data.get("sla_horas"):
        tipo = data.get("tipo", "tarea")
        if isinstance(tipo, TipoActividad):
            tipo = tipo.value
        data["sla_horas"] = SLA_POR_TIPO.get(tipo, 24)
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
    if current.get("estado") == "vencida" and "fecha" not in data:
        raise ValueError("Para modificar una actividad vencida se debe indicar la nueva fecha de reprogramación")
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


def completar_actividad(
    actividad_id: int,
    tipo_resultado: str,
    tenant_id: Optional[str] = None,
    *,
    siguiente_accion: Optional[str] = None,
    comentario: Optional[str] = None,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    patch: Dict[str, Any] = {
        "completada": True,
        "estado": "completada",
        "tipo_resultado": tipo_resultado,
    }
    if siguiente_accion:
        patch["siguiente_accion"] = siguiente_accion
    if comentario:
        if not patch.get("descripcion"):
            patch["descripcion"] = comentario
    updated = update_actividad(actividad_id, patch, normalized_tenant, actor=actor)
    if updated and siguiente_accion:
        registrar_evento(
            normalized_tenant,
            entidad="actividad",
            entidad_id=actividad_id,
            tipo_evento="siguiente_accion_registrada",
            actor=actor,
            descripcion=f"Siguiente acción: {siguiente_accion}",
            payload={"actividad_id": actividad_id, "siguiente_accion": siguiente_accion, "tipo_resultado": tipo_resultado},
        )
    return updated


def cancelar_actividad(
    actividad_id: int,
    motivo: str,
    tenant_id: Optional[str] = None,
    *,
    siguiente_accion: Optional[str] = None,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    patch: Dict[str, Any] = {"estado": "cancelada", "completada": False}
    if siguiente_accion:
        patch["siguiente_accion"] = siguiente_accion
    updated = update_actividad(actividad_id, patch, normalized_tenant, actor=actor)
    if updated:
        registrar_evento(
            normalized_tenant,
            entidad="actividad",
            entidad_id=actividad_id,
            tipo_evento="actividad_cancelada",
            actor=actor,
            descripcion=f"Actividad cancelada: {motivo}",
            payload={"actividad_id": actividad_id, "motivo": motivo},
        )
    return updated


def crear_actividad_automatica(
    trigger: str,
    contexto: Dict[str, Any],
    tenant_id: Optional[str] = None,
    *,
    actor: str = "sistema",
) -> Optional[Dict[str, Any]]:
    """Crea una actividad automática basada en un trigger de negocio.

    Triggers soportados: lead_nuevo, actividad_vencida, propuesta_enviada,
    contacto_convertido, oportunidad_reabierta.
    """
    now = datetime.utcnow()
    tipo_map = {
        "lead_nuevo": TipoActividad.LLAMADA,
        "actividad_vencida": TipoActividad.TAREA,
        "propuesta_enviada": TipoActividad.EMAIL,
        "contacto_convertido": TipoActividad.LLAMADA,
        "oportunidad_reabierta": TipoActividad.LLAMADA,
    }
    titulo_map = {
        "lead_nuevo": "Llamar al nuevo lead",
        "actividad_vencida": "Retomar actividad vencida",
        "propuesta_enviada": "Seguimiento de propuesta enviada",
        "contacto_convertido": "Primera llamada a contacto convertido",
        "oportunidad_reabierta": "Re-contactar cliente por oportunidad reabierta",
    }
    tipo = tipo_map.get(trigger, TipoActividad.TAREA)
    titulo = titulo_map.get(trigger, f"Acción automática: {trigger}")
    sla_h = SLA_POR_TIPO.get(tipo.value, 24)
    data: Dict[str, Any] = {
        "tipo": tipo.value,
        "titulo": titulo,
        "fecha": now + timedelta(hours=sla_h),
        "sla_horas": sla_h,
        "prioridad": contexto.get("prioridad", "alta"),
        "asignado_a": contexto.get("asignado_a", actor),
        "responsable": contexto.get("responsable", actor),
    }
    if "contacto_id" in contexto:
        data["contacto_id"] = contexto["contacto_id"]
    if "oportunidad_id" in contexto:
        data["oportunidad_id"] = contexto["oportunidad_id"]
    if not data.get("contacto_id") and not data.get("oportunidad_id"):
        return None
    try:
        return create_actividad(data, tenant_id, actor=actor)
    except ValueError:
        return None


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
        for actividad in list_actividades_by_tenant(tenant_id, completada=False).get("items", [])
        if actividad.get("fecha") and datetime.fromisoformat(actividad["fecha"]) < now
    ]


def marcar_actividades_vencidas(tenant_id: Optional[str] = None, *, actor: str = "sistema") -> int:
    """Marca como 'vencida' todas las actividades pendientes con fecha pasada. Devuelve el conteo."""
    normalized_tenant = normalize_tenant_id(tenant_id)
    vencidas = list_actividades_vencidas(normalized_tenant)
    count = 0
    for act in vencidas:
        if act.get("estado") in ("completada", "cancelada", "vencida"):
            continue
        repo_update_actividad(normalized_tenant, act["id"], {"estado": "vencida", "actualizado_por": actor})
        count += 1
    return count


def archivar_actividad(actividad_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    result = repo_archivar_actividad(normalized_tenant, actividad_id, actor)
    if result:
        registrar_evento(
            normalized_tenant,
            entidad="actividad",
            entidad_id=actividad_id,
            tipo_evento="actividad_archivada",
            actor=actor,
            descripcion="Actividad archivada",
            payload={"actividad_id": actividad_id},
        )
    return result
