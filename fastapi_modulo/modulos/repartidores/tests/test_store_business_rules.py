"""
Tests de reglas de negocio y máquina de estados para el módulo repartidores.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Máquina de estados — transiciones permitidas
# ---------------------------------------------------------------------------

class TestMaquinaDeEstados:
    """Verifica que el mapa TRANSITIONS sea correcto y que store lo aplique."""

    def test_transicion_draft_a_assigned(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory()
        entrega = entrega_factory()
        assert entrega.state == "draft"

        result = assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        assert result.state == "assigned"

    def test_transicion_assigned_a_picked_up(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

        result = update_entrega_state(
            db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up")
        )
        assert result.state == "picked_up"

    def test_transicion_picked_up_a_in_transit(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))

        result = update_entrega_state(
            db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit")
        )
        assert result.state == "in_transit"

    def test_transicion_in_transit_a_delivered(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit"))

        result = update_entrega_state(
            db,
            entrega.id,
            ActualizarEstadoEntregaInput(
                state="delivered", evidencia_entrega="Foto firmada por el cliente"
            ),
        )
        assert result.state == "delivered"
        assert result.fecha_entrega is not None

    def test_transicion_invalida_rechazada(self, db, entrega_factory):
        """draft → in_transit no está permitido."""
        from fastapi_modulo.modulos.repartidores.modelos.store import update_entrega_state
        from fastapi_modulo.modulos.repartidores.modelos.schemas import ActualizarEstadoEntregaInput

        entrega = entrega_factory()
        with pytest.raises(ValueError, match="Transición de estado no permitida"):
            update_entrega_state(
                db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit")
            )

    def test_transicion_delivered_bloqueada(self, db, repartidor_factory, entrega_factory):
        """delivered es estado terminal — no hay transición válida."""
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit"))
        update_entrega_state(
            db,
            entrega.id,
            ActualizarEstadoEntregaInput(
                state="delivered", evidencia_entrega="Evidencia OK final"
            ),
        )

        with pytest.raises(ValueError, match="Transición de estado no permitida"):
            update_entrega_state(
                db, entrega.id, ActualizarEstadoEntregaInput(state="assigned")
            )

    def test_cancelled_es_estado_terminal(self, db, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import update_entrega_state
        from fastapi_modulo.modulos.repartidores.modelos.schemas import ActualizarEstadoEntregaInput

        entrega = entrega_factory()
        update_entrega_state(
            db,
            entrega.id,
            ActualizarEstadoEntregaInput(state="cancelled", motivo_cancelacion="Cliente canceló el pedido"),
        )
        with pytest.raises(ValueError, match="Transición de estado no permitida"):
            update_entrega_state(
                db, entrega.id, ActualizarEstadoEntregaInput(state="draft")
            )

    def test_failed_puede_reasignarse(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(
            db,
            entrega.id,
            ActualizarEstadoEntregaInput(state="failed", motivo_cancelacion="No hubo acceso al edificio"),
        )
        assert entrega.state == "failed"

        result = assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        assert result.state == "assigned"


# ---------------------------------------------------------------------------
# Reglas de negocio — asignación
# ---------------------------------------------------------------------------

class TestReglasAsignacion:
    def test_repartidor_offline_no_asignable(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory(state="offline")
        entrega = entrega_factory()
        with pytest.raises(ValueError, match="offline"):
            assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

    def test_repartidor_suspended_no_asignable(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory(state="suspended")
        entrega = entrega_factory()
        with pytest.raises(ValueError, match="suspended"):
            assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

    def test_repartidor_inactivo_no_asignable(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory(activo=False)
        entrega = entrega_factory()
        with pytest.raises(ValueError, match="no disponible"):
            assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

    def test_limite_entregas_simultaneas(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory(max_entregas_simultaneas=2)
        e1 = entrega_factory()
        e2 = entrega_factory()
        e3 = entrega_factory()  # Esta debe ser rechazada

        assign_entrega(db, e1.id, AsignarEntregaInput(repartidor_id=rep.id))
        assign_entrega(db, e2.id, AsignarEntregaInput(repartidor_id=rep.id))

        with pytest.raises(ValueError, match="límite"):
            assign_entrega(db, e3.id, AsignarEntregaInput(repartidor_id=rep.id))

    def test_repartidor_pasa_a_busy_al_asignar(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega, get_repartidor
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput

        rep = repartidor_factory(state="available")
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

        updated_rep = get_repartidor(db, rep.id)
        assert updated_rep.state == "busy"

    def test_repartidor_vuelve_a_available_al_entregar(
        self, db, repartidor_factory, entrega_factory
    ):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
            get_repartidor,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit"))
        update_entrega_state(
            db,
            entrega.id,
            ActualizarEstadoEntregaInput(
                state="delivered", evidencia_entrega="Foto entregada al cliente"
            ),
        )

        updated_rep = get_repartidor(db, rep.id)
        assert updated_rep.state == "available"


# ---------------------------------------------------------------------------
# Reglas de negocio — evidencia y motivo
# ---------------------------------------------------------------------------

class TestReglasEvidenciaMotivo:
    def test_delivered_sin_evidencia_rechazado(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="in_transit"))

        with pytest.raises(ValueError, match="evidencia"):
            update_entrega_state(
                db,
                entrega.id,
                ActualizarEstadoEntregaInput(state="delivered", evidencia_entrega="cort"),
            )

    def test_cancelled_sin_motivo_rechazado(self, db, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import update_entrega_state
        from fastapi_modulo.modulos.repartidores.modelos.schemas import ActualizarEstadoEntregaInput

        entrega = entrega_factory()
        with pytest.raises(ValueError, match="motivo"):
            update_entrega_state(
                db,
                entrega.id,
                ActualizarEstadoEntregaInput(state="cancelled", motivo_cancelacion="no"),
            )

    def test_failed_sin_motivo_rechazado(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

        with pytest.raises(ValueError, match="motivo"):
            update_entrega_state(
                db,
                entrega.id,
                ActualizarEstadoEntregaInput(state="failed", motivo_cancelacion="no"),
            )


# ---------------------------------------------------------------------------
# Trazabilidad — logs
# ---------------------------------------------------------------------------

class TestEntregaLog:
    def test_asignacion_genera_log(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import assign_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import AsignarEntregaInput
        from fastapi_modulo.modulos.repartidores.modelos.db_models import RepEntregaLog

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))

        logs = db.query(RepEntregaLog).filter(RepEntregaLog.entrega_id == entrega.id).all()
        tipos = [log.tipo for log in logs]
        assert "asignacion" in tipos

    def test_cambio_estado_genera_log(self, db, repartidor_factory, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import (
            assign_entrega,
            update_entrega_state,
        )
        from fastapi_modulo.modulos.repartidores.modelos.schemas import (
            AsignarEntregaInput,
            ActualizarEstadoEntregaInput,
        )
        from fastapi_modulo.modulos.repartidores.modelos.db_models import RepEntregaLog

        rep = repartidor_factory()
        entrega = entrega_factory()
        assign_entrega(db, entrega.id, AsignarEntregaInput(repartidor_id=rep.id))
        update_entrega_state(db, entrega.id, ActualizarEstadoEntregaInput(state="picked_up"))

        logs = db.query(RepEntregaLog).filter(RepEntregaLog.entrega_id == entrega.id).all()
        estados_nuevos = [log.estado_nuevo for log in logs]
        assert "picked_up" in estados_nuevos
