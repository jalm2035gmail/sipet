from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.intelicoop.repositories.snapshots_repo import (
    get_cohortes_repo,
    get_dashboard_resumen_repo,
    get_descriptive_analytics_repo,
    get_pattern_discovery_summary_repo,
    get_tendencias_repo,
)


def get_dashboard_resumen_service() -> Dict[str, Any]:
    return get_dashboard_resumen_repo()


def get_descriptive_analytics_service() -> Dict[str, Any]:
    return get_descriptive_analytics_repo()


def get_tendencias_service(kpi_key: str = "imor_pct", n_cuts: int = 12) -> Dict[str, Any]:
    return get_tendencias_repo(kpi_key=kpi_key, n_cuts=n_cuts)


def get_cohortes_service(dimension: str | None = None) -> Dict[str, Any]:
    return get_cohortes_repo(dimension=dimension)


def get_pattern_discovery_summary_service() -> Dict[str, Any]:
    return get_pattern_discovery_summary_repo()

