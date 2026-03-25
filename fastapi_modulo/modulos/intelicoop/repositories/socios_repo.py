from __future__ import annotations

from typing import Any, Dict, List

from fastapi_modulo.modulos.intelicoop.modelos.store_operativo import create_socio, get_socio, list_socios


def list_socios_repo() -> List[Dict[str, Any]]:
    return list_socios()


def get_socio_repo(socio_id: int) -> Dict[str, Any] | None:
    return get_socio(socio_id)


def create_socio_repo(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_socio(payload)

