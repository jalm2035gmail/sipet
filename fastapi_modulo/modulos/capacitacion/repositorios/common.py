from __future__ import annotations

from typing import Optional

from fastapi_modulo.core import db as core_db


def active_host(host: Optional[str] = None) -> str:
    return (host or core_db.get_request_host() or "").strip()


def get_db(host: Optional[str] = None):
    return core_db.get_session_factory_for_host(active_host(host))()


def get_engine(host: Optional[str] = None):
    return core_db.get_engine_for_host(active_host(host))
