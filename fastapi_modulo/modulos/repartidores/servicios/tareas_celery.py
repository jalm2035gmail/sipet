from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi_modulo.modulos.repartidores.servicios.celery_app import celery_app

logger = logging.getLogger(__name__)

_RETRY_KWARGS = {
    'autoretry_for': (Exception,),
    'max_retries': 3,
    'default_retry_delay': 60,
    'retry_backoff': True,
    'retry_backoff_max': 300,
    'retry_jitter': True,
}


@celery_app.task(name='repartidores.cerrar_entregas_fallidas', **_RETRY_KWARGS)
def cerrar_entregas_fallidas_task(max_dias: int = 7, **kwargs) -> dict:
    """Cierra automáticamente entregas en estado 'failed' con más de max_dias días."""
    from fastapi_modulo.core.db import SessionLocal
    from fastapi_modulo.modulos.repartidores.modelos.db_models import RepEntrega, RepEntregaLog

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=max_dias)
        entregas = (
            db.query(RepEntrega)
            .filter(RepEntrega.state == 'failed', RepEntrega.updated_at < cutoff)
            .all()
        )
        for e in entregas:
            e.state = 'cancelled'
            e.motivo_cancelacion = (
                f'Cierre automático: más de {max_dias} días en estado failed.'
            )
            e.updated_at = datetime.utcnow()
            db.add(RepEntregaLog(
                entrega_id=e.id,
                tipo='estado',
                estado_anterior='failed',
                estado_nuevo='cancelled',
                notas=f'Cierre automático por tarea programada (max_dias={max_dias}).',
            ))
        db.commit()
        logger.info('cerrar_entregas_fallidas_task: cerradas=%s', len(entregas))
        return {'status': 'ok', 'cerradas': len(entregas)}
    except Exception as exc:
        db.rollback()
        logger.error('cerrar_entregas_fallidas_task: error=%s', exc)
        raise
    finally:
        db.close()


@celery_app.task(name='repartidores.verificar_alertas', **_RETRY_KWARGS)
def verificar_alertas_task(**kwargs) -> dict:
    """Detecta alertas operativas cada 15 min y las persiste como notificaciones internas."""
    from fastapi_modulo.core.db import SessionLocal
    from fastapi_modulo.modulos.repartidores.modelos.db_models import RepNotificacionLog
    from fastapi_modulo.modulos.repartidores.servicios.alertas import get_alertas_operativas

    db = SessionLocal()
    try:
        alertas = get_alertas_operativas(db)
        for alerta in alertas:
            db.add(RepNotificacionLog(
                tipo=alerta['tipo'],
                canal='sistema',
                destinatario='supervisores',
                mensaje=alerta['mensaje'],
                entrega_id=alerta.get('entrega_id'),
                repartidor_id=alerta.get('repartidor_id'),
                estado='registrada',
            ))
        db.commit()
        logger.info('verificar_alertas_task: alertas=%s', len(alertas))
        return {'status': 'ok', 'alertas': len(alertas)}
    except Exception as exc:
        db.rollback()
        logger.error('verificar_alertas_task: error=%s', exc)
        raise
    finally:
        db.close()


@celery_app.task(name='repartidores.recordatorio_repartidores', **_RETRY_KWARGS)
def recordatorio_repartidores_task(**kwargs) -> dict:
    """Envía recordatorio diario a repartidores con entregas pendientes del día."""
    from fastapi_modulo.core.db import SessionLocal
    from fastapi_modulo.modulos.repartidores.modelos.db_models import RepEntrega, RepRepartidor
    from fastapi_modulo.modulos.repartidores.servicios.notificaciones import (
        notif_recordatorio_pendientes_directo,
    )

    db = SessionLocal()
    try:
        repartidores = (
            db.query(RepRepartidor)
            .filter(
                RepRepartidor.activo == True,
                RepRepartidor.state.in_(['available', 'busy']),
            )
            .all()
        )
        enviados = 0
        for rep in repartidores:
            pendientes = (
                db.query(RepEntrega)
                .filter(
                    RepEntrega.repartidor_id == rep.id,
                    RepEntrega.state.in_(['assigned', 'picked_up', 'in_transit']),
                )
                .all()
            )
            if pendientes:
                notif_recordatorio_pendientes_directo(db, rep, pendientes)
                enviados += 1
        db.commit()
        logger.info('recordatorio_repartidores_task: enviados=%s', enviados)
        return {'status': 'ok', 'repartidores_notificados': enviados}
    except Exception as exc:
        db.rollback()
        logger.error('recordatorio_repartidores_task: error=%s', exc)
        raise
    finally:
        db.close()


@celery_app.task(name='repartidores.recalcular_kpis', **_RETRY_KWARGS)
def recalcular_kpis_task(**kwargs) -> dict:
    """Recalcula y registra KPIs diarios del módulo (se usa para dashboard)."""
    from fastapi_modulo.core.db import SessionLocal
    from fastapi_modulo.modulos.repartidores.modelos.db_models import (
        RepEntrega,
        RepIncidencia,
        RepRepartidor,
    )

    db = SessionLocal()
    try:
        totales = {
            'repartidores_activos': (
                db.query(RepRepartidor).filter(RepRepartidor.activo == True).count()
            ),
            'entregas_totales': db.query(RepEntrega).count(),
            'entregas_entregadas': (
                db.query(RepEntrega).filter(RepEntrega.state == 'delivered').count()
            ),
            'entregas_canceladas': (
                db.query(RepEntrega).filter(RepEntrega.state == 'cancelled').count()
            ),
            'incidencias_abiertas': (
                db.query(RepIncidencia).filter(RepIncidencia.state == 'open').count()
            ),
            'calculado_at': datetime.utcnow().isoformat(),
        }
        logger.info('recalcular_kpis_task: %s', totales)
        return {'status': 'ok', **totales}
    except Exception as exc:
        logger.error('recalcular_kpis_task: error=%s', exc)
        raise
    finally:
        db.close()
