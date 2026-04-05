"""
Fixtures compartidas para los tests del módulo repartidores.

Usa SQLite en memoria aislada por PID para no tocar la DB de producción.
El motor se parchea en core.db antes de importar cualquier store/controller.
"""
from __future__ import annotations

import os
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Generator

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Aseguramos que el root del proyecto esté en sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Configuración de entorno de test
# ---------------------------------------------------------------------------
os.environ["APP_ENV"] = "test"
os.environ["SQLITE_DB_PATH"] = ":memory:"

# Stub de fastapi_modulo.main para evitar arranque del servidor al importar
_fake_main = types.ModuleType("fastapi_modulo.main")
sys.modules.setdefault("fastapi_modulo.main", _fake_main)

# ---------------------------------------------------------------------------
# Motor SQLite en memoria: parcheamos core.db ANTES de importar los módulos
# ---------------------------------------------------------------------------
import fastapi_modulo.core.db as core_db

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TEST_SESSION_FACTORY = sessionmaker(
    bind=TEST_ENGINE, autocommit=False, autoflush=False
)

core_db.get_engine_for_host = lambda host=None: TEST_ENGINE
core_db.get_session_factory_for_host = lambda host=None: TEST_SESSION_FACTORY
core_db.get_current_engine = lambda: TEST_ENGINE
core_db.engine = TEST_ENGINE
core_db.SessionLocal = TEST_SESSION_FACTORY

# ---------------------------------------------------------------------------
# Creamos el schema al arrancar la sesión de tests
# ---------------------------------------------------------------------------
from fastapi_modulo.modulos.repartidores.modelos.db_models import (  # noqa: E402
    ensure_repartidores_schema,
)

ensure_repartidores_schema(bind=TEST_ENGINE)


# ---------------------------------------------------------------------------
# Fixture: sesión DB limpia por test (rollback automático)
# ---------------------------------------------------------------------------
@pytest.fixture()
def db() -> Generator[Session, None, None]:
    connection = TEST_ENGINE.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# Factories de datos de prueba
# ---------------------------------------------------------------------------
@pytest.fixture()
def zona_factory(db: Session):
    from fastapi_modulo.modulos.repartidores.modelos.store import create_zona
    from fastapi_modulo.modulos.repartidores.modelos.schemas import ZonaCreate

    seq = [0]

    def _make(**kwargs) -> object:
        seq[0] += 1
        data = ZonaCreate(
            name=kwargs.get("name", f"Zona Test {seq[0]}"),
            code=kwargs.get("code", f"ZTEST{seq[0]}"),
            description=kwargs.get("description", ""),
            ciudad=kwargs.get("ciudad", "CDMX"),
            radio_km=kwargs.get("radio_km", 5.0),
            active=kwargs.get("active", True),
        )
        return create_zona(db, data)

    return _make


@pytest.fixture()
def repartidor_factory(db: Session):
    from fastapi_modulo.modulos.repartidores.modelos.store import create_repartidor
    from fastapi_modulo.modulos.repartidores.modelos.schemas import RepartidorCreate

    seq = [0]

    def _make(**kwargs) -> object:
        seq[0] += 1
        data = RepartidorCreate(
            name=kwargs.get("name", f"Rep Test {seq[0]}"),
            codigo=kwargs.get("codigo", f"RTEST{seq[0]}"),
            telefono=kwargs.get("telefono", ""),
            email=kwargs.get("email", ""),
            tipo=kwargs.get("tipo", "interno"),
            state=kwargs.get("state", "available"),
            activo=kwargs.get("activo", True),
            zona_id=kwargs.get("zona_id", None),
            vehiculo_id=kwargs.get("vehiculo_id", None),
            negocio=kwargs.get("negocio", ""),
            sucursal=kwargs.get("sucursal", ""),
            sipet_username=kwargs.get("sipet_username", ""),
            tarifa_base=kwargs.get("tarifa_base", 100),
            bono_por_entrega=kwargs.get("bono_por_entrega", 10),
            meta_entregas_diarias=kwargs.get("meta_entregas_diarias", 10),
            max_entregas_simultaneas=kwargs.get("max_entregas_simultaneas", 5),
            notas=kwargs.get("notas", ""),
        )
        return create_repartidor(db, data)

    return _make


@pytest.fixture()
def entrega_factory(db: Session):
    from fastapi_modulo.modulos.repartidores.modelos.store import create_entrega
    from fastapi_modulo.modulos.repartidores.modelos.schemas import EntregaCreate

    seq = [0]

    def _make(**kwargs) -> object:
        seq[0] += 1
        data = EntregaCreate(
            referencia_externa=kwargs.get("referencia_externa", ""),
            cliente_nombre=kwargs.get("cliente_nombre", f"Cliente {seq[0]}"),
            cliente_telefono=kwargs.get("cliente_telefono", ""),
            origen=kwargs.get("origen", "Bodega Central"),
            destino=kwargs.get("destino", f"Calle {seq[0]} #123"),
            descripcion=kwargs.get("descripcion", ""),
            prioridad=kwargs.get("prioridad", "normal"),
            costo_envio=kwargs.get("costo_envio", 50),
            distancia_km=kwargs.get("distancia_km", 0.0),
            tiempo_estimado_min=kwargs.get("tiempo_estimado_min", 0),
            fecha_programada=kwargs.get(
                "fecha_programada", datetime.now() + timedelta(hours=2)
            ),
            zona_id=kwargs.get("zona_id", None),
            repartidor_id=kwargs.get("repartidor_id", None),
            liquidable=kwargs.get("liquidable", True),
        )
        return create_entrega(db, data)

    return _make


# ---------------------------------------------------------------------------
# Fixture: TestClient con auth inyectada vía middleware + dependency override
# ---------------------------------------------------------------------------
@pytest.fixture()
def build_client() -> Callable[..., TestClient]:
    from fastapi_modulo.modulos.repartidores.controladores.repartidores import (
        get_db,
        require_access,
        require_supervisor,
        require_write,
        router,
    )

    def _factory(
        role: str = "administrador",
        user: str = "tester",
    ) -> TestClient:
        app = FastAPI()

        @app.middleware("http")
        async def _inject_state(request: Request, call_next):
            request.state.user_name = user
            request.state.user_role = role
            request.state.tenant_id = "test"
            return await call_next(request)

        # Siempre usamos el motor de test en lugar del SessionLocal de producción
        def _get_test_db():
            session = TEST_SESSION_FACTORY()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = _get_test_db

        # Permite cualquier auth (pruebas de lógica, no de auth)
        app.dependency_overrides[require_access] = lambda: {"username": user, "role": role}
        app.dependency_overrides[require_write] = lambda: {"username": user, "role": role}
        app.dependency_overrides[require_supervisor] = lambda: {"username": user, "role": role}

        app.include_router(router)
        return TestClient(app, raise_server_exceptions=True)

    return _factory
