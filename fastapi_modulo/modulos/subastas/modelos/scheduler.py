"""Scheduler de automatizaciones del módulo de subastas — Fase 8.2 / 8.3 / 8.5

Provee funciones de «tick» que realizan transiciones automáticas de estado:
  - tick_publish_scheduled  → scheduled + start_at<=ahora  → published
  - tick_close_auctions     → {live, published} + end_at<ahora → close_auction()
  - expire_overdue_awards   → delegada a store.expire_overdue_awards()
  - run_all_ticks           → ejecuta las tres anteriores en secuencia

Integración con la app FastAPI (agregar en el lifespan de la aplicación host):

    from contextlib import asynccontextmanager
    from modulos.subastas.modelos.scheduler import start_scheduler, stop_scheduler
    from modulos.subastas.controladores.subastas import SessionLocal

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        start_scheduler(SessionLocal, interval_seconds=60)
        yield
        await stop_scheduler()

El endpoint POST /subastas/api/scheduler/tick permite lanzar el ciclo
manualmente sin necesidad del scheduler en background.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db_models import Auction, AuctionState
from .store import close_auction, expire_overdue_awards, publish_auction

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Ticks individuales
# ─────────────────────────────────────────────────────────────────────────────

def tick_publish_scheduled(db: Session) -> int:
    """Publica automáticamente las subastas programadas cuyo start_at ya llegó.

    Transición: scheduled → published (cuando start_at <= ahora).
    Retorna el número de subastas publicadas en este tick.
    """
    now = datetime.utcnow()
    stmt = select(Auction).where(
        Auction.state == AuctionState.scheduled,
        Auction.start_at.is_not(None),
        Auction.start_at <= now,
    )
    auctions = list(db.scalars(stmt).all())
    published = 0
    for auction in auctions:
        try:
            publish_auction(db, auction.id, actor='scheduler')
            logger.info('Scheduler: subasta %d publicada automáticamente.', auction.id)
            published += 1
        except Exception as exc:
            logger.error('Scheduler: error publicando subasta %d: %s', auction.id, exc)
    return published


def tick_close_auctions(db: Session) -> int:
    """Cierra automáticamente las subastas cuyo end_at ya pasó.

    Actúa sobre subastas en estado 'live' o 'published'.
    Llama a close_auction() que aplica la lógica completa de adjudicación
    y precio de reserva.
    Retorna el número de subastas cerradas en este tick.
    """
    now = datetime.utcnow()
    closeable_states = {AuctionState.live, AuctionState.published}
    stmt = select(Auction).where(
        Auction.state.in_(closeable_states),
        Auction.end_at.is_not(None),
        Auction.end_at < now,
    )
    auctions = list(db.scalars(stmt).all())
    closed = 0
    for auction in auctions:
        try:
            close_auction(db, auction.id, actor='scheduler')
            logger.info('Scheduler: subasta %d cerrada automáticamente.', auction.id)
            closed += 1
        except Exception as exc:
            logger.error('Scheduler: error cerrando subasta %d: %s', auction.id, exc)
    return closed


# ─────────────────────────────────────────────────────────────────────────────
# Tick completo
# ─────────────────────────────────────────────────────────────────────────────

def run_all_ticks(db: Session) -> dict:
    """Ejecuta todos los ticks del scheduler en una sola llamada.

    Retorna un dict con el conteo de cambios realizados:
        {'published': int, 'closed': int, 'expired_awards': int}
    """
    return {
        'published': tick_publish_scheduled(db),
        'closed': tick_close_auctions(db),
        'expired_awards': expire_overdue_awards(db),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Background scheduler (asyncio)
# ─────────────────────────────────────────────────────────────────────────────

_scheduler_task: asyncio.Task | None = None


async def _scheduler_loop(session_factory, interval_seconds: int) -> None:
    """Bucle interno del scheduler. No llamar directamente; usar start_scheduler()."""
    while True:
        await asyncio.sleep(interval_seconds)
        db: Session = session_factory()
        try:
            result = run_all_ticks(db)
            if any(result.values()):
                logger.info('Scheduler tick completado: %s', result)
        except Exception as exc:
            logger.error('Scheduler tick error: %s', exc)
        finally:
            db.close()


def start_scheduler(session_factory, interval_seconds: int = 60) -> None:
    """Inicia el scheduler en background (asyncio.Task).

    Llamar desde el lifespan de la app FastAPI después del primer yield.
    Si ya hay un scheduler en ejecución, no crea uno nuevo.

    Args:
        session_factory: Callable que retorna una Session de SQLAlchemy
                         (p.ej. SessionLocal de controladores/subastas.py).
        interval_seconds: Intervalo entre ticks en segundos (default: 60).
    """
    global _scheduler_task
    if _scheduler_task is not None and not _scheduler_task.done():
        logger.warning('Scheduler ya está en ejecución; ignorando start_scheduler().')
        return
    _scheduler_task = asyncio.create_task(
        _scheduler_loop(session_factory, interval_seconds),
        name='subastas_scheduler',
    )
    logger.info('Scheduler de subastas iniciado (intervalo: %ds).', interval_seconds)


async def stop_scheduler() -> None:
    """Detiene el scheduler en background de forma limpia.

    Llamar desde el lado de teardown del lifespan de la app FastAPI.
    """
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        return
    _scheduler_task.cancel()
    try:
        await _scheduler_task
    except asyncio.CancelledError:
        pass
    finally:
        _scheduler_task = None
    logger.info('Scheduler de subastas detenido.')
