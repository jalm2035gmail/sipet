from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.repartidores.modelos.db_models import (
    RepEntrega,
    RepRepartidor,
    RepZona,
)


def get_alertas_operativas(
    db: Session,
    max_min_sin_recoleccion: int = 60,
) -> list[dict[str, Any]]:
    """Retorna todas las alertas operativas activas en este momento."""
    alertas: list[dict[str, Any]] = []
    alertas.extend(_alertas_entregas_vencidas(db))
    alertas.extend(_alertas_sin_recoleccion(db, max_min_sin_recoleccion))
    alertas.extend(_alertas_zonas_sin_repartidores(db))
    return alertas


def _alertas_entregas_vencidas(db: Session) -> list[dict[str, Any]]:
    """Entregas en draft cuya fecha_programada ya pasó."""
    now = datetime.utcnow()
    entregas = (
        db.query(RepEntrega)
        .filter(RepEntrega.state == 'draft', RepEntrega.fecha_programada < now)
        .order_by(RepEntrega.fecha_programada)
        .all()
    )
    resultado = []
    for e in entregas:
        minutos = int((now - e.fecha_programada).total_seconds() / 60)
        resultado.append({
            'tipo': 'entrega_vencida_sin_asignar',
            'severidad': 'alta',
            'entrega_id': e.id,
            'folio': e.folio,
            'fecha_programada': e.fecha_programada.isoformat(),
            'minutos_vencida': minutos,
            'mensaje': f'Entrega {e.folio} lleva {minutos} min vencida sin asignar.',
        })
    return resultado


def _alertas_sin_recoleccion(db: Session, max_min: int = 60) -> list[dict[str, Any]]:
    """Entregas asignadas hace más de max_min minutos sin pasar a picked_up."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_min)
    entregas = (
        db.query(RepEntrega)
        .filter(
            RepEntrega.state == 'assigned',
            RepEntrega.fecha_asignacion.isnot(None),
            RepEntrega.fecha_asignacion < cutoff,
        )
        .order_by(RepEntrega.fecha_asignacion)
        .all()
    )
    resultado = []
    for e in entregas:
        minutos = int((datetime.utcnow() - e.fecha_asignacion).total_seconds() / 60)
        resultado.append({
            'tipo': 'entrega_asignada_sin_recoleccion',
            'severidad': 'media',
            'entrega_id': e.id,
            'folio': e.folio,
            'repartidor_id': e.repartidor_id,
            'minutos_sin_recoleccion': minutos,
            'mensaje': (
                f'Entrega {e.folio} lleva {minutos} min asignada sin ser recolectada.'
            ),
        })
    return resultado


def _alertas_zonas_sin_repartidores(db: Session) -> list[dict[str, Any]]:
    """Zonas activas con entregas pendientes pero sin repartidor disponible."""
    zonas_activas = db.query(RepZona).filter(RepZona.active == True).all()
    alertas = []
    for zona in zonas_activas:
        tiene_rep = (
            db.query(RepRepartidor)
            .filter(
                RepRepartidor.zona_id == zona.id,
                RepRepartidor.state == 'available',
                RepRepartidor.activo == True,
            )
            .first()
        )
        if tiene_rep:
            continue
        tiene_entrega = (
            db.query(RepEntrega)
            .filter(
                RepEntrega.zona_id == zona.id,
                RepEntrega.state.in_(['draft', 'assigned']),
            )
            .first()
        )
        if tiene_entrega:
            alertas.append({
                'tipo': 'zona_sin_repartidores_disponibles',
                'severidad': 'media',
                'zona_id': zona.id,
                'zona_code': zona.code,
                'zona_name': zona.name,
                'mensaje': (
                    f'Zona {zona.name} ({zona.code}) tiene entregas pendientes '
                    f'pero ningún repartidor disponible.'
                ),
            })
    return alertas
