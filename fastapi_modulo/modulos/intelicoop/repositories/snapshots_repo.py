from __future__ import annotations

from typing import Any, Dict, List

from fastapi_modulo.modulos.intelicoop.modelos.store_analytics import (
    get_cohortes,
    get_dashboard_resumen,
    get_descriptive_analytics,
    get_pattern_discovery_summary,
    get_segmentation_propensity_summary,
    get_tendencias,
)
from fastapi_modulo.modulos.intelicoop.modelos.store_batch import (
    get_batch_overview,
    list_batch_alerts,
    list_batch_runs,
    run_batch_job,
    run_due_batch_jobs,
)
from fastapi_modulo.modulos.intelicoop.modelos.store_features import (
    get_foundation_overview,
    materialize_foundation_cut,
)
from fastapi_modulo.modulos.intelicoop.modelos.store_governance import (
    get_governance_overview,
    run_governance_refresh,
)


def get_foundation_overview_repo() -> Dict[str, Any]:
    return get_foundation_overview()


def materialize_foundation_cut_repo(cut_type: str = "daily_close") -> Dict[str, Any]:
    return materialize_foundation_cut(cut_type=cut_type)


def get_descriptive_analytics_repo() -> Dict[str, Any]:
    return get_descriptive_analytics()


def get_tendencias_repo(kpi_key: str = "imor_pct", n_cuts: int = 12) -> Dict[str, Any]:
    return get_tendencias(kpi_key=kpi_key, n_cuts=n_cuts)


def get_cohortes_repo(dimension: str | None = None) -> Dict[str, Any]:
    return get_cohortes(dimension=dimension)


def get_pattern_discovery_summary_repo() -> Dict[str, Any]:
    return get_pattern_discovery_summary()


def get_segmentation_propensity_summary_repo() -> Dict[str, Any]:
    return get_segmentation_propensity_summary()


def get_dashboard_resumen_repo() -> Dict[str, Any]:
    return get_dashboard_resumen()


def get_governance_overview_repo() -> Dict[str, Any]:
    return get_governance_overview()


def run_governance_refresh_repo(actor: str = "manual") -> Dict[str, Any]:
    return run_governance_refresh(actor=actor)


def get_batch_overview_repo() -> Dict[str, Any]:
    return get_batch_overview()


def list_batch_runs_repo(limit: int = 20) -> List[Dict[str, Any]]:
    return list_batch_runs(limit=limit)


def list_batch_alerts_repo(limit: int = 20) -> List[Dict[str, Any]]:
    return list_batch_alerts(limit=limit)


def run_batch_job_repo(job_key: str, trigger_type: str = "manual") -> Dict[str, Any]:
    return run_batch_job(job_key=job_key, trigger_type=trigger_type)


def run_due_batch_jobs_repo() -> Dict[str, Any]:
    return run_due_batch_jobs()

