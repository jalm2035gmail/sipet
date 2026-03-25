from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_scoring import evaluate_scoring_v2, summarize_scoring
from fastapi_modulo.modulos.intelicoop.repositories.scoring_repo import (
    create_scoring_result_repo,
    get_scoring_explainability_repo,
    get_scoring_trace_repo,
    list_scoring_results_repo,
)


def evaluate_and_create_scoring_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    scoring_eval = evaluate_scoring_v2(
        ingreso_mensual=payload["ingreso_mensual"],
        deuda_actual=payload["deuda_actual"],
        antiguedad_meses=payload["antiguedad_meses"],
        solicitud_id=payload.get("solicitud_id") or f"sol-{uuid.uuid4().hex[:10]}",
        socio_id=payload.get("socio_id"),
        credito_id=payload.get("credito_id"),
    )
    return create_scoring_result_repo(
        {
            "ingreso_mensual": payload["ingreso_mensual"],
            "deuda_actual": payload["deuda_actual"],
            "antiguedad_meses": payload["antiguedad_meses"],
            **scoring_eval,
        }
    )


def get_scoring_trace_service(scoring_result_id: int) -> Dict[str, Any] | None:
    return get_scoring_trace_repo(scoring_result_id)


def get_scoring_summary_service() -> Dict[str, Any]:
    return summarize_scoring(list_scoring_results_repo())


def get_scoring_explainability_service(socio_id: int | None = None) -> Dict[str, Any]:
    return get_scoring_explainability_repo(socio_id=socio_id)

