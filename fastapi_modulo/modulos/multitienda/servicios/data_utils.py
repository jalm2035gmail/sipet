from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from enum import Enum
import logging

from sqlalchemy.inspection import inspect as sa_inspect

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal

_log = logging.getLogger("multitienda.data_utils")


def coerce_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_mapping(row: dict) -> dict:
    return {key: coerce_value(value) for key, value in row.items()}


def orm_to_dict(instance) -> dict:
    return serialize_mapping({
        attr.key: getattr(instance, attr.key)
        for attr in sa_inspect(instance.__class__).mapper.column_attrs
    })


def orm_list(items) -> list:
    rows = items.all() if hasattr(items, "all") else items
    return [orm_to_dict(item) for item in rows]


def parse_datetime_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        normalized = normalized.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return value
    return value


def normalize_datetime_fields(data: dict, *fields: str) -> dict:
    normalized = dict(data)
    for field in fields:
        if field in normalized:
            normalized[field] = parse_datetime_value(normalized[field])
    return normalized


@contextmanager
def managed_session(*, commit: bool = False):
    db = SessionLocal()
    try:
        yield db
        if commit:
            db.commit()
    except Exception:
        _log.exception("Error dentro de managed_session(commit=%s); se realizara rollback.", commit)
        db.rollback()
        raise
    finally:
        db.close()
