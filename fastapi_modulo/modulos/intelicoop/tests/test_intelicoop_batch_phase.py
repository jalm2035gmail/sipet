from __future__ import annotations

import pytest
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")


from fastapi_modulo.core.db import MAIN, engine
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopAnalyticCut,
    IntelicoopAuditLog,
    IntelicoopBatchAlert,
    IntelicoopBatchJobState,
    IntelicoopBatchRun,
    IntelicoopBusinessRule,
    IntelicoopCampania,
    IntelicoopCampaniaFeatureSnapshot,
    IntelicoopContactoCampania,
    IntelicoopCohorteSnapshot,
    IntelicoopCredito,
    IntelicoopCreditoFeatureSnapshot,
    IntelicoopCuenta,
    IntelicoopDataQualitySnapshot,
    IntelicoopGovernanceSnapshot,
    IntelicoopHistorialPago,
    IntelicoopKpiSnapshot,
    IntelicoopModelVersionRegistry,
    IntelicoopModelDriftSnapshot,
    IntelicoopModelRecalibration,
    IntelicoopProspecto,
    IntelicoopProspectoFeatureSnapshot,
    IntelicoopScoringResult,
    IntelicoopScoringTraza,
    IntelicoopSeguimientoCampania,
    IntelicoopSocio,
    IntelicoopSocioFeatureSnapshot,
    IntelicoopTransaccion,
    IntelicoopAhorroFeatureSnapshot,
)


INTELICOOP_TABLES = [
    IntelicoopSocio.__table__,
    IntelicoopCredito.__table__,
    IntelicoopHistorialPago.__table__,
    IntelicoopCuenta.__table__,
    IntelicoopTransaccion.__table__,
    IntelicoopCampania.__table__,
    IntelicoopProspecto.__table__,
    IntelicoopContactoCampania.__table__,
    IntelicoopSeguimientoCampania.__table__,
    IntelicoopScoringResult.__table__,
    IntelicoopScoringTraza.__table__,
    IntelicoopModelVersionRegistry.__table__,
    IntelicoopAnalyticCut.__table__,
    IntelicoopDataQualitySnapshot.__table__,
    IntelicoopSocioFeatureSnapshot.__table__,
    IntelicoopCreditoFeatureSnapshot.__table__,
    IntelicoopAhorroFeatureSnapshot.__table__,
    IntelicoopCampaniaFeatureSnapshot.__table__,
    IntelicoopProspectoFeatureSnapshot.__table__,
    IntelicoopKpiSnapshot.__table__,
    IntelicoopCohorteSnapshot.__table__,
    IntelicoopGovernanceSnapshot.__table__,
    IntelicoopModelDriftSnapshot.__table__,
    IntelicoopModelRecalibration.__table__,
    IntelicoopAuditLog.__table__,
    IntelicoopBusinessRule.__table__,
    IntelicoopBatchJobState.__table__,
    IntelicoopBatchRun.__table__,
    IntelicoopBatchAlert.__table__,
]


@pytest.fixture(autouse=True)
def _reset_batch_tables(reset_tables) -> None:
    reset_tables(INTELICOOP_TABLES)


def test_batch_jobs_execute_and_persist_bitacora(build_client, auth_headers) -> None:
    client = build_client()
    headers = auth_headers(role="admin", user="intelicoop.batch")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Batch",
            "email": "batch@example.com",
            "telefono": "555-0110",
            "direccion": "Zona 2",
            "segmento": "inactivo",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    credito = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 2400,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 2500,
            "deuda_actual": 2100,
            "antiguedad_meses": 4,
            "estado": "mora",
        },
    )
    assert credito.status_code == 201

    cuenta = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_id, "tipo": "ahorro", "saldo": 120},
    )
    assert cuenta.status_code == 201

    for job_key in ("foundation_refresh", "segmentation_refresh", "scoring_refresh", "alerts_refresh", "governance_refresh"):
        response = client.post("/api/intelicoop/batch/ejecutar", headers=headers, json={"job_key": job_key})
        assert response.status_code == 201
        body = response.json()
        assert body["job_key"] == job_key
        assert body["status"] == "success"

    runs = client.get("/api/intelicoop/batch/runs?limit=10", headers=headers)
    assert runs.status_code == 200
    run_rows = runs.json()
    foundation_run = next(row for row in run_rows if row["job_key"] == "foundation_refresh")
    for job_key in ("segmentation_refresh", "scoring_refresh", "alerts_refresh"):
        job_run = next(row for row in run_rows if row["job_key"] == job_key)
        assert job_run["cut_key"] == foundation_run["cut_key"]

    overview = client.get("/api/intelicoop/batch/resumen", headers=headers)
    assert overview.status_code == 200
    data = overview.json()
    assert len(data["jobs"]) >= 5
    assert len(data["runs"]) >= 5
    assert len(data["alerts"]) >= 1
    assert any(row["job_key"] == "alerts_refresh" for row in data["runs"])
    assert any(row["job_key"] == "governance_refresh" for row in data["runs"])


def test_batch_due_runner_executes_scheduled_jobs(build_client, auth_headers) -> None:
    client = build_client()
    headers = auth_headers(role="admin", user="intelicoop.batch")

    response = client.post("/api/intelicoop/batch/ejecutar-programados", headers=headers, json={})

    assert response.status_code == 201
    body = response.json()
    assert set(body["executed_jobs"]) == {
        "foundation_refresh",
        "segmentation_refresh",
        "scoring_refresh",
        "alerts_refresh",
        "governance_refresh",
    }
    assert len(body["runs"]) == 5

    runs = client.get("/api/intelicoop/batch/runs?limit=10", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) == 5
