"""Hooks de notificación del módulo de subastas — Fase 8.4

Define los contratos (interfaces) de notificación que deben implementar los
adaptadores externos. La implementación real corresponde al módulo
avan_notificaciones cuando esté disponible.

Uso — registrar handlers externos:

    from modulos.subastas.modelos.notificaciones import registry

    @registry.on_bid_placed
    def notificar_nueva_puja(*, auction_id, bidder_id, amount):
        # enviar notificación push / email / websocket
        ...

    @registry.on_auction_awarded
    def notificar_adjudicacion(*, auction_id, bidder_id, final_amount):
        ...

Uso — disparar hooks desde el store u otros adaptadores:

    from modulos.subastas.modelos.notificaciones import registry

    registry.fire_bid_placed(auction_id=1, bidder_id=3, amount=1500.00)

Los handlers se ejecutan de forma síncrona en el mismo hilo. Si necesitas
llamadas asíncronas, el handler debe schedulear la corrutina externamente
(p.ej. con asyncio.create_task dentro de un context loop activo).

Los errores en handlers individuales se capturan y loguean sin interrumpir
el flujo principal de la aplicación.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


class HookRegistry:
    """Registro central de hooks de notificación del módulo de subastas."""

    def __init__(self) -> None:
        self._on_bid_placed: list[Callable] = []
        self._on_auction_awarded: list[Callable] = []
        self._on_payment_due: list[Callable] = []
        self._on_award_expired: list[Callable] = []

    # ── Registradores (usables como decoradores o llamadores directos) ────────

    def on_bid_placed(self, fn: Callable) -> Callable:
        """Registra un handler para el evento 'nueva puja registrada'.

        El handler recibe kwargs:
            auction_id (int), bidder_id (int), amount (float)
        """
        self._on_bid_placed.append(fn)
        return fn

    def on_auction_awarded(self, fn: Callable) -> Callable:
        """Registra un handler para el evento 'subasta adjudicada'.

        El handler recibe kwargs:
            auction_id (int), bidder_id (int | None), final_amount (float)
        """
        self._on_auction_awarded.append(fn)
        return fn

    def on_payment_due(self, fn: Callable) -> Callable:
        """Registra un handler para el evento 'pago pendiente / próximo a vencer'.

        El handler recibe kwargs:
            award_id (int), auction_id (int), bidder_id (int | None),
            due_at (datetime)
        """
        self._on_payment_due.append(fn)
        return fn

    def on_award_expired(self, fn: Callable) -> Callable:
        """Registra un handler para el evento 'adjudicación expirada por falta de pago'.

        El handler recibe kwargs:
            award_id (int), auction_id (int), bidder_id (int | None)
        """
        self._on_award_expired.append(fn)
        return fn

    # ── Disparadores ─────────────────────────────────────────────────────────

    def fire_bid_placed(self, *, auction_id: int, bidder_id: int, amount: float) -> None:
        self._fire(self._on_bid_placed, auction_id=auction_id, bidder_id=bidder_id, amount=amount)

    def fire_auction_awarded(
        self,
        *,
        auction_id: int,
        bidder_id: int | None,
        final_amount: float,
    ) -> None:
        self._fire(
            self._on_auction_awarded,
            auction_id=auction_id,
            bidder_id=bidder_id,
            final_amount=final_amount,
        )

    def fire_payment_due(
        self,
        *,
        award_id: int,
        auction_id: int,
        bidder_id: int | None,
        due_at: datetime,
    ) -> None:
        self._fire(
            self._on_payment_due,
            award_id=award_id,
            auction_id=auction_id,
            bidder_id=bidder_id,
            due_at=due_at,
        )

    def fire_award_expired(
        self,
        *,
        award_id: int,
        auction_id: int,
        bidder_id: int | None,
    ) -> None:
        self._fire(
            self._on_award_expired,
            award_id=award_id,
            auction_id=auction_id,
            bidder_id=bidder_id,
        )

    # ── Interno ───────────────────────────────────────────────────────────────

    def _fire(self, handlers: list[Callable], **kwargs) -> None:
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception as exc:
                logger.error(
                    'Hook error en %s(%s): %s',
                    getattr(handler, '__name__', repr(handler)),
                    ', '.join(f'{k}={v!r}' for k, v in kwargs.items()),
                    exc,
                )

    def clear(self) -> None:
        """Elimina todos los handlers registrados. Útil en tests."""
        self._on_bid_placed.clear()
        self._on_auction_awarded.clear()
        self._on_payment_due.clear()
        self._on_award_expired.clear()


# Instancia global — importar desde cualquier módulo que necesite notificaciones.
registry = HookRegistry()
