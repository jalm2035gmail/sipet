from __future__ import annotations

import pytest
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")


from fastapi_modulo.core.db import MAIN, engine
from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopAnalyticCut,
    IntelicoopAhorroFeatureSnapshot,
    IntelicoopCampania,
    IntelicoopContactoCampania,
    IntelicoopCredito,
    IntelicoopCreditoFeatureSnapshot,
    IntelicoopCuenta,
    IntelicoopDataQualitySnapshot,
    IntelicoopHistorialPago,
    IntelicoopKpiSnapshot,
    IntelicoopModelVersionRegistry,
    IntelicoopProspecto,
    IntelicoopProspectoFeatureSnapshot,
    IntelicoopScoringResult,
    IntelicoopScoringTraza,
    IntelicoopSeguimientoCampania,
    IntelicoopSocio,
    IntelicoopSocioFeatureSnapshot,
    IntelicoopTransaccion,
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
    IntelicoopProspectoFeatureSnapshot.__table__,
    IntelicoopKpiSnapshot.__table__,
]


@pytest.fixture(autouse=True)
def _reset_foundation_tables(reset_tables) -> None:
    reset_tables(INTELICOOP_TABLES)


def test_foundation_overview_exposes_contract(build_client, auth_headers) -> None:
    client = build_client()

    response = client.get("/api/intelicoop/fundamentos/resumen", headers=auth_headers("Intelicoop", role="admin", user="intelicoop.foundation"))

    assert response.status_code == 200
    body = response.json()
    assert body["entity_model"]["transactional"]
    assert body["entity_model"]["analytical"]
    assert body["entity_model"]["relationships"]
    assert body["time_cuts"]["active_cut_key"].startswith("day:")
    assert body["data_layers"]["bronze"]["datasets"]
    assert body["data_layers"]["silver"]["datasets"]
    assert body["data_layers"]["gold"]["datasets"]
    assert body["data_layers"]["ml"]["datasets"]
    assert body["data_layers"]["gold"]["datasets"][0]["feature_modes"] == ["observadas", "derivadas", "imputadas"]


def test_foundation_materialize_creates_analytic_snapshots(build_client, auth_headers) -> None:
    client = build_client()
    headers = auth_headers("Intelicoop", role="admin", user="intelicoop.foundation")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Base",
            "email": "base@example.com",
            "telefono": "555-0101",
            "direccion": "Zona 1",
            "segmento": "hormiga",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    credito = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 1000,
            "numero_abonos": 10,
            "periodicidad": "mensual",
            "ingreso_mensual": 4500,
            "deuda_actual": 700,
            "antiguedad_meses": 18,
            "estado": "solicitado",
        },
    )
    assert credito.status_code == 201

    materialize = client.post("/api/intelicoop/fundamentos/materializar", headers=headers, json={"cut_type": "daily_close"})

    assert materialize.status_code == 201
    body = materialize.json()
    assert body["cut_key"].startswith("day:")
    assert body["feature_rows"] >= 1
    assert body["quality_rules"] >= 1
    assert body["data_layers"]["bronze"]["datasets"]
    assert body["data_layers"]["silver"]["datasets"]
    assert body["data_layers"]["gold"]["datasets"]
    assert body["data_layers"]["ml"]["datasets"]
    assert body["imputation_summary"]["features_socio_gold"]["imputed_fields"] is not None

    overview = client.get("/api/intelicoop/fundamentos/resumen", headers=headers)
    assert overview.status_code == 200
    overview_body = overview.json()
    latest = overview_body["storage_contract"]["latest_materialized_cut"]
    assert latest["cut_key"] == body["cut_key"]
    assert overview_body["storage_contract"]["bronze"]["layer"] == "bronze"
    assert overview_body["storage_contract"]["silver"]["layer"] == "silver"
    assert overview_body["storage_contract"]["gold"]["layer"] == "gold"
    assert overview_body["storage_contract"]["ml"]["layer"] == "ml"


def test_foundation_materialize_builds_credit_savings_and_commercial_feature_families(build_client, auth_headers) -> None:
    client = build_client()
    headers = auth_headers("Intelicoop", role="admin", user="intelicoop.foundation")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Features",
            "email": "features@example.com",
            "telefono": "555-0102",
            "direccion": "Zona 2",
            "segmento": "hormiga",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    credito = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 2000,
            "numero_abonos": 8,
            "periodicidad": "mensual",
            "ingreso_mensual": 5000,
            "deuda_actual": 1200,
            "antiguedad_meses": 18,
            "estado": "mora",
        },
    )
    assert credito.status_code == 201
    credito_id = credito.json()["credito"]["id"]

    credito_recompra = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 2600,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 5500,
            "deuda_actual": 1400,
            "antiguedad_meses": 24,
            "estado": "aprobado",
        },
    )
    assert credito_recompra.status_code == 201

    pago = client.post(
        "/api/intelicoop/creditos/pagos",
        headers=headers,
        json={"credito_id": credito_id, "monto": 500},
    )
    assert pago.status_code == 201

    cuenta = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_id, "tipo": "ahorro", "saldo": 1500},
    )
    assert cuenta.status_code == 201
    cuenta_id = cuenta.json()["id"]

    for payload in (
        {"cuenta_id": cuenta_id, "tipo": "deposito", "monto": 300},
        {"cuenta_id": cuenta_id, "tipo": "retiro", "monto": 100},
    ):
        response = client.post("/api/intelicoop/ahorros/transacciones", headers=headers, json=payload)
        assert response.status_code == 201

    campana = client.post(
        "/api/intelicoop/campanas",
        headers=headers,
        json={"nombre": "Campana Features", "tipo": "Retencion", "estado": "activa"},
    )
    assert campana.status_code == 201
    campana_id = campana.json()["id"]

    contacto = client.post(
        "/api/intelicoop/campanas/contactos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_id,
            "ejecutivo_id": "ejecutivo_features",
            "canal": "whatsapp",
            "estado_contacto": "contactado",
        },
    )
    assert contacto.status_code == 201

    seguimiento = client.post(
        "/api/intelicoop/campanas/seguimientos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_id,
            "lista": "retencion",
            "etapa": "cerrado",
            "conversion": True,
            "monto_colocado": 900,
        },
    )
    assert seguimiento.status_code == 201

    materialize = client.post("/api/intelicoop/fundamentos/materializar", headers=headers, json={"cut_type": "daily_close"})
    assert materialize.status_code == 201
    cut_key = materialize.json()["cut_key"]
    ml_layer = materialize.json()["data_layers"]["ml"]["datasets"]

    session_factory = core_db.get_session_factory_for_host("")
    db = session_factory()
    try:
        socio_feature = db.query(IntelicoopSocioFeatureSnapshot).filter(IntelicoopSocioFeatureSnapshot.cut_key == cut_key).first()
        credito_feature = db.query(IntelicoopCreditoFeatureSnapshot).filter(IntelicoopCreditoFeatureSnapshot.cut_key == cut_key).first()
        ahorro_feature = db.query(IntelicoopAhorroFeatureSnapshot).filter(IntelicoopAhorroFeatureSnapshot.cut_key == cut_key).first()
        analytic_cut = db.query(IntelicoopAnalyticCut).filter(IntelicoopAnalyticCut.cut_key == cut_key).first()

        assert socio_feature is not None
        assert credito_feature is not None
        assert ahorro_feature is not None
        assert analytic_cut is not None

        assert socio_feature.campanas_participadas >= 1
        assert socio_feature.campanas_convertidas >= 1
        assert socio_feature.respuesta_por_canal_json
        assert socio_feature.score_propension_referencia >= 0
        assert socio_feature.score_abandono >= 0
        assert socio_feature.responde_campania == 1
        assert socio_feature.recompra_credito == 1
        assert socio_feature.up_sell_exitoso == 1
        assert socio_feature.abandono_90_dias in {0, 1}

        assert credito_feature.porcentaje_pagado > 0
        assert credito_feature.creditos_activos >= 1
        assert credito_feature.creditos_en_mora >= 1
        assert credito_feature.exposicion_total >= 2000
        assert credito_feature.convirtio_credito == 1
        assert credito_feature.recompra_credito == 1
        assert credito_feature.up_sell_exitoso in {0, 1}
        assert credito_feature.default_30 in {0, 1}
        assert credito_feature.default_60 in {0, 1}
        assert credito_feature.default_90 in {0, 1}

        assert ahorro_feature.saldo_promedio_30d >= 0
        assert ahorro_feature.saldo_promedio_60d >= 0
        assert ahorro_feature.saldo_promedio_90d >= 0
        assert ahorro_feature.frecuencia_transaccional >= 0
        assert ahorro_feature.volatilidad_saldo >= 0
        assert ahorro_feature.estacionalidad_ahorro in {"estable", "media", "alta"}

        training_scoring = next(item for item in ml_layer if item["dataset_key"] == "training_scoring_ml")
        training_propension = next(item for item in ml_layer if item["dataset_key"] == "training_propension_ml")
        training_abandono = next(item for item in ml_layer if item["dataset_key"] == "training_abandono_ml")
        assert training_scoring["label_distribution"]["recompra_credito"] >= 1
        assert "default_30" in training_scoring["target_labels"]
        assert training_propension["label_distribution"]["responde_campania"] >= 1
        assert "up_sell_exitoso" in training_propension["target_labels"]
        assert "abandono_90_dias" in training_abandono["target_labels"]
    finally:
        db.close()
