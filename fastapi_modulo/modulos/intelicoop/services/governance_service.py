from __future__ import annotations

from typing import Any, Dict, List

from fastapi_modulo.modulos.intelicoop.repositories.snapshots_repo import (
    get_batch_overview_repo,
    get_governance_overview_repo,
    list_batch_alerts_repo,
    list_batch_runs_repo,
    run_batch_job_repo,
    run_due_batch_jobs_repo,
    run_governance_refresh_repo,
)


def get_governance_overview_service() -> Dict[str, Any]:
    return get_governance_overview_repo()


def run_governance_refresh_service(actor: str = "manual") -> Dict[str, Any]:
    return run_governance_refresh_repo(actor=actor)


def get_batch_overview_service() -> Dict[str, Any]:
    return get_batch_overview_repo()


def list_batch_runs_service(limit: int = 20) -> List[Dict[str, Any]]:
    return list_batch_runs_repo(limit=limit)


def list_batch_alerts_service(limit: int = 20) -> List[Dict[str, Any]]:
    return list_batch_alerts_repo(limit=limit)


def run_batch_job_service(job_key: str) -> Dict[str, Any]:
    return run_batch_job_repo(job_key=job_key, trigger_type="manual")


def run_due_batch_jobs_service() -> Dict[str, Any]:
    return run_due_batch_jobs_repo()
