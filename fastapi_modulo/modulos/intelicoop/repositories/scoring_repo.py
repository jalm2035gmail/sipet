from __future__ import annotations

from typing import Any, Dict, List

from fastapi_modulo.modulos.intelicoop.modelos.store_scoring import (
    create_scoring_result,
    get_scoring_explainability,
    get_scoring_trace,
    list_scoring_results,
)


def create_scoring_result_repo(payload: Dict[str, Any]) -> Dict[str, Any]:
    return create_scoring_result(payload)


def get_scoring_trace_repo(scoring_result_id: int) -> Dict[str, Any] | None:
    return get_scoring_trace(scoring_result_id)


def list_scoring_results_repo() -> List[Dict[str, Any]]:
    return list_scoring_results()


def get_scoring_explainability_repo(socio_id: int | None = None, model_version: str = "intelicoop_scoring_v1") -> Dict[str, Any]:
    return get_scoring_explainability(socio_id=socio_id, model_version=model_version)

