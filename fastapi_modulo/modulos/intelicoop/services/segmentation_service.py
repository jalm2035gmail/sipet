from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.intelicoop.repositories.snapshots_repo import get_segmentation_propensity_summary_repo


def get_segmentation_propensity_summary_service() -> Dict[str, Any]:
    return get_segmentation_propensity_summary_repo()

