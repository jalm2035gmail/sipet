from __future__ import annotations

import json

import pytest
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")


from fastapi_modulo.core.db import MAIN, engine
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopAnalyticCut,
    IntelicoopAuditLog,
    IntelicoopBusinessRule,
    IntelicoopGovernanceSnapshot,
    IntelicoopHistorialPago,
    IntelicoopModelDriftSnapshot,
    IntelicoopModelRecalibration,
    IntelicoopModelVersionRegistry,
    IntelicoopScoringResult,
    IntelicoopScoringTraza,
    IntelicoopSocio,
)


TABLES = [
    IntelicoopSocio.__table__,
    IntelicoopHistorialPago.__table__,
    IntelicoopScoringResult.__table__,
    IntelicoopScoringTraza.__table__,
    IntelicoopModelVersionRegistry.__table__,
    IntelicoopAnalyticCut.__table__,
    IntelicoopGovernanceSnapshot.__table__,
    IntelicoopModelDriftSnapshot.__table__,
    IntelicoopModelRecalibration.__table__,
    IntelicoopAuditLog.__table__,
    IntelicoopBusinessRule.__table__,
]


@pytest.fixture(autouse=True)
def _reset_governance_tables(reset_tables) -> None:
    reset_tables(TABLES)


def test_governance_refresh_creates_monitoring_drift_and_audit(build_client, auth_headers) -> None:
    client = build_client()
    headers = auth_headers(role="admin", user="intelicoop.governance")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Governance",
            "email": "governance@example.com",
            "telefono": "555-0111",
            "direccion": "Zona 3",
            "segmento": "inactivo",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    for payload in (
        {"solicitud_id": "gov-1", "socio_id": socio_id, "ingreso_mensual": 6000, "deuda_actual": 500, "antiguedad_meses": 36},
        {"solicitud_id": "gov-2", "socio_id": socio_id, "ingreso_mensual": 2500, "deuda_actual": 2200, "antiguedad_meses": 4},
    ):
        response = client.post("/api/intelicoop/scoring/evaluar", headers=headers, json=payload)
        assert response.status_code == 201

    refresh = client.post("/api/intelicoop/gobernanza/refresh", headers=headers, json={})

    assert refresh.status_code == 201
    body = refresh.json()
    assert body["model_version"] == "intelicoop_scoring_v1"
    assert body["monitoring"]["total_inferencias"] >= 2
    assert len(body["drift_rows"]) >= 3
    assert body["business_rules"]
    assert "auc" in body["monitoring"]
    assert "ks" in body["monitoring"]
    assert "gini" in body["monitoring"]
    assert "psi" in body["monitoring"]
    assert "csi" in body["monitoring"]
    assert "segment_thresholds" in body["monitoring"]
    assert "governance_cycle" in body["monitoring"]
    assert body["governance_alerts"]
    assert "challenger_version" in body["retraining"]
    assert body["comparison"]["available"] is True
    assert "deployment_approved" in body["impact"]
    assert body["explainability"]["importancia_variables"]
    assert body["explainability"]["shap_values_promedio"]
    assert body["explainability"]["top_factores_por_score"]
    assert body["explainability"]["explicacion_agregada_segmento"]

    overview = client.get("/api/intelicoop/gobernanza/resumen", headers=headers)
    assert overview.status_code == 200
    data = overview.json()
    assert data["latest_snapshot"]["model_version"] == "intelicoop_scoring_v1"
    assert data["drift_rows"]
    assert data["audit_logs"]
    assert data["model_versions"]
    assert data["business_rules"]
    assert any(row["event_type"] == "governance_impact_documented" for row in data["audit_logs"])

    from sqlalchemy.orm import Session

    db = Session(bind=engine)
    try:
        version_row = (
            db.query(IntelicoopModelVersionRegistry)
            .filter(IntelicoopModelVersionRegistry.version_key == "intelicoop_scoring_v1")
            .first()
        )
        assert version_row is not None
        metricas = json.loads(version_row.metricas_json)
        assert metricas["artifact_path"]
        assert metricas["artifact_format"] == "joblib"
        assert "artifact_checksum" in metricas
        assert metricas["load_status"] in {"loaded", "missing", "error"}
        assert "loaded_at" in metricas
        assert metricas["expected_features"]
        assert metricas["expected_performance"]
        assert "psi" in metricas
        assert "csi" in metricas
        assert "segment_thresholds" in metricas
        assert "lifecycle_status" in metricas

        challenger_row = (
            db.query(IntelicoopModelVersionRegistry)
            .filter(IntelicoopModelVersionRegistry.version_key.like("intelicoop_scoring_v1_challenger_%"))
            .first()
        )
        assert challenger_row is not None
    finally:
        db.close()
