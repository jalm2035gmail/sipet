from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.crm.modelos.db_models import (
    CrmActividad,
    CrmCampania,
    CrmContacto,
    CrmContactoCampania,
    CrmEvento,
    CrmNota,
    CrmOportunidad,
)


def _active_host(host: str | None = None) -> str:
    return host if host is not None else core_db.get_request_host()


def ensure_crm_schema(host: str | None = None) -> None:
    active_host = _active_host(host)
    engine = core_db.get_engine_for_host(active_host)
    MAIN.metadata.create_all(
        bind=engine,
        tables=[
            CrmContacto.__table__,
            CrmOportunidad.__table__,
            CrmActividad.__table__,
            CrmNota.__table__,
            CrmCampania.__table__,
            CrmContactoCampania.__table__,
            CrmEvento.__table__,
        ],
        checkfirst=True,
    )
    _ensure_crm_columns(engine)


def _ensure_crm_columns(engine) -> None:
    inspector = inspect(engine)
    column_specs = {
        "crm_contactos": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "fuente": "VARCHAR(50) NOT NULL DEFAULT 'manual'",
            "sucursal": "VARCHAR(100) NOT NULL DEFAULT ''",
            "fuente_detalle": "VARCHAR(120) NOT NULL DEFAULT ''",
            "lead_score": "INTEGER NOT NULL DEFAULT 0",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "asignado_a": "VARCHAR(100) NOT NULL DEFAULT ''",
            "creado_en": "TIMESTAMP",
            "actualizado_en": "TIMESTAMP",
        },
        "crm_oportunidades": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "fecha_cierre_real": "DATE",
            "cerrado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "cerrado_en": "TIMESTAMP",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "asignado_a": "VARCHAR(100) NOT NULL DEFAULT ''",
            "responsable": "VARCHAR(100) NOT NULL DEFAULT ''",
            "descripcion": "TEXT",
            "sucursal": "VARCHAR(100) NOT NULL DEFAULT ''",
            "ultimo_movimiento_en": "TIMESTAMP",
            "creado_en": "TIMESTAMP",
            "actualizado_en": "TIMESTAMP",
        },
        "crm_actividades": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "fecha_completada": "TIMESTAMP",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "asignado_a": "VARCHAR(100) NOT NULL DEFAULT ''",
            "responsable": "VARCHAR(100) NOT NULL DEFAULT ''",
        },
        "crm_notas": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
        },
        "crm_campanias": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "cerrado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "cerrado_en": "TIMESTAMP",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "asignado_a": "VARCHAR(100) NOT NULL DEFAULT ''",
            "resultado": "TEXT",
        },
        "crm_contactos_campanias": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
            "creado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
            "actualizado_por": "VARCHAR(100) NOT NULL DEFAULT ''",
        },
        "crm_eventos": {
            "tenant_id": "VARCHAR(100) NOT NULL DEFAULT 'default'",
        },
    }
    with engine.begin() as conn:
        for table_name, specs in column_specs.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in specs.items():
                if column_name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def get_db(host: str | None = None) -> Session:
    session_factory = core_db.get_session_factory_for_host(_active_host(host))
    return session_factory()
