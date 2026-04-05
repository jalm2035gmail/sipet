from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.enums import ETAPAS_CERRADAS, EtapaOportunidad
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.repositorios.contacto_repository import get_contacto as repo_get_contacto
from fastapi_modulo.modulos.crm.repositorios.oportunidad_repository import (
    archivar_oportunidad as repo_archivar_oportunidad,
    create_oportunidad as repo_create_oportunidad,
    delete_oportunidad as repo_delete_oportunidad,
    get_historial_etapas,
    get_oportunidad as repo_get_oportunidad,
    list_oportunidades as repo_list_oportunidades,
    registrar_historial_etapa,
    update_oportunidad as repo_update_oportunidad,
)


STAGE_ACTIVITY_MAP = {
    EtapaOportunidad.NUEVO_LEAD.value: "Realizar primer contacto con el lead",
    EtapaOportunidad.POR_CONTACTAR.value: "Contactar al prospecto",
    EtapaOportunidad.CONTACTADO.value: "Calificar necesidad del prospecto",
    EtapaOportunidad.CALIFICADO.value: "Iniciar diagnóstico comercial",
    EtapaOportunidad.DIAGNOSTICO.value: "Preparar propuesta comercial",
    EtapaOportunidad.NEGOCIACION.value: "Seguimiento de negociación",
    EtapaOportunidad.PROPUESTA_ENVIADA.value: "Hacer seguimiento a propuesta enviada",
    EtapaOportunidad.SEGUIMIENTO_PROPUESTA.value: "Obtener decisión del cliente",
    EtapaOportunidad.DECISION.value: "Preparar cierre",
    # Legado
    EtapaOportunidad.PROSPECTO.value: "Calificar oportunidad",
    EtapaOportunidad.PROPUESTA.value: "Enviar y revisar propuesta",
}

_ETAPAS_NEGOCIACION = {EtapaOportunidad.NEGOCIACION.value}
_ETAPAS_PROPUESTA = {EtapaOportunidad.PROPUESTA_ENVIADA.value, EtapaOportunidad.PROPUESTA.value}


def _validar_transicion_etapa(current: Dict[str, Any], data: Dict[str, Any], next_etapa: str) -> None:
    """Aplica reglas de negocio obligatorias al cambiar de etapa."""
    merged = {**current, **data}

    if next_etapa in _ETAPAS_NEGOCIACION:
        if not float(merged.get("valor_estimado") or 0):
            raise ValueError("Para pasar a Negociación se requiere monto estimado mayor a 0")
        if not str(merged.get("responsable") or merged.get("asignado_a") or "").strip():
            raise ValueError("Para pasar a Negociación se requiere asignar un responsable")
        if not merged.get("fecha_cierre_est"):
            raise ValueError("Para pasar a Negociación se requiere fecha estimada de cierre")

    if next_etapa in _ETAPAS_PROPUESTA:
        if not merged.get("fecha_cierre_est"):
            raise ValueError("Para pasar a Propuesta se requiere fecha estimada de cierre")
        if int(merged.get("probabilidad") or 0) < 40:
            raise ValueError("Para pasar a Propuesta la probabilidad debe ser al menos 40%")

    if next_etapa == EtapaOportunidad.CERRADO_PERDIDO.value:
        if not data.get("motivo_perdida_id") and not current.get("motivo_perdida_id"):
            raise ValueError("Para cerrar como perdida se debe indicar el motivo de pérdida")

    if next_etapa == EtapaOportunidad.CERRADO_GANADO.value:
        # Auto-fill fecha_cierre_real si no está presente
        if not merged.get("fecha_cierre_real"):
            data["fecha_cierre_real"] = date.today()


def list_oportunidades(contacto_id: Optional[int] = None, etapa: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_oportunidades(normalize_tenant_id(None), contacto_id, etapa)


def list_oportunidades_by_tenant(tenant_id: Optional[str], contacto_id: Optional[int] = None, etapa: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo_list_oportunidades(normalize_tenant_id(tenant_id), contacto_id, etapa)


_STAGE_BASE_PROB = {
    EtapaOportunidad.NUEVO_LEAD.value: 5,
    EtapaOportunidad.POR_CONTACTAR.value: 10,
    EtapaOportunidad.CONTACTADO.value: 20,
    EtapaOportunidad.CALIFICADO.value: 30,
    EtapaOportunidad.DIAGNOSTICO.value: 40,
    EtapaOportunidad.NEGOCIACION.value: 55,
    EtapaOportunidad.PROPUESTA_ENVIADA.value: 65,
    EtapaOportunidad.SEGUIMIENTO_PROPUESTA.value: 75,
    EtapaOportunidad.DECISION.value: 85,
    EtapaOportunidad.CERRADO_GANADO.value: 100,
    EtapaOportunidad.CERRADO_PERDIDO.value: 0,
    EtapaOportunidad.PROSPECTO.value: 25,
    EtapaOportunidad.PROPUESTA.value: 60,
}


def calcular_probabilidad_sistema(oportunidad: Dict[str, Any], tenant_id: Optional[str] = None) -> float:
    """Calcula la probabilidad de cierre basada en señales objetivas (0-100)."""
    etapa = oportunidad.get("etapa", "")
    base = float(_STAGE_BASE_PROB.get(etapa, 10))
    ajuste = 0.0

    # Penalizar por inactividad
    ref_str = oportunidad.get("ultimo_movimiento_en") or ""
    if ref_str:
        try:
            ref_dt = datetime.fromisoformat(ref_str)
            dias_sin_mov = max(0, (datetime.utcnow() - ref_dt).days)
            if dias_sin_mov > 30:
                ajuste -= 20
            elif dias_sin_mov > 14:
                ajuste -= 10
            elif dias_sin_mov > 7:
                ajuste -= 5
        except ValueError:
            pass

    # Bonus por actividad futura programada
    from fastapi_modulo.modulos.crm.repositorios.actividad_repository import list_actividades as repo_list_acts
    normalized_tenant = normalize_tenant_id(tenant_id)
    oportunidad_id = oportunidad.get("id")
    if oportunidad_id:
        acts = repo_list_acts(normalized_tenant, None, oportunidad_id, False)
        now = datetime.utcnow()
        futuras = [
            a for a in acts
            if a.get("fecha") and datetime.fromisoformat(a["fecha"]) > now
        ]
        if futuras:
            ajuste += 10

    # Bonus por fuente referido del contacto
    contacto_id = oportunidad.get("contacto_id")
    if contacto_id:
        contacto = repo_get_contacto(normalized_tenant, int(contacto_id))
        if contacto and contacto.get("fuente") == "referido":
            ajuste += 8
        if contacto:
            lead_score = int(contacto.get("lead_score") or 0)
            ajuste += round((lead_score - 50) / 10, 1)

    # Fecha de cierre próxima (<7 días) como factor de urgencia
    fecha_cierre_str = oportunidad.get("fecha_cierre_est") or ""
    if fecha_cierre_str:
        try:
            fecha_cierre = date.fromisoformat(fecha_cierre_str)
            dias_al_cierre = (fecha_cierre - date.today()).days
            if 0 <= dias_al_cierre <= 7:
                ajuste += 5
        except ValueError:
            pass

    resultado = max(0.0, min(100.0, round(base + ajuste, 1)))
    return resultado


def list_oportunidades_sin_movimiento(tenant_id: Optional[str], dias_minimos: int = 7) -> List[Dict[str, Any]]:
    from fastapi_modulo.modulos.crm.modelos.enums import ETAPAS_ABIERTAS
    todas = repo_list_oportunidades(normalize_tenant_id(tenant_id), limit=10000).get("items", [])
    now = datetime.utcnow()
    resultado = []
    for op in todas:
        if op.get("etapa") not in ETAPAS_ABIERTAS:
            continue
        ref = op.get("ultimo_movimiento_en") or ""
        try:
            ref_dt = datetime.fromisoformat(ref) if ref else None
        except ValueError:
            ref_dt = None
        dias = max(0, (now - ref_dt).days) if ref_dt else 999
        if dias < dias_minimos:
            continue
        resultado.append({**op, "dias_sin_movimiento": dias})
    resultado.sort(key=lambda x: -x["dias_sin_movimiento"])
    return resultado


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
    if data.get("etapa") in ETAPAS_CERRADAS and not data.get("fecha_cierre_real"):
        data["fecha_cierre_real"] = date.today()
        data["cerrado_por"] = actor
    data["probabilidad_sistema"] = calcular_probabilidad_sistema(data, normalized_tenant)
    created = repo_create_oportunidad(data)
    # Registrar historial de etapa inicial
    registrar_historial_etapa(
        normalized_tenant,
        oportunidad_id=created["id"],
        etapa_anterior=None,
        etapa_nueva=created["etapa"],
        actor=actor,
        comentario="Oportunidad creada",
    )
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


def update_oportunidad(
    oportunidad_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
    comentario_historial: Optional[str] = None,
    motivo_historial: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    current = repo_get_oportunidad(normalized_tenant, oportunidad_id)
    if not current:
        return None
    current_stage = current.get("etapa")
    next_stage = data.get("etapa", current_stage)
    is_currently_closed = current_stage in ETAPAS_CERRADAS
    is_next_closed = next_stage in ETAPAS_CERRADAS

    if is_currently_closed and next_stage == current_stage:
        raise ValueError("La oportunidad está cerrada y no puede editarse sin reabrirse")

    if is_currently_closed and current_stage != next_stage and is_next_closed:
        raise ValueError(
            "No se puede cambiar entre estados cerrados. "
            "Para reclasificar, primero reabra la oportunidad hacia una etapa activa"
        )

    # Aplicar reglas de negocio si cambia de etapa
    if current_stage != next_stage:
        _validar_transicion_etapa(current, data, next_stage)

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
    data["probabilidad_sistema"] = calcular_probabilidad_sistema({**current, **data}, normalized_tenant)
    updated = repo_update_oportunidad(normalized_tenant, oportunidad_id, data)
    if updated and current_stage != updated.get("etapa"):
        registrar_historial_etapa(
            normalized_tenant,
            oportunidad_id=updated["id"],
            etapa_anterior=current_stage,
            etapa_nueva=updated["etapa"],
            actor=actor,
            comentario=comentario_historial,
            motivo=motivo_historial,
        )
        registrar_evento(
            normalized_tenant,
            entidad="oportunidad",
            entidad_id=updated["id"],
            tipo_evento="oportunidad_etapa_cambiada",
            actor=actor,
            descripcion=f"Cambio de etapa: {current_stage} -> {updated.get('etapa')}",
            payload={"oportunidad_id": updated["id"], "anterior": current_stage, "actual": updated.get("etapa")},
        )
        _ensure_stage_activity(updated, actor=actor)
    if updated and updated.get("etapa") in ETAPAS_CERRADAS:
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


def get_historial_oportunidad(oportunidad_id: int, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return get_historial_etapas(normalize_tenant_id(tenant_id), oportunidad_id)


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
    comentario: Optional[str] = None,
    motivo: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    return update_oportunidad(
        oportunidad_id,
        {"etapa": etapa},
        tenant_id,
        actor=actor,
        comentario_historial=comentario,
        motivo_historial=motivo,
    )


def marcar_oportunidad_ganada(
    oportunidad_id: int,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
    motivo_ganancia_id: Optional[int] = None,
    monto_real: Optional[float] = None,
    producto_vendido: Optional[str] = None,
    comentario: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    data: Dict[str, Any] = {"etapa": EtapaOportunidad.CERRADO_GANADO.value}
    if motivo_ganancia_id is not None:
        data["motivo_ganancia_id"] = motivo_ganancia_id
    if monto_real is not None:
        data["monto_real"] = monto_real
    if producto_vendido:
        data["producto_vendido"] = producto_vendido
    return update_oportunidad(
        oportunidad_id,
        data,
        tenant_id,
        actor=actor,
        comentario_historial=comentario,
    )


def marcar_oportunidad_perdida(
    oportunidad_id: int,
    tenant_id: Optional[str] = None,
    *,
    actor: str = "",
    motivo_perdida_id: int,
    comentario: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    return update_oportunidad(
        oportunidad_id,
        {"etapa": EtapaOportunidad.CERRADO_PERDIDO.value, "motivo_perdida_id": motivo_perdida_id},
        tenant_id,
        actor=actor,
        comentario_historial=comentario,
        motivo_historial=str(motivo_perdida_id),
    )


STAGE_ACTIVITY_MAP = {
    EtapaOportunidad.PROSPECTO.value: "Calificar oportunidad",
    EtapaOportunidad.NEGOCIACION.value: "Seguimiento de negociación",
    EtapaOportunidad.PROPUESTA.value: "Enviar y revisar propuesta",
}


def list_oportunidades(
    contacto_id: Optional[int] = None,
    etapa: Optional[str] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    sucursal: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    return repo_list_oportunidades(normalize_tenant_id(None), contacto_id, etapa, q, responsable, sucursal, skip, limit)


def list_oportunidades_by_tenant(
    tenant_id: Optional[str],
    contacto_id: Optional[int] = None,
    etapa: Optional[str] = None,
    q: Optional[str] = None,
    responsable: Optional[str] = None,
    sucursal: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    return repo_list_oportunidades(normalize_tenant_id(tenant_id), contacto_id, etapa, q, responsable, sucursal, skip, limit)


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
    if "version" in data and data["version"] != current.get("version", 1):
        raise ValueError(
            f"Conflicto de concurrencia: la oportunidad fue modificada por otro usuario "
            f"(versión esperada {data['version']}, versión actual {current.get('version', 1)})"
        )
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
    if is_currently_closed and current_stage != next_stage and is_next_closed:
        raise ValueError(
            "No se puede cambiar entre estados cerrados. "
            "Para reclasificar, primero reabra la oportunidad hacia una etapa activa"
        )
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
    data["version"] = (current.get("version") or 1) + 1
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


def archivar_oportunidad(oportunidad_id: int, tenant_id: Optional[str] = None, *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized_tenant = normalize_tenant_id(tenant_id)
    result = repo_archivar_oportunidad(normalized_tenant, oportunidad_id, actor)
    if result:
        registrar_evento(
            normalized_tenant,
            entidad="oportunidad",
            entidad_id=oportunidad_id,
            tipo_evento="oportunidad_archivada",
            actor=actor,
            descripcion=f"Oportunidad archivada: {result.get('nombre', '')}",
            payload={"oportunidad_id": oportunidad_id},
        )
    return result
