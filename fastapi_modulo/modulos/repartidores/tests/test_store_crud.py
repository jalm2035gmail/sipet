"""
Tests unitarios de las operaciones CRUD básicas en store.py.
Usa SQLite en memoria vía conftest.py.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Zonas
# ---------------------------------------------------------------------------

class TestZonaCRUD:
    def test_crear_zona(self, db, zona_factory):
        zona = zona_factory(name="Norte", code="NORTE", ciudad="CDMX")
        assert zona.id is not None
        assert zona.name == "Norte"
        assert zona.code == "NORTE"
        assert zona.active is True

    def test_codigo_zona_unico(self, db, zona_factory):
        zona_factory(code="UNICO1")
        with pytest.raises(ValueError, match="Ya existe una zona"):
            zona_factory(code="UNICO1")

    def test_listar_zonas_activas(self, db, zona_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import list_zonas
        zona_factory(active=True)
        zona_factory(active=True)
        zonas = list_zonas(db, solo_activas=True)
        assert len(zonas) >= 2

    def test_zona_inactiva_no_listada(self, db, zona_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import list_zonas
        from fastapi_modulo.modulos.repartidores.modelos.schemas import ZonaCreate
        from fastapi_modulo.modulos.repartidores.modelos.db_models import RepZona

        # Crear directamente con active=False
        obj = RepZona(name="Inactiva", code="INACT1", active=False)
        db.add(obj)
        db.commit()

        zonas = list_zonas(db, solo_activas=True)
        codigos = [z.code for z in zonas]
        assert "INACT1" not in codigos


# ---------------------------------------------------------------------------
# Repartidores
# ---------------------------------------------------------------------------

class TestRepartidorCRUD:
    def test_crear_repartidor(self, db, repartidor_factory):
        rep = repartidor_factory(name="Juan", codigo="JTEST1")
        assert rep.id is not None
        assert rep.name == "Juan"
        assert rep.state == "available"
        assert rep.activo is True

    def test_codigo_repartidor_unico(self, db, repartidor_factory):
        repartidor_factory(codigo="DUP1")
        with pytest.raises(ValueError, match="Ya existe un repartidor"):
            repartidor_factory(codigo="DUP1")

    def test_estado_invalido_rechazado(self, db):
        from fastapi_modulo.modulos.repartidores.modelos.store import create_repartidor
        from fastapi_modulo.modulos.repartidores.modelos.schemas import RepartidorCreate

        with pytest.raises(ValueError, match="Estado de repartidor inválido"):
            create_repartidor(
                db,
                RepartidorCreate(
                    name="Bad",
                    codigo="BADSTATE",
                    state="volando",
                    tarifa_base=0,
                    bono_por_entrega=0,
                ),
            )

    def test_get_repartidor_existente(self, db, repartidor_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import get_repartidor

        rep = repartidor_factory()
        found = get_repartidor(db, rep.id)
        assert found is not None
        assert found.id == rep.id

    def test_get_repartidor_inexistente(self, db):
        from fastapi_modulo.modulos.repartidores.modelos.store import get_repartidor

        assert get_repartidor(db, 99999) is None

    def test_update_repartidor(self, db, repartidor_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import update_repartidor
        from fastapi_modulo.modulos.repartidores.modelos.schemas import RepartidorUpdate

        rep = repartidor_factory(name="Original")
        updated = update_repartidor(db, rep.id, RepartidorUpdate(name="Actualizado"))
        assert updated.name == "Actualizado"

    def test_listar_solo_activos(self, db, repartidor_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import list_repartidores

        repartidor_factory(activo=True)
        repartidor_factory(activo=False)
        activos = list_repartidores(db, solo_activos=True)
        for r in activos:
            assert r.activo is True


# ---------------------------------------------------------------------------
# Entregas
# ---------------------------------------------------------------------------

class TestEntregaCRUD:
    def test_crear_entrega(self, db, entrega_factory):
        e = entrega_factory(cliente_nombre="María", prioridad="alta")
        assert e.id is not None
        assert e.state == "draft"
        assert e.folio.startswith("REP")

    def test_prioridad_invalida_rechazada(self, db):
        from fastapi_modulo.modulos.repartidores.modelos.store import create_entrega
        from fastapi_modulo.modulos.repartidores.modelos.schemas import EntregaCreate
        from datetime import datetime, timedelta

        with pytest.raises(ValueError, match="Prioridad inválida"):
            create_entrega(
                db,
                EntregaCreate(
                    cliente_nombre="Test",
                    destino="Destino",
                    prioridad="MUYURGENTE",
                    fecha_programada=datetime.now() + timedelta(hours=1),
                    costo_envio=0,
                ),
            )

    def test_folio_unico_secuencial(self, db, entrega_factory):
        e1 = entrega_factory()
        e2 = entrega_factory()
        assert e1.folio != e2.folio

    def test_get_entrega_existente(self, db, entrega_factory):
        from fastapi_modulo.modulos.repartidores.modelos.store import get_entrega

        e = entrega_factory()
        found = get_entrega(db, e.id)
        assert found is not None
        assert found.id == e.id

    def test_get_entrega_inexistente(self, db):
        from fastapi_modulo.modulos.repartidores.modelos.store import get_entrega

        assert get_entrega(db, 99999) is None
