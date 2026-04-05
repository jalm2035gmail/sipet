"""Motor de automatización CRM: SLA, alertas y acciones automáticas."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.db_models import CrmReglaAutomatizacion
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.servicios.actividad_service import (
    list_actividades_by_tenant,
    marcar_actividades_vencidas,
)
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id
from fastapi_modulo.modulos.crm.servicios.evento_service import registrar_evento


def verificar_sla_actividades(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Devuelve actividades que han superado su ventana de SLA pero aún no están completadas."""
    normalized_tenant = normalize_tenant_id(tenant_id)
    now = datetime.utcnow()
    pendientes = list_actividades_by_tenant(normalized_tenant, completada=False).get("items", [])
    alertas: List[Dict[str, Any]] = []
    for act in pendientes:
        if act.get("estado") in ("completada", "cancelada"):
            continue
        sla_horas = act.get("sla_horas")
        fecha_str = act.get("fecha")
        if not sla_horas or not fecha_str:
            continue
        try:
            fecha = datetime.fromisoformat(fecha_str)
        except ValueError:
            continue
        deadline = fecha + timedelta(hours=int(sla_horas))
        if now > deadline:
            horas_vencida = round((now - deadline).total_seconds() / 3600, 1)
            alertas.append({
                "actividad_id": act["id"],
                "titulo": act.get("titulo"),
                "tipo": act.get("tipo"),
                "responsable": act.get("responsable") or act.get("asignado_a"),
                "fecha_programada": fecha_str,
                "sla_horas": sla_horas,
                "horas_vencida": horas_vencida,
                "prioridad": act.get("prioridad", "media"),
                "contacto_id": act.get("contacto_id"),
                "oportunidad_id": act.get("oportunidad_id"),
            })
    return sorted(alertas, key=lambda x: x["horas_vencida"], reverse=True)


def ejecutar_ciclo_automatizacion(tenant_id: Optional[str] = None, *, actor: str = "sistema") -> Dict[str, Any]:
    """Ejecuta el ciclo completo de automatización para un tenant.

    - Marca actividades vencidas
    - Retorna resumen de alertas SLA activas
    """
    normalized_tenant = normalize_tenant_id(tenant_id)
    count_vencidas = marcar_actividades_vencidas(normalized_tenant, actor=actor)
    alertas_sla = verificar_sla_actividades(normalized_tenant)

    if count_vencidas > 0:
        registrar_evento(
            normalized_tenant,
            entidad="sistema",
            entidad_id=0,
            tipo_evento="ciclo_automatizacion",
            actor=actor,
            descripcion=f"Ciclo de automatización: {count_vencidas} actividades marcadas como vencidas",
            payload={"vencidas_marcadas": count_vencidas, "alertas_sla": len(alertas_sla)},
        )

    return {
        "tenant_id": normalized_tenant,
        "timestamp": datetime.utcnow().isoformat(),
        "actividades_marcadas_vencidas": count_vencidas,
        "alertas_sla_activas": len(alertas_sla),
        "detalle_alertas": alertas_sla,
    }


# ── CRUD de reglas de automatización ─────────────────────────────────────────

def _map_regla(obj: CrmReglaAutomatizacion) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "nombre": obj.nombre,
        "evento_trigger": obj.evento_trigger,
        "condicion_json": obj.condicion_json,
        "accion_tipo": obj.accion_tipo,
        "accion_params_json": obj.accion_params_json,
        "activa": obj.activa,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "creado_en": obj.creado_en.isoformat() if obj.creado_en else "",
        "actualizado_en": obj.actualizado_en.isoformat() if obj.actualizado_en else "",
    }


def list_reglas(tenant_id: Optional[str], *, solo_activas: bool = False) -> List[Dict[str, Any]]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        q = db.query(CrmReglaAutomatizacion).filter(CrmReglaAutomatizacion.tenant_id == normalized)
        if solo_activas:
            q = q.filter(CrmReglaAutomatizacion.activa == True)  # noqa: E712
        return [_map_regla(r) for r in q.order_by(CrmReglaAutomatizacion.id).all()]
    finally:
        db.close()


def get_regla(tenant_id: Optional[str], regla_id: int) -> Optional[Dict[str, Any]]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        obj = db.query(CrmReglaAutomatizacion).filter(
            CrmReglaAutomatizacion.tenant_id == normalized,
            CrmReglaAutomatizacion.id == regla_id,
        ).first()
        return _map_regla(obj) if obj else None
    finally:
        db.close()


def create_regla(data: Dict[str, Any], tenant_id: Optional[str], *, actor: str = "") -> Dict[str, Any]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        obj = CrmReglaAutomatizacion(
            tenant_id=normalized,
            nombre=data["nombre"],
            evento_trigger=data["evento_trigger"],
            condicion_json=data.get("condicion_json"),
            accion_tipo=data["accion_tipo"],
            accion_params_json=data.get("accion_params_json"),
            activa=bool(data.get("activa", True)),
            creado_por=actor,
            actualizado_por=actor,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _map_regla(obj)
    finally:
        db.close()


def update_regla(tenant_id: Optional[str], regla_id: int, data: Dict[str, Any], *, actor: str = "") -> Optional[Dict[str, Any]]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        obj = db.query(CrmReglaAutomatizacion).filter(
            CrmReglaAutomatizacion.tenant_id == normalized,
            CrmReglaAutomatizacion.id == regla_id,
        ).first()
        if not obj:
            return None
        for field in ("nombre", "evento_trigger", "condicion_json", "accion_tipo", "accion_params_json", "activa"):
            if field in data:
                setattr(obj, field, data[field])
        obj.actualizado_por = actor
        obj.actualizado_en = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return _map_regla(obj)
    finally:
        db.close()


def delete_regla(tenant_id: Optional[str], regla_id: int) -> bool:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        obj = db.query(CrmReglaAutomatizacion).filter(
            CrmReglaAutomatizacion.tenant_id == normalized,
            CrmReglaAutomatizacion.id == regla_id,
        ).first()
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
    finally:
        db.close()


# ── Motor de evaluación de reglas ─────────────────────────────────────────────

def evaluar_reglas(
    tenant_id: Optional[str],
    evento_trigger: str,
    contexto: Dict[str, Any],
    *,
    actor: str = "sistema",
) -> List[Dict[str, Any]]:
    """Evalúa reglas activas que coincidan con `evento_trigger` y ejecuta sus acciones.

    El `contexto` contiene atributos de la entidad que disparó el evento
    (e.g. {"oportunidad_id": 5, "etapa": "negociacion", "valor_estimado": 80000}).

    Retorna la lista de acciones ejecutadas.
    """
    normalized = normalize_tenant_id(tenant_id)
    reglas = list_reglas(normalized, solo_activas=True)
    ejecutadas: List[Dict[str, Any]] = []

    for regla in reglas:
        if regla["evento_trigger"] != evento_trigger:
            continue
        if not _evaluar_condicion(regla.get("condicion_json"), contexto):
            continue
        resultado = _ejecutar_accion(
            normalized,
            regla["accion_tipo"],
            regla.get("accion_params_json") or {},
            contexto,
            actor=actor,
        )
        ejecutadas.append({
            "regla_id": regla["id"],
            "nombre": regla["nombre"],
            "accion_tipo": regla["accion_tipo"],
            "resultado": resultado,
        })
        registrar_evento(
            normalized,
            entidad="regla_automatizacion",
            entidad_id=regla["id"],
            tipo_evento="regla_ejecutada",
            actor=actor,
            descripcion=f"Regla ejecutada: {regla['nombre']} ({evento_trigger})",
            payload={"regla_id": regla["id"], "contexto": contexto},
        )

    return ejecutadas


def _evaluar_condicion(condicion: Optional[Dict[str, Any]], contexto: Dict[str, Any]) -> bool:
    """Evaluación simple de condición JSON.

    Formato de condicion_json:
      {"campo": "valor_estimado", "operador": ">=", "valor": 50000}
    Si condicion es None o vacía, la regla aplica siempre.
    """
    if not condicion:
        return True
    campo = condicion.get("campo")
    operador = condicion.get("operador", "==")
    valor_esperado = condicion.get("valor")
    if campo is None:
        return True
    valor_actual = contexto.get(campo)
    try:
        if operador == "==":
            return valor_actual == valor_esperado
        if operador == "!=":
            return valor_actual != valor_esperado
        if operador == ">=":
            return float(valor_actual or 0) >= float(valor_esperado or 0)
        if operador == "<=":
            return float(valor_actual or 0) <= float(valor_esperado or 0)
        if operador == ">":
            return float(valor_actual or 0) > float(valor_esperado or 0)
        if operador == "<":
            return float(valor_actual or 0) < float(valor_esperado or 0)
        if operador == "in":
            return valor_actual in (valor_esperado or [])
    except (TypeError, ValueError):
        pass
    return False


def _ejecutar_accion(
    tenant_id: str,
    accion_tipo: str,
    params: Dict[str, Any],
    contexto: Dict[str, Any],
    *,
    actor: str,
) -> str:
    """Despacha la acción correspondiente al tipo configurado en la regla."""
    if accion_tipo == "crear_notificacion":
        from fastapi_modulo.modulos.crm.servicios.notification_service import crear_notificacion
        usuario = params.get("usuario_dest") or contexto.get("responsable") or actor
        mensaje = params.get("mensaje", "Evento CRM automático")
        crear_notificacion(
            tenant_id,
            usuario_dest=str(usuario),
            tipo=params.get("tipo_notificacion", "regla_automatica"),
            mensaje=mensaje,
            referencia_tipo=params.get("referencia_tipo") or contexto.get("entidad"),
            referencia_id=params.get("referencia_id") or contexto.get("entidad_id"),
        )
        return f"Notificación enviada a {usuario}"

    if accion_tipo == "crear_actividad":
        from fastapi_modulo.modulos.crm.servicios.actividad_service import create_actividad
        data = {
            "contacto_id": params.get("contacto_id") or contexto.get("contacto_id"),
            "oportunidad_id": params.get("oportunidad_id") or contexto.get("oportunidad_id"),
            "tipo": params.get("tipo", "tarea"),
            "titulo": params.get("titulo", "Actividad automática"),
            "descripcion": params.get("descripcion", "Generada por regla de automatización"),
            "fecha": datetime.utcnow() + timedelta(hours=int(params.get("horas_adelanto", 24))),
            "responsable": params.get("responsable") or contexto.get("responsable") or actor,
        }
        create_actividad(data, tenant_id, actor=actor)
        return "Actividad creada"

    if accion_tipo == "registrar_evento":
        registrar_evento(
            tenant_id,
            entidad=params.get("entidad", "sistema"),
            entidad_id=params.get("entidad_id") or contexto.get("entidad_id") or 0,
            tipo_evento=params.get("tipo_evento", "evento_automatico"),
            actor=actor,
            descripcion=params.get("descripcion", "Evento automático por regla"),
            payload=contexto,
        )
        return "Evento registrado"

    return f"Acción desconocida: {accion_tipo}"

