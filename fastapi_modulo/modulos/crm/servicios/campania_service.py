from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmContacto,
    CrmContactoCampania,
    CrmOportunidad,
)
from fastapi_modulo.modulos.crm.modelos.enums import EstadoCampania, TipoActividad, SLA_POR_TIPO
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.campania_repository import (
    add_contacto_campania as repo_add_contacto_campania,
    archivar_campania as repo_archivar_campania,
    contacto_campania_exists,
    create_campania as repo_create_campania,
    get_campania as repo_get_campania,
    list_campanias as repo_list_campanias,
    list_contactos_campania as repo_list_contactos_campania,
    remove_contacto_campania as repo_remove_contacto_campania,
    update_campania as repo_update_campania,
)


def list_campanias(estado: Optional[str] = None, q: Optional[str] = None, responsable: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    return repo_list_campanias(normalize_tenant_id(None), estado, q, responsable, skip, limit)


def list_campanias_by_tenant(tenant_id: Optional[str], estado: Optional[str] = None, q: Optional[str] = None, responsable: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    return repo_list_campanias(normalize_tenant_id(tenant_id), estado, q, responsable, skip, limit)


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
    campania = repo_get_campania(normalized_tenant, int(data["campania_id"]))
    if campania and campania.get("estado") == EstadoCampania.FINALIZADA.value:
        raise ValueError("No se pueden agregar contactos a una campaña finalizada")
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


# ---------------------------------------------------------------------------
# 4.2  Segmentación automática de contactos
# ---------------------------------------------------------------------------

def segmentar_contactos(
    campania_id: int,
    filtros: Dict[str, Any],
    tenant_id: Optional[str] = None,
    *,
    agregar: bool = False,
    actor: str = "",
) -> Dict[str, Any]:
    """Segmenta contactos según filtros y opcionalmente los incorpora a la campaña.

    Parámetros disponibles en `filtros`:
        fuente, sucursal, score_min, score_max, temperatura,
        etapa_oportunidad, dias_inactividad_min, dias_inactividad_max,
        campania_anterior_id, responsable.

    Si `agregar=True`, los contactos resultantes se incorporan automáticamente
    a la campaña (sin duplicar los ya existentes).
    """
    normalized = normalize_tenant_id(tenant_id)
    campania = repo_get_campania(normalized, campania_id)
    if not campania:
        raise ValueError("Campaña no encontrada")
    if campania["estado"] == EstadoCampania.FINALIZADA.value:
        raise ValueError("No se puede segmentar una campaña finalizada")

    db = get_db()
    try:
        query = db.query(CrmContacto).filter(CrmContacto.tenant_id == normalized)

        if filtros.get("fuente"):
            query = query.filter(CrmContacto.fuente == filtros["fuente"])
        if filtros.get("sucursal"):
            query = query.filter(CrmContacto.sucursal == filtros["sucursal"])
        if filtros.get("responsable"):
            query = query.filter(CrmContacto.asignado_a == filtros["responsable"])
        if filtros.get("temperatura"):
            query = query.filter(CrmContacto.lead_temperatura == filtros["temperatura"])
        if filtros.get("score_min") is not None:
            query = query.filter(CrmContacto.lead_score >= filtros["score_min"])
        if filtros.get("score_max") is not None:
            query = query.filter(CrmContacto.lead_score <= filtros["score_max"])

        # Filtro por etapa de oportunidad (al menos una oportunidad en esa etapa)
        if filtros.get("etapa_oportunidad"):
            sub = db.query(CrmOportunidad.contacto_id).filter(
                CrmOportunidad.tenant_id == normalized,
                CrmOportunidad.etapa == filtros["etapa_oportunidad"],
            ).subquery()
            query = query.filter(CrmContacto.id.in_(sub))

        # Filtro por inactividad (días desde último movimiento de oportunidad)
        if filtros.get("dias_inactividad_min") is not None or filtros.get("dias_inactividad_max") is not None:
            now = datetime.utcnow()
            sub_op = db.query(CrmOportunidad.contacto_id).filter(
                CrmOportunidad.tenant_id == normalized,
            )
            if filtros.get("dias_inactividad_min") is not None:
                cutoff_max = now - timedelta(days=int(filtros["dias_inactividad_min"]))
                sub_op = sub_op.filter(CrmOportunidad.ultimo_movimiento_en <= cutoff_max)
            if filtros.get("dias_inactividad_max") is not None:
                cutoff_min = now - timedelta(days=int(filtros["dias_inactividad_max"]))
                sub_op = sub_op.filter(CrmOportunidad.ultimo_movimiento_en >= cutoff_min)
            query = query.filter(CrmContacto.id.in_(sub_op.subquery()))

        # Excluir contactos ya en otra campaña específica
        if filtros.get("campania_anterior_id") is not None:
            ya_en = db.query(CrmContactoCampania.contacto_id).filter(
                CrmContactoCampania.tenant_id == normalized,
                CrmContactoCampania.campania_id == int(filtros["campania_anterior_id"]),
            ).subquery()
            query = query.filter(CrmContacto.id.in_(ya_en))

        contactos = query.all()
        contacto_ids = [c.id for c in contactos]

        incorporados = 0
        omitidos = 0
        if agregar:
            for cid in contacto_ids:
                if not contacto_campania_exists(normalized, cid, campania_id):
                    repo_add_contacto_campania({
                        "tenant_id": normalized,
                        "contacto_id": cid,
                        "campania_id": campania_id,
                        "creado_por": actor,
                        "actualizado_por": actor,
                    })
                    incorporados += 1
                else:
                    omitidos += 1

            registrar_evento(
                normalized,
                entidad="campania",
                entidad_id=campania_id,
                tipo_evento="segmento_incorporado",
                actor=actor,
                descripcion=f"Segmentación: {incorporados} contactos incorporados a campaña",
                payload={"campania_id": campania_id, "incorporados": incorporados, "omitidos": omitidos},
            )

        return {
            "campania_id": campania_id,
            "total_encontrados": len(contacto_ids),
            "incorporados": incorporados,
            "omitidos": omitidos,
            "contacto_ids": contacto_ids,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4.4  Activar campaña con side-effects
# ---------------------------------------------------------------------------

def activar_campania(
    campania_id: int,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
) -> Optional[Dict[str, Any]]:
    """Activa una campaña y desencadena acciones automáticas:

    - Cambia el estado a ACTIVA.
    - Crea una actividad de seguimiento para cada contacto del segmento
      (asignada al responsable de la campaña o al actor).
    - Registra un evento de activación.
    """
    normalized = normalize_tenant_id(tenant_id)
    campania = repo_get_campania(normalized, campania_id)
    if not campania:
        return None
    if campania["estado"] == EstadoCampania.ACTIVA.value:
        raise ValueError("La campaña ya está activa")
    if campania["estado"] == EstadoCampania.FINALIZADA.value:
        raise ValueError("No se puede activar una campaña finalizada")

    # Cambiar estado
    updated = repo_update_campania(normalized, campania_id, {
        "estado": EstadoCampania.ACTIVA.value,
        "actualizado_por": actor,
    })
    if not updated:
        return None

    # Crear actividades de seguimiento para ejecutivos del segmento
    from fastapi_modulo.modulos.crm.servicios.actividad_service import create_actividad as svc_create_actividad

    contactos_campania = repo_list_contactos_campania(normalized, campania_id)
    responsable_campania = campania.get("asignado_a") or actor
    sla_h = SLA_POR_TIPO.get(TipoActividad.LLAMADA.value, 24)
    actividades_creadas = 0
    for rel in contactos_campania:
        cid = rel.get("contacto_id")
        if not cid:
            continue
        try:
            svc_create_actividad(
                {
                    "tipo": TipoActividad.LLAMADA.value,
                    "titulo": f"Seguimiento campaña: {campania['nombre']}",
                    "descripcion": f"Actividad automática generada al activar campaña {campania['nombre']}",
                    "fecha": datetime.utcnow() + timedelta(hours=sla_h),
                    "sla_horas": sla_h,
                    "prioridad": "media",
                    "contacto_id": cid,
                    "responsable": responsable_campania,
                    "asignado_a": responsable_campania,
                },
                normalized,
                actor=actor,
            )
            actividades_creadas += 1
        except Exception:
            pass  # No bloquear activación si falla una actividad individual

    registrar_evento(
        normalized,
        entidad="campania",
        entidad_id=campania_id,
        tipo_evento="campania_activada",
        actor=actor,
        descripcion=f"Campaña activada: {campania['nombre']}",
        payload={
            "campania_id": campania_id,
            "actividades_creadas": actividades_creadas,
            "contactos_en_segmento": len(contactos_campania),
        },
    )

    updated["actividades_creadas"] = actividades_creadas
    return updated


def archivar_campania(campania_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    result = repo_archivar_campania(normalized_tenant, campania_id, actor)
    if result:
        registrar_evento(
            normalized_tenant,
            entidad="campania",
            entidad_id=campania_id,
            tipo_evento="campania_archivada",
            actor=actor,
            descripcion=f"Campaña archivada: {result.get('nombre', '')}",
            payload={"campania_id": campania_id},
        )
    return result
