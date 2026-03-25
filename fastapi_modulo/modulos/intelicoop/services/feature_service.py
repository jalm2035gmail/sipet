from __future__ import annotations

from typing import Any, Dict

from fastapi_modulo.modulos.intelicoop.repositories.snapshots_repo import (
    get_foundation_overview_repo,
    materialize_foundation_cut_repo,
)


def get_foundation_overview_service() -> Dict[str, Any]:
    return get_foundation_overview_repo()


def materialize_foundation_cut_service(cut_type: str = "daily_close") -> Dict[str, Any]:
    return materialize_foundation_cut_repo(cut_type=cut_type)

