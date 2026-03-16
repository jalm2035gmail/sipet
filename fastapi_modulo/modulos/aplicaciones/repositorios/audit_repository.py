from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos.aplicaciones.servicios.protocol_service import (
    get_protocol_status_map as protocol_status_map_service,
)


def get_protocol_audit_records() -> dict[str, dict[str, Any]]:
    return protocol_status_map_service()


def get_protocol_status_summary() -> dict[str, dict[str, Any]]:
    return get_protocol_audit_records()


def get_protocol_status_map_proxy() -> dict[str, dict[str, Any]]:
    return get_protocol_audit_records()


get_protocol_status_map = get_protocol_status_map_proxy

__all__ = ["get_protocol_audit_records", "get_protocol_status_map", "get_protocol_status_summary"]
