from __future__ import annotations

import os
from typing import Any

try:
    from celery import Celery
    from celery.schedules import crontab
except ImportError:  # pragma: no cover
    Celery = None  # type: ignore[assignment,misc]
    crontab = None  # type: ignore[assignment]

_BROKER_URL = (
    os.environ.get('REPARTIDORES_CELERY_BROKER_URL')
    or os.environ.get('CELERY_BROKER_URL')
    or os.environ.get('REDIS_URL')
    or 'redis://localhost:6379/0'
).strip()

_RESULT_BACKEND = (
    os.environ.get('REPARTIDORES_CELERY_RESULT_BACKEND')
    or os.environ.get('CELERY_RESULT_BACKEND')
    or _BROKER_URL
).strip()


def get_celery_app() -> Any:
    if Celery is None:  # pragma: no cover
        return None
    app = Celery(
        'sipet_repartidores',
        broker=_BROKER_URL,
        backend=_RESULT_BACKEND,
        include=['fastapi_modulo.modulos.repartidores.servicios.tareas_celery'],
    )
    app.conf.task_default_queue = 'repartidores'
    app.conf.task_track_started = True
    app.conf.task_serializer = 'json'
    app.conf.accept_content = ['json']
    app.conf.result_serializer = 'json'
    app.conf.beat_schedule = {
        # Cierra entregas fallidas antiguas — todos los días a la 01:00
        'repartidores-cerrar-fallidas-diario': {
            'task': 'repartidores.cerrar_entregas_fallidas',
            'schedule': crontab(hour=1, minute=0) if crontab else 86400,
        },
        # Verifica alertas operativas — cada 15 minutos
        'repartidores-alertas-cada-15-min': {
            'task': 'repartidores.verificar_alertas',
            'schedule': 900,
        },
        # Recordatorio a repartidores — todos los días a las 08:00
        'repartidores-recordatorio-diario': {
            'task': 'repartidores.recordatorio_repartidores',
            'schedule': crontab(hour=8, minute=0) if crontab else 86400,
        },
        # Recálculo de KPIs — todos los días a las 00:30
        'repartidores-kpis-diarios': {
            'task': 'repartidores.recalcular_kpis',
            'schedule': crontab(hour=0, minute=30) if crontab else 86400,
        },
    }
    return app


celery_app = get_celery_app()

__all__ = ['celery_app', 'get_celery_app']
