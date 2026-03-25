from __future__ import annotations

from typing import Any, Dict, List

from fastapi_modulo.modulos.intelicoop.modelos.store_operativo import (
    create_credito,
    create_historial_pago,
    get_credito,
    get_credito_detail,
    list_creditos,
    list_historial_pagos,
)


def list_creditos_repo() -> List[Dict[str, Any]]:
    return list_creditos()


def get_credito_repo(credito_id: int) -> Dict[str, Any] | None:
    return get_credito(credito_id)


def get_credito_detail_repo(credito_id: int) -> Dict[str, Any] | None:
    return get_credito_detail(credito_id)


def create_credito_repo(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_credito(payload)


def list_historial_pagos_repo(credito_id: int | None = None) -> List[Dict[str, Any]]:
    return list_historial_pagos(credito_id=credito_id)


def create_historial_pago_repo(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_historial_pago(payload)

