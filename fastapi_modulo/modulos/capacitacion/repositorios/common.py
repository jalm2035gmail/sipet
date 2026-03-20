from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db


def active_host(host: Optional[str] = None) -> str:
    return (host or core_db.get_request_host() or "").strip()


def get_db(host: Optional[str] = None) -> Session:
    return core_db.get_session_factory_for_host(active_host(host))()


def get_engine(host: Optional[str] = None):
    return core_db.get_engine_for_host(active_host(host))


@contextmanager
def get_db_ctx(host: Optional[str] = None) -> Generator[Session, None, None]:
    """Context manager que garantiza commit, rollback y cierre automático.

    Uso:
        with get_db_ctx() as db:
            obj = db.query(MiModelo).filter(...).first()
            db.refresh(obj)
            return serializar(obj)

    No es necesario llamar a db.commit() ni db.close() manualmente;
    el context manager lo hace por ti. Si ocurre cualquier excepción,
    ejecuta rollback antes de re-lanzarla.
    """
    session: Session = get_db(host)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        