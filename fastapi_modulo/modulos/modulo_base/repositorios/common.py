from __future__ import annotations

import os

from sqlalchemy.orm import Session

from fastapi_modulo.db import MAIN, SessionLocal, engine
from fastapi_modulo.modulos.modulo_base.modelos.db_models import ModuloBaseRegistro


def ensure_modulo_base_schema(*, allow_create_all_in_dev: bool = True, uses_migrations: bool = True) -> None:
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    is_dev_like = app_env in {"development", "dev", "test", "testing", "local"}
    if uses_migrations and not allow_create_all_in_dev:
        return
    if uses_migrations and not is_dev_like:
        raise RuntimeError("Modulo base requiere migraciones Alembic en entornos reales; create_all solo se permite en desarrollo.")
    MAIN.metadata.create_all(bind=engine, tables=[ModuloBaseRegistro.__table__], checkfirst=True)


def get_db() -> Session:
    return SessionLocal()
