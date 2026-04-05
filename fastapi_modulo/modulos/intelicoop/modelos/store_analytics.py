from __future__ import annotations

from fastapi_modulo.modulos.intelicoop.modelos.store_legacy import (
    get_aggregate_consumption_summary,
    get_cohortes,
    get_dashboard_resumen,
    get_descriptive_analytics,
    get_pattern_discovery_summary,
    get_segmentation_propensity_summary,
    get_tendencias,
)

__all__ = [
    "get_aggregate_consumption_summary",
    "get_descriptive_analytics",
    "get_tendencias",
    "get_cohortes",
    "get_pattern_discovery_summary",
    "get_segmentation_propensity_summary",
    "get_dashboard_resumen",
]
