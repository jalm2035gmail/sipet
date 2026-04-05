"""Motor de notificaciones internas del CRM.

Genera y persiste alertas para usuarios sobre eventos relevantes:
  - lead nuevo asignado
  - actividad vencida / próxima a vencer (<2 h)
  - oportunidad sin movimiento (amarilla/roja)
  - cambio de etapa en oportunidad
  - propuesta pendiente de seguimiento
  - campaña por iniciar / finalizada
  - oportunidad perdida de alto valor
  - cierre ganado
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.modelos.db_models import CrmNotificacion
from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.servicios.contacto_service import normalize_tenant_id


# ── Escritura ─────────────────────────────────────────────────────────────────

def crear_notificacion(
    tenant_id: Optional[str],
    usuario_dest: str,
    tipo: str,
    mensaje: str,
    *,
    referencia_tipo: Optional[str] = None,
    referencia_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Persiste una notificación para un usuario y devuelve su dict."""
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        notif = CrmNotificacion(
            tenant_id=normalized,
            usuario_dest=usuario_dest,
            tipo=tipo,
            mensaje=mensaje,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            leida=False,
            fecha_creacion=datetime.utcnow(),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return _map(notif)
    finally:
        db.close()


# ── Lecturas ──────────────────────────────────────────────────────────────────

def list_notificaciones(
    tenant_id: Optional[str],
    usuario: str,
    *,
    solo_no_leidas: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        q = db.query(CrmNotificacion).filter(
            CrmNotificacion.tenant_id == normalized,
            CrmNotificacion.usuario_dest == usuario,
        )
        if solo_no_leidas:
            q = q.filter(CrmNotificacion.leida == False)  # noqa: E712
        total = q.count()
        rows = q.order_by(CrmNotificacion.fecha_creacion.desc()).offset(skip).limit(limit).all()
        return {"items": [_map(r) for r in rows], "total": total, "skip": skip, "limit": limit}
    finally:
        db.close()


def marcar_leida(tenant_id: Optional[str], notif_id: int, usuario: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        notif = db.query(CrmNotificacion).filter(
            CrmNotificacion.tenant_id == normalized,
            CrmNotificacion.id == notif_id,
            CrmNotificacion.usuario_dest == usuario,
        ).first()
        if not notif:
            return None
        notif.leida = True
        db.commit()
        db.refresh(notif)
        return _map(notif)
    finally:
        db.close()


def marcar_todas_leidas(tenant_id: Optional[str], usuario: str) -> int:
    """Marca todas las notificaciones no leídas del usuario. Devuelve la cantidad actualizada."""
    normalized = normalize_tenant_id(tenant_id)
    db = get_db()
    try:
        count = (
            db.query(CrmNotificacion)
            .filter(
                CrmNotificacion.tenant_id == normalized,
                CrmNotificacion.usuario_dest == usuario,
                CrmNotificacion.leida == False,  # noqa: E712
            )
            .update({"leida": True})
        )
        db.commit()
        return count
    finally:
        db.close()


# ── Generadores de notificaciones por tipo de evento ─────────────────────────

def notificar_lead_asignado(
    tenant_id: Optional[str],
    contacto_id: int,
    nombre_contacto: str,
    ejecutivo: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=ejecutivo,
        tipo="lead_asignado",
        mensaje=f"Se te asignó el lead: {nombre_contacto}",
        referencia_tipo="contacto",
        referencia_id=contacto_id,
    )


def notificar_actividad_vencida(
    tenant_id: Optional[str],
    actividad_id: int,
    titulo: str,
    responsable: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="actividad_vencida",
        mensaje=f"Actividad vencida: {titulo}",
        referencia_tipo="actividad",
        referencia_id=actividad_id,
    )


def notificar_actividad_proxima(
    tenant_id: Optional[str],
    actividad_id: int,
    titulo: str,
    responsable: str,
    minutos: int,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="actividad_proxima",
        mensaje=f"Actividad en {minutos} min: {titulo}",
        referencia_tipo="actividad",
        referencia_id=actividad_id,
    )


def notificar_oportunidad_sin_movimiento(
    tenant_id: Optional[str],
    oportunidad_id: int,
    nombre: str,
    responsable: str,
    dias: int,
    semaforo: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="oportunidad_sin_movimiento",
        mensaje=f"Oportunidad sin movimiento ({dias}d, {semaforo}): {nombre}",
        referencia_tipo="oportunidad",
        referencia_id=oportunidad_id,
    )


def notificar_cambio_etapa(
    tenant_id: Optional[str],
    oportunidad_id: int,
    nombre: str,
    etapa_anterior: str,
    etapa_nueva: str,
    responsable: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="cambio_etapa",
        mensaje=f"Etapa cambiada en '{nombre}': {etapa_anterior} → {etapa_nueva}",
        referencia_tipo="oportunidad",
        referencia_id=oportunidad_id,
    )


def notificar_oportunidad_perdida_alto_valor(
    tenant_id: Optional[str],
    oportunidad_id: int,
    nombre: str,
    monto: float,
    responsable: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="oportunidad_perdida_alto_valor",
        mensaje=f"Oportunidad perdida de alto valor (${monto:,.0f}): {nombre}",
        referencia_tipo="oportunidad",
        referencia_id=oportunidad_id,
    )


def notificar_cierre_ganado(
    tenant_id: Optional[str],
    oportunidad_id: int,
    nombre: str,
    monto: float,
    responsable: str,
) -> Dict[str, Any]:
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo="cierre_ganado",
        mensaje=f"¡Cierre ganado! '{nombre}' por ${monto:,.0f}",
        referencia_tipo="oportunidad",
        referencia_id=oportunidad_id,
    )


def notificar_campania_evento(
    tenant_id: Optional[str],
    campania_id: int,
    nombre: str,
    tipo: str,
    responsable: str,
) -> Dict[str, Any]:
    """tipo: 'campania_iniciada' | 'campania_finalizada'"""
    label = "iniciada" if tipo == "campania_iniciada" else "finalizada"
    return crear_notificacion(
        tenant_id,
        usuario_dest=responsable,
        tipo=tipo,
        mensaje=f"Campaña {label}: {nombre}",
        referencia_tipo="campania",
        referencia_id=campania_id,
    )


# ── Ciclo de alertas proactivas ───────────────────────────────────────────────

def ejecutar_ciclo_notificaciones(
    tenant_id: Optional[str],
    *,
    umbral_alto_valor: float = 50_000.0,
) -> Dict[str, Any]:
    """Genera notificaciones proactivas para actividades próximas a vencer y opps sin movimiento.

    Se debe llamar periódicamente (e.g. cada 30 minutos).
    """
    from fastapi_modulo.modulos.crm.servicios.actividad_service import list_actividades_by_tenant
    from fastapi_modulo.modulos.crm.servicios.oportunidad_service import list_oportunidades_sin_movimiento

    normalized = normalize_tenant_id(tenant_id)
    now = datetime.utcnow()
    generadas = 0

    # Actividades próximas a vencer en las próximas 2 horas
    pendientes = list_actividades_by_tenant(normalized, completada=False).get("items", [])
    for act in pendientes:
        fecha_str = act.get("fecha")
        if not fecha_str:
            continue
        try:
            fecha = datetime.fromisoformat(fecha_str)
        except ValueError:
            continue
        minutos_restantes = (fecha - now).total_seconds() / 60
        if 0 < minutos_restantes <= 120:
            responsable = (act.get("responsable") or act.get("asignado_a") or "").strip()
            if responsable:
                notificar_actividad_proxima(
                    normalized,
                    act["id"],
                    act.get("titulo", ""),
                    responsable,
                    int(minutos_restantes),
                )
                generadas += 1

    # Oportunidades sin movimiento (amarillas/rojas)
    for op in list_oportunidades_sin_movimiento(normalized, dias_minimos=7):
        if op.get("semaforo") in ("amarillo", "rojo"):
            responsable = (op.get("responsable") or "").strip()
            if responsable:
                notificar_oportunidad_sin_movimiento(
                    normalized,
                    op["oportunidad_id"],
                    op.get("nombre", ""),
                    responsable,
                    op.get("dias_sin_movimiento", 0),
                    op.get("semaforo", ""),
                )
                generadas += 1

    return {"tenant_id": normalized, "notificaciones_generadas": generadas, "timestamp": now.isoformat()}


# ── Mapper interno ────────────────────────────────────────────────────────────

def _map(obj: CrmNotificacion) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "usuario_dest": obj.usuario_dest,
        "tipo": obj.tipo,
        "referencia_tipo": obj.referencia_tipo,
        "referencia_id": obj.referencia_id,
        "mensaje": obj.mensaje,
        "leida": obj.leida,
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }
