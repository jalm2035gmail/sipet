"""
Tests de generación y validación de liquidaciones.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest


def _make_delivered_entrega(db, repartidor, entrega_factory, *, fecha_entrega=None):
    """Crea una entrega y la lleva a estado 'delivered' en la sesión dada."""
    from fastapi_modulo.modulos.repartidores.modelos.store import (
        assign_entrega,
        update_entrega_state,
    )
    from fastapi_modulo.modulos.repartidores.modelos.schemas import (
        AsignarEntregaInput,
        ActualizarEstadoEntregaInput,
    )

    entrega = entrega_factory()
    assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=repartidor.id))
    update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))
    update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit"))
    update_entrega_state(
        db,
        entrega.id,
        ActualizarEstadoEntregaInput(
            state="delivered", evidencia_entrega="Foto entregada al destinatario"
        ),
    )
    # Ajusta la fecha de entrega para que caiga en el periodo deseado
    if fecha_entrega is not None:
        from fastapi_modulo.modulos.repartidores.modelos.db_models import RepEntrega
        db.query(RepEntrega).filter(RepEntrega.id == entrega.id).update(
            {"fecha_entrega": fecha_entrega}
        )
        db.commit()
        db.refresh(entrega)
    return entrega


class TestLiquidacion:
    def test_generar_liquidacion_basica(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import generate_liquidacion
        from fastapi_modulo.modulos.repartidores.modelos.schemas import GenerarLiquidacionInput

        rep = repartidor_factory(tarifa_base=100, bono_por_entrega=20)
        today = date.today()
        fecha_entrega = datetime.combine(today, datetime.min.time()) + timedelta(hours=8)

        _make_delivered_entrega(db, rep, entrega_factory, fecha_entrega=fecha_entrega)
        _make_delivered_entrega(db, rep, entrega_factory, fecha_entrega=fecha_entrega)

        liq = generate_liquidacion(
            db,
            GenerarLiquidacionInput(
                repartidor_id=rep.id,
                fecha_inicio=today,
                fecha_fin=today,
            ),
        )
        assert liq.id is not None
        assert liq.total_entregas == 2
        # 2 × (100 base + 20 bono) = 240
        assert float(liq.total_base) == pytest.approx(200.0)
        assert float(liq.total_bonos) == pytest.approx(40.0)
        assert float(liq.total_pagar) == pytest.approx(240.0)
        assert liq.state == "draft"

    def test_canceladas_excluidas_de_liquidacion(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            generate_liquidacion,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            GenerarLiquidacionInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory(tarifa_base=100, bono_por_entrega=0)
        today = date.today()
        fecha_entrega = datetime.combine(today, datetime.min.time()) + timedelta(hours=9)

        # Una entregada, una cancelada
        _make_delivered_entrega(db, rep, entrega_factory, fecha_entrega=fecha_entrega)
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        e_cancelada = entrega_factory()
        assign_entrega(db, e_cancelada.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(
            db,
            e_cancelada.id,
            ActualizarEstadoEntregaInput(
                state="cancelled", motivo_cancelacion="Dirección incorrecta"
            ),
        )

        liq = generate_liquidacion(
            db,
            GenerarLiquidacionInput(
                repartidor_id=rep.id,
                fecha_inicio=today,
                fecha_fin=today,
            ),
        )
        # Solo 1 entrega liquidable
        assert liq.total_entregas == 1
        assert float(liq.total_pagar) == pytest.approx(100.0)

    def test_sin_entregas_liquidables_rechazado(self, db, repartidor_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import generate_liquidacion
        from fastapi_modulo.modulos.repartidores.modelos.schemas import GenerarLiquidacionInput

        rep = repartidor_factory()
        today = date.today()
        with pytest.raises(ValueError, match="No hay entregas liquidables"):
            generate_liquidacion(
                db,
                GenerarLiquidacionInput(
                    repartidor_id=rep.id,
                    fecha_inicio=today,
                    fecha_fin=today,
                ),
            )

    def test_reliquidacion_bloqueada_si_approved(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import generate_liquidacion
        from fastapi_modulo.modulos.repartidores.modelos.schemas import GenerarLiquidacionInput
        from fastapi_modulo.modulos.repartidores.modelos.db_models import RepLiquidacion

        rep = repartidor_factory(tarifa_base=100, bono_por_entrega=0)
        today = date.today()
        fecha_entrega = datetime.combine(today, datetime.min.time()) + timedelta(hours=10)

        _make_delivered_entrega(db, rep, entrega_factory, fecha_entrega=fecha_entrega)

        liq = generate_liquidacion(
            db,
            GenerarLiquidacionInput(
                repartidor_id=rep.id,
                fecha_inicio=today,
                fecha_fin=today,
            ),
        )
        # Marcar como aprobada directamente en DB
        db.query(RepLiquidacion).filter(RepLiquidacion.id == liq.id).update(
            {"state": "approved"}
        )
        db.commit()

        # Segunda liquidación del mismo periodo debe fallar
        with pytest.raises(ValueError, match="Ya existe una liquidación"):
            generate_liquidacion(
                db,
                GenerarLiquidacionInput(
                    repartidor_id=rep.id,
                    fecha_inicio=today,
                    fecha_fin=today,
                ),
            )

    def test_descuentos_reducen_total(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import generate_liquidacion
        from fastapi_modulo.modulos.repartidores.modelos.schemas import GenerarLiquidacionInput

        rep = repartidor_factory(tarifa_base=200, bono_por_entrega=0)
        today = date.today()
        fecha_entrega = datetime.combine(today, datetime.min.time()) + timedelta(hours=11)

        _make_delivered_entrega(db, rep, entrega_factory, fecha_entrega=fecha_entrega)

        liq = generate_liquidacion(
            db,
            GenerarLiquidacionInput(
                repartidor_id=rep.id,
                fecha_inicio=today,
                fecha_fin=today,
                descuentos=50,
            ),
        )
        assert float(liq.total_descuentos) == pytest.approx(50.0)
        assert float(liq.total_pagar) == pytest.approx(150.0)  # 200 - 50

    def test_repartidor_inexistente_rechazado(self, db):
        from fastapi_modulo.modulos.repartidores.modelos.store import generate_liquidacion
        from fastapi_modulo.modulos.repartidores.modelos.schemas import GenerarLiquidacionInput

        with pytest.raises(ValueError, match="Repartidor no encontrado"):
            generate_liquidacion(
                db,
                GenerarLiquidacionInput(
                    repartidor_id=99999,
                    fecha_inicio=date.today(),
                    fecha_fin=date.today(),
                ),
            )
