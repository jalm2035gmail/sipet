from __future__ import annotations

import os

from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.modulo_base.modelos.db_models import ModuloBaseCategoria, ModuloBaseRegistro


def _resolve_runtime_host(host: str | None = None) -> str | None:
    normalized = str(host or "").strip()
    if normalized:
        return normalized
    current_host = core_db.get_request_host()
    return current_host or None


def get_engine(host: str | None = None) -> Engine:
    return core_db.get_engine_for_host(_resolve_runtime_host(host))


def ensure_modulo_base_schema(
    *,
    allow_create_all_in_dev: bool = True,
    uses_migrations: bool = True,
    host: str | None = None,
    bind: Engine | Connection | None = None,
) -> None:
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    is_dev_like = app_env in {"development", "dev", "test", "testing", "local"}
    if uses_migrations and not allow_create_all_in_dev:
        return
    if uses_migrations and not is_dev_like:
        raise RuntimeError("Modulo base requiere migraciones Alembic en entornos reales; create_all solo se permite en desarrollo.")
    target = bind or get_engine(host)
    MAIN.metadata.create_all(bind=target, tables=[ModuloBaseCategoria.__table__, ModuloBaseRegistro.__table__], checkfirst=True)


def get_db(host: str | None = None) -> Session:
    session_factory = core_db.get_session_factory_for_host(_resolve_runtime_host(host))
    return session_factory()
