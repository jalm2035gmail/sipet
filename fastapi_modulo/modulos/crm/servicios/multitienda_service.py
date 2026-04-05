"""Servicio de integración CRM ↔ Multitienda (Fase 9.2).

Detecta y procesa eventos de Multitienda para alimentar el CRM:
  - Crear leads desde clientes registrados
  - Detectar carritos abandonados → abrir oportunidad
  - Reactivar clientes inactivos → crear oportunidad de reactivación
  - Pedidos de alto valor → crear actividad de seguimiento postventa
  - Enriquecer lead score con comportamiento de compra

El módulo es completamente opcional: si Multitienda no está disponible,
todas las funciones retornan resultados vacíos en lugar de fallar.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi_modulo.modulos.crm.repositorios.common import get_db
from fastapi_modulo.modulos.crm.modelos.db_models import CrmContacto, CrmOportunidad, CrmActividad

log = logging.getLogger(__name__)

# ── Detección de disponibilidad de Multitienda ────────────────────────────────

try:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.cart.models import Cart
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.orders.models import Order
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import CustomerBehavior
    MULTITIENDA_DISPONIBLE = True
except ImportError:
    MULTITIENDA_DISPONIBLE = False
    log.info("CRM: módulo Multitienda no disponible — integración desactivada")


def estado_integracion() -> dict[str, Any]:
    return {
        "multitienda": MULTITIENDA_DISPONIBLE,
        "conversaciones": True,  # siempre disponible (tablas propias del CRM)
    }


# ── Helpers internos ──────────────────────────────────────────────────────────

def _normalize(host):
    return host  # pass-through; get_db() handles None


def _find_contacto_by_email(db, tenant_id: str, email: str):
    return (
        db.query(CrmContacto)
        .filter(CrmContacto.tenant_id == tenant_id, CrmContacto.email == email, CrmContacto.eliminado == False)
        .first()
    )


# ── 9.2.1 Sincronizar clientes ────────────────────────────────────────────────

def sincronizar_clientes(tenant_id: str, host=None) -> dict[str, Any]:
    """Importa clientes de Multitienda como contactos CRM (crea o actualiza)."""
    if not MULTITIENDA_DISPONIBLE:
        return {"error": "Multitienda no disponible", "creados": 0, "actualizados": 0}

    db = get_db(host)
    creados = 0
    actualizados = 0
    try:
        clientes = db.query(User).filter(User.user_type == "customer").all()
        for u in clientes:
            if not u.email:
                continue
            contacto = _find_contacto_by_email(db, tenant_id, u.email)
            nombre = getattr(u, "full_name", None) or u.username or u.email
            if contacto is None:
                db.add(CrmContacto(
                    tenant_id=tenant_id,
                    nombre=nombre,
                    email=u.email,
                    tipo="prospecto",
                    fuente="backend",
                    fuente_detalle="multitienda_sync",
                    creado_en=datetime.utcnow(),
                ))
                creados += 1
            else:
                if not contacto.nombre and nombre:
                    contacto.nombre = nombre
                actualizados += 1
        db.commit()
        return {"creados": creados, "actualizados": actualizados, "total_procesados": creados + actualizados}
    finally:
        db.close()


# ── 9.2.2 Detectar carritos abandonados ───────────────────────────────────────

def detectar_carritos_abandonados(
    tenant_id: str, horas_min: int = 24, monto_min: float = 0, host=None
) -> dict[str, Any]:
    """Carritos con ítems sin orden asociada en las últimas N horas → oportunidad CRM."""
    if not MULTITIENDA_DISPONIBLE:
        return {"error": "Multitienda no disponible", "procesados": 0}

    corte = datetime.utcnow() - timedelta(hours=horas_min)
    db = get_db(host)
    creadas = 0
    try:
        carts = (
            db.query(Cart)
            .filter(Cart.updated_at <= corte, Cart.user_id != None)
            .all()
        )
        # Obtener order user_ids para excluir los que sí compraron
        order_user_ids = {row[0] for row in db.query(Order.customer_id).filter(Order.customer_id != None).all()}

        for cart in carts:
            if cart.user_id in order_user_ids:
                continue
            if not cart.items:
                continue
            monto = float(cart.get_total())
            if monto < monto_min:
                continue

            # Buscar usuario y contacto asociado
            user = db.query(User).filter(User.id == cart.user_id).first()
            if not user or not user.email:
                continue
            contacto = _find_contacto_by_email(db, tenant_id, user.email)
            if contacto is None:
                continue

            # Evitar duplicado: hay oportunidad de carrito abandonado abierta?
            ya_existe = (
                db.query(CrmOportunidad)
                .filter(
                    CrmOportunidad.tenant_id == tenant_id,
                    CrmOportunidad.contacto_id == contacto.id,
                    CrmOportunidad.fuente == "carrito_abandonado",
                    CrmOportunidad.etapa.notin_(["cerrado_ganado", "cerrado_perdido", "congelado"]),
                    CrmOportunidad.eliminado == False,
                )
                .first()
            )
            if ya_existe:
                continue

            op = CrmOportunidad(
                tenant_id=tenant_id,
                contacto_id=contacto.id,
                nombre=f"Carrito abandonado — {user.email}",
                etapa="nuevo_lead",
                valor_estimado=monto,
                probabilidad=20,
                fuente="carrito_abandonado",
                descripcion=f"Carrito con {len(cart.items)} ítem(s) abandonado hace >{horas_min}h",
                creado_en=datetime.utcnow(),
                version=1,
            )
            db.add(op)
            creadas += 1

        db.commit()
        return {"oportunidades_creadas": creadas}
    finally:
        db.close()


# ── 9.2.3 Reactivar clientes inactivos ───────────────────────────────────────

def reactivar_clientes_inactivos(
    tenant_id: str, dias_inactivo: int = 90, host=None
) -> dict[str, Any]:
    """Clientes sin compras en N días → oportunidad de reactivación."""
    if not MULTITIENDA_DISPONIBLE:
        return {"error": "Multitienda no disponible", "procesados": 0}

    corte = datetime.utcnow() - timedelta(days=dias_inactivo)
    db = get_db(host)
    creadas = 0
    try:
        comportamientos = (
            db.query(CustomerBehavior)
            .filter(CustomerBehavior.last_order_date <= corte)
            .all()
        )
        for cb in comportamientos:
            user = db.query(User).filter(User.id == cb.customer_id).first()
            if not user or not user.email:
                continue
            contacto = _find_contacto_by_email(db, tenant_id, user.email)
            if contacto is None:
                continue

            ya_existe = (
                db.query(CrmOportunidad)
                .filter(
                    CrmOportunidad.tenant_id == tenant_id,
                    CrmOportunidad.contacto_id == contacto.id,
                    CrmOportunidad.fuente == "reactivacion",
                    CrmOportunidad.etapa.notin_(["cerrado_ganado", "cerrado_perdido", "congelado"]),
                    CrmOportunidad.eliminado == False,
                )
                .first()
            )
            if ya_existe:
                continue

            ticket = float(getattr(cb, "total_spent", 0) or 0)
            op = CrmOportunidad(
                tenant_id=tenant_id,
                contacto_id=contacto.id,
                nombre=f"Reactivación — {user.email}",
                etapa="por_contactar",
                valor_estimado=round(ticket * 0.3, 2),   # 30% del gasto histórico como estimado
                probabilidad=25,
                fuente="reactivacion",
                descripcion=f"Cliente inactivo {dias_inactivo}+ días. Último pedido: {cb.last_order_date}",
                creado_en=datetime.utcnow(),
                version=1,
            )
            db.add(op)
            creadas += 1

        db.commit()
        return {"oportunidades_creadas": creadas}
    finally:
        db.close()


# ── 9.2.4 Postventa de pedidos de alto valor ──────────────────────────────────

def procesar_pedidos_alto_valor(
    tenant_id: str, monto_min: float = 5000, dias_atras: int = 7, host=None
) -> dict[str, Any]:
    """Pedidos recientes > monto_min → actividad de seguimiento postventa."""
    if not MULTITIENDA_DISPONIBLE:
        return {"error": "Multitienda no disponible", "procesados": 0}

    desde = datetime.utcnow() - timedelta(days=dias_atras)
    db = get_db(host)
    creadas = 0
    try:
        pedidos = (
            db.query(Order)
            .filter(Order.total >= monto_min)
            .all()
        )
        for order in pedidos:
            email = getattr(order, "guest_email", None)
            if not email and order.customer_id:
                user = db.query(User).filter(User.id == order.customer_id).first()
                email = user.email if user else None
            if not email:
                continue

            contacto = _find_contacto_by_email(db, tenant_id, email)
            if contacto is None:
                continue

            ya_existe = (
                db.query(CrmActividad)
                .filter(
                    CrmActividad.tenant_id == tenant_id,
                    CrmActividad.contacto_id == contacto.id,
                    CrmActividad.titulo.like(f"%{getattr(order, 'order_number', order.id)}%"),
                    CrmActividad.eliminado == False,
                )
                .first()
            )
            if ya_existe:
                continue

            db.add(CrmActividad(
                tenant_id=tenant_id,
                contacto_id=contacto.id,
                tipo="llamada",
                titulo=f"Postventa pedido #{getattr(order, 'order_number', order.id)}",
                descripcion=f"Seguimiento postventa. Total: ${float(order.total):,.0f}",
                estado="pendiente",
                prioridad="alta",
                creado_en=datetime.utcnow(),
            ))
            creadas += 1

        db.commit()
        return {"actividades_creadas": creadas}
    finally:
        db.close()


# ── 9.2.5 Enriquecer scoring con datos de compra ─────────────────────────────

def enriquecer_scoring_lead(tenant_id: str, contacto_id: int, host=None) -> dict[str, Any]:
    """Combina scoring CRM con comportamiento de compra de Multitienda."""
    db = get_db(host)
    try:
        contacto = (
            db.query(CrmContacto)
            .filter(CrmContacto.id == contacto_id, CrmContacto.tenant_id == tenant_id, CrmContacto.eliminado == False)
            .first()
        )
        if not contacto:
            return {"error": "Contacto no encontrado"}

        enrichment: dict[str, Any] = {
            "contacto_id": contacto_id,
            "multitienda_disponible": MULTITIENDA_DISPONIBLE,
        }

        if MULTITIENDA_DISPONIBLE and contacto.email:
            user = db.query(User).filter(User.email == contacto.email).first()
            if user:
                cb = db.query(CustomerBehavior).filter(CustomerBehavior.customer_id == user.id).first()
                if cb:
                    total_orders = int(getattr(cb, "total_orders", 0) or 0)
                    total_spent = float(getattr(cb, "total_spent", 0) or 0)
                    ltv = float(getattr(cb, "predicted_lifetime_value", 0) or 0)
                    churn = float(getattr(cb, "churn_probability", 0) or 0)

                    # Bonus de score: hasta +25 por comportamiento de compra
                    bonus = 0
                    if total_orders >= 5:
                        bonus += 10
                    elif total_orders >= 2:
                        bonus += 5
                    if total_spent >= 10000:
                        bonus += 10
                    elif total_spent >= 2000:
                        bonus += 5
                    if churn < 0.3:
                        bonus += 5

                    nuevo_score = min(100, int(contacto.lead_score or 0) + bonus)
                    contacto.lead_score = nuevo_score
                    db.commit()

                    enrichment.update({
                        "total_orders": total_orders,
                        "total_spent": total_spent,
                        "predicted_lifetime_value": ltv,
                        "churn_probability": churn,
                        "score_bonus": bonus,
                        "nuevo_lead_score": nuevo_score,
                    })
                else:
                    enrichment["mensaje"] = "Sin datos de comportamiento de compra en Multitienda"
            else:
                enrichment["mensaje"] = "Email del contacto no encontrado en Multitienda"

        return enrichment
    finally:
        db.close()


# ── 9.2.6 Ciclo completo ─────────────────────────────────────────────────────

def ejecutar_ciclo_multitienda(tenant_id: str, host=None) -> dict[str, Any]:
    """Ejecuta todos los triggers de integración Multitienda → CRM."""
    if not MULTITIENDA_DISPONIBLE:
        return {"error": "Multitienda no disponible", "ejecutado": False}

    resultados: dict[str, Any] = {}
    for nombre, fn, kwargs in [
        ("sincronizar_clientes", sincronizar_clientes, {}),
        ("detectar_carritos_abandonados", detectar_carritos_abandonados, {"horas_min": 24}),
        ("reactivar_clientes_inactivos", reactivar_clientes_inactivos, {"dias_inactivo": 90}),
        ("procesar_pedidos_alto_valor", procesar_pedidos_alto_valor, {"monto_min": 5000, "dias_atras": 7}),
    ]:
        try:
            resultados[nombre] = fn(tenant_id, host=host, **kwargs)
        except Exception as exc:
            log.exception("Error en ciclo multitienda: %s — %s", nombre, exc)
            resultados[nombre] = {"error": str(exc)}

    return {"ejecutado": True, "resultados": resultados}
