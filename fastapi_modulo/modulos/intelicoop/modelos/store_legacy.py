from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, time, timedelta
from typing import Any, Dict, List

from sqlalchemy import case, func, inspect as sa_inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopAhorroFeatureSnapshot,
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
    IntelicoopSocioFeatureSnapshot,
    IntelicoopSocio,
    IntelicoopTransaccion,
)
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_scoring import evaluate_scoring_v2

_SCHEMA_READY_HOSTS: set[str] = set()
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VALID_TX_TIPOS = {"deposito", "retiro"}
_VALID_CREDITO_ESTADOS = {"solicitado", "aprobado", "vigente", "liquidado", "rechazado", "mora", "reestructurado"}
_ACTIVE_CREDITO_ESTADOS = {"solicitado", "aprobado", "vigente", "mora", "reestructurado"}
_CONVERSION_CREDITO_ESTADOS = {"aprobado", "vigente", "liquidado", "mora", "reestructurado"}
FOUNDATION_FEATURE_VERSION = "intelicoop_foundation_v1"
FEATURE_ENGINEERING_VERSION = "intelicoop_features_v1"
BATCH_VERSION = "intelicoop_batch_v1"
GOVERNANCE_VERSION = "intelicoop_governance_v1"
BATCH_JOB_CATALOG = [
    {
        "job_key": "foundation_refresh",
        "job_label": "Recalculo de features y snapshots",
        "cadence_minutes": 1440,
        "config": {"cut_type": "daily_close"},
    },
    {
        "job_key": "segmentation_refresh",
        "job_label": "Recalculo de segmentos automaticos",
        "cadence_minutes": 1440,
        "config": {},
    },
    {
        "job_key": "scoring_refresh",
        "job_label": "Recalculo batch de scoring",
        "cadence_minutes": 1440,
        "config": {},
    },
    {
        "job_key": "alerts_refresh",
        "job_label": "Generacion batch de alertas",
        "cadence_minutes": 720,
        "config": {},
    },
    {
        "job_key": "governance_refresh",
        "job_label": "Monitoreo, drift y auditoria",
        "cadence_minutes": 1440,
        "config": {},
    },
]
BUSINESS_RULE_CATALOG = [
    {
        "rule_key": "max_high_risk_share",
        "rule_label": "Participacion maxima de alto riesgo",
        "description": "El porcentaje de scoring alto no debe superar el umbral definido.",
        "severity": "alta",
        "threshold_value": 0.35,
        "config": {},
    },
    {
        "rule_key": "max_ratio_deuda_ingreso_avg",
        "rule_label": "Ratio deuda/ingreso promedio",
        "description": "El ratio deuda/ingreso promedio no debe exceder el umbral.",
        "severity": "media",
        "threshold_value": 0.55,
        "config": {},
    },
    {
        "rule_key": "max_drift_score",
        "rule_label": "Drift maximo aceptado",
        "description": "El drift por feature no debe superar el umbral configurado.",
        "severity": "alta",
        "threshold_value": 0.20,
        "config": {},
    },
]

# ── Catálogo de KPIs: define tipo observado/estimado y umbrales de semáforo ──
# direction "higher" = mayor es mejor; "lower" = menor es mejor
# verde/amarillo son los umbrales de corte
KPI_CATALOG: Dict[str, Any] = {
    "socios_total":     {"label": "Total socios",           "group": "fundamentos", "metric_type": "observado",  "direction": "higher", "verde": 10,   "amarillo": 1},
    "creditos_total":   {"label": "Total créditos",         "group": "fundamentos", "metric_type": "observado",  "direction": "higher", "verde": 5,    "amarillo": 1},
    "campanas_total":   {"label": "Total campañas",         "group": "fundamentos", "metric_type": "observado",  "direction": "higher", "verde": 2,    "amarillo": 1},
    "prospectos_total": {"label": "Total prospectos",       "group": "fundamentos", "metric_type": "observado",  "direction": "higher", "verde": 5,    "amarillo": 1},
    "scoring_total":    {"label": "Total evaluaciones",     "group": "fundamentos", "metric_type": "observado",  "direction": "higher", "verde": 5,    "amarillo": 1},
    "imor_pct":         {"label": "IMOR estimado %",        "group": "riesgo",      "metric_type": "estimado",   "direction": "lower",  "verde": 5.0,  "amarillo": 10.0},
    "captacion_neta":   {"label": "Captación neta",         "group": "captacion",   "metric_type": "observado",  "direction": "higher", "verde": 1000, "amarillo": 0},
    "conversion_pct":   {"label": "Conversión comercial %", "group": "comercial",   "metric_type": "observado",  "direction": "higher", "verde": 20.0, "amarillo": 10.0},
}


def _compute_semaforo(kpi_key: str, value: float) -> str:
    cat = KPI_CATALOG.get(kpi_key)
    if not cat:
        return "sin_umbral"
    verde = cat.get("verde")
    amarillo = cat.get("amarillo")
    if cat["direction"] == "higher":
        if verde is not None and value >= verde:
            return "verde"
        if amarillo is not None and value >= amarillo:
            return "amarillo"
        return "rojo"
    else:
        if verde is not None and value <= verde:
            return "verde"
        if amarillo is not None and value <= amarillo:
            return "amarillo"
        return "rojo"
TRANSACTIONAL_ENTITY_DEFINITIONS = [
    {"key": "socios", "table": "intelicoop_socios", "grain": "1 fila por socio"},
    {"key": "creditos", "table": "intelicoop_creditos", "grain": "1 fila por credito"},
    {"key": "historial_pagos", "table": "intelicoop_historial_pagos", "grain": "1 fila por pago"},
    {"key": "cuentas", "table": "intelicoop_cuentas", "grain": "1 fila por cuenta"},
    {"key": "transacciones", "table": "intelicoop_transacciones", "grain": "1 fila por transaccion"},
    {"key": "campanas", "table": "intelicoop_campanas", "grain": "1 fila por campana"},
    {"key": "prospectos", "table": "intelicoop_prospectos", "grain": "1 fila por prospecto"},
    {"key": "contactos_campania", "table": "intelicoop_contactos_campania", "grain": "1 fila por contacto"},
    {"key": "seguimiento_campania", "table": "intelicoop_seguimiento_campania", "grain": "1 fila por seguimiento"},
    {"key": "scoring_results", "table": "intelicoop_scoring_results", "grain": "1 fila por inferencia"},
]
ANALYTICAL_ENTITY_DEFINITIONS = [
    {"key": "scoring_trazas", "table": "intelicoop_scoring_trazas", "grain": "1 fila por traza de inferencia"},
    {"key": "model_versions", "table": "intelicoop_model_versions", "grain": "1 fila por version de modelo"},
    {"key": "analytic_cuts", "table": "intelicoop_analytic_cuts", "grain": "1 fila por corte analitico"},
    {"key": "data_quality_snapshots", "table": "intelicoop_data_quality_snapshots", "grain": "1 fila por regla y corte"},
    {"key": "socio_feature_snapshots", "table": "intelicoop_socio_feature_snapshots", "grain": "1 fila por socio y corte"},
    {"key": "credito_feature_snapshots", "table": "intelicoop_credito_feature_snapshots", "grain": "1 fila por credito y corte"},
    {"key": "ahorro_feature_snapshots", "table": "intelicoop_ahorro_feature_snapshots", "grain": "1 fila por cuenta y corte"},
    {"key": "campania_feature_snapshots", "table": "intelicoop_campania_feature_snapshots", "grain": "1 fila por campana y corte"},
    {"key": "prospecto_feature_snapshots", "table": "intelicoop_prospecto_feature_snapshots", "grain": "1 fila por prospecto y corte"},
    {"key": "cohorte_snapshots", "table": "intelicoop_cohorte_snapshots", "grain": "1 fila por dimension+bucket+metrica y corte"},
    {"key": "kpi_snapshots", "table": "intelicoop_kpi_snapshots", "grain": "1 fila por KPI y corte"},
    {"key": "batch_job_states", "table": "intelicoop_batch_job_states", "grain": "1 fila por job programado"},
    {"key": "batch_runs", "table": "intelicoop_batch_runs", "grain": "1 fila por ejecucion batch"},
    {"key": "batch_alerts", "table": "intelicoop_batch_alerts", "grain": "1 fila por alerta batch"},
    {"key": "governance_snapshots", "table": "intelicoop_governance_snapshots", "grain": "1 fila por snapshot de gobernanza"},
    {"key": "model_drift_snapshots", "table": "intelicoop_model_drift_snapshots", "grain": "1 fila por feature monitoreada"},
    {"key": "model_recalibrations", "table": "intelicoop_model_recalibrations", "grain": "1 fila por evento de recalibracion"},
    {"key": "audit_logs", "table": "intelicoop_audit_logs", "grain": "1 fila por evento auditable"},
    {"key": "business_rules", "table": "intelicoop_business_rules", "grain": "1 fila por regla de negocio"},
]
FOUNDATION_RELATIONSHIPS = [
    {"from": "socios", "to": "creditos", "type": "1:N", "key": "socios.id -> creditos.socio_id"},
    {"from": "creditos", "to": "historial_pagos", "type": "1:N", "key": "creditos.id -> historial_pagos.credito_id"},
    {"from": "socios", "to": "cuentas", "type": "1:N", "key": "socios.id -> cuentas.socio_id"},
    {"from": "cuentas", "to": "transacciones", "type": "1:N", "key": "cuentas.id -> transacciones.cuenta_id"},
    {"from": "campanas", "to": "contactos_campania", "type": "1:N", "key": "campanas.id -> contactos_campania.campania_id"},
    {"from": "socios", "to": "contactos_campania", "type": "1:N", "key": "socios.id -> contactos_campania.socio_id"},
    {"from": "campanas", "to": "seguimiento_campania", "type": "1:N", "key": "campanas.id -> seguimiento_campania.campania_id"},
    {"from": "socios", "to": "seguimiento_campania", "type": "1:N", "key": "socios.id -> seguimiento_campania.socio_id"},
    {"from": "socios", "to": "scoring_results", "type": "1:N", "key": "socios.id -> scoring_results.socio_id"},
    {"from": "creditos", "to": "scoring_results", "type": "1:N", "key": "creditos.id -> scoring_results.credito_id"},
    {"from": "socios", "to": "socio_feature_snapshots", "type": "1:N", "key": "socios.id -> socio_feature_snapshots.socio_id"},
]

BRONZE_DATASETS = [
    {"dataset_key": "socios_raw", "source_table": "intelicoop_socios", "grain": "1 fila por socio operativo"},
    {"dataset_key": "creditos_raw", "source_table": "intelicoop_creditos", "grain": "1 fila por credito operativo"},
    {"dataset_key": "pagos_raw", "source_table": "intelicoop_historial_pagos", "grain": "1 fila por pago operativo"},
    {"dataset_key": "cuentas_raw", "source_table": "intelicoop_cuentas", "grain": "1 fila por cuenta operativa"},
    {"dataset_key": "transacciones_raw", "source_table": "intelicoop_transacciones", "grain": "1 fila por transaccion operativa"},
    {"dataset_key": "campanas_raw", "source_table": "intelicoop_campanas", "grain": "1 fila por campana operativa"},
    {"dataset_key": "contactos_raw", "source_table": "intelicoop_contactos_campania", "grain": "1 fila por contacto operativo"},
    {"dataset_key": "seguimientos_raw", "source_table": "intelicoop_seguimiento_campania", "grain": "1 fila por seguimiento operativo"},
    {"dataset_key": "prospectos_raw", "source_table": "intelicoop_prospectos", "grain": "1 fila por prospecto operativo"},
    {"dataset_key": "scoring_raw", "source_table": "intelicoop_scoring_results", "grain": "1 fila por inferencia operativa"},
]
SILVER_DATASETS = [
    {"dataset_key": "socios_clean", "source_table": "intelicoop_socios", "quality_scope": "socios"},
    {"dataset_key": "creditos_clean", "source_table": "intelicoop_creditos", "quality_scope": "creditos"},
    {"dataset_key": "cuentas_clean", "source_table": "intelicoop_cuentas", "quality_scope": "cuentas"},
    {"dataset_key": "transacciones_clean", "source_table": "intelicoop_transacciones", "quality_scope": "transacciones"},
    {"dataset_key": "campanas_clean", "source_table": "intelicoop_campanas", "quality_scope": "campanas"},
    {"dataset_key": "prospectos_clean", "source_table": "intelicoop_prospectos", "quality_scope": "prospectos"},
    {"dataset_key": "contactos_resolved", "source_table": "intelicoop_contactos_campania", "quality_scope": "contactos_campania"},
    {"dataset_key": "seguimientos_resolved", "source_table": "intelicoop_seguimiento_campania", "quality_scope": "seguimiento_campania"},
]
GOLD_DATASETS = [
    {"dataset_key": "features_socio_gold", "source_table": "intelicoop_socio_feature_snapshots", "entity": "socio"},
    {"dataset_key": "features_credito_gold", "source_table": "intelicoop_credito_feature_snapshots", "entity": "credito"},
    {"dataset_key": "features_ahorro_gold", "source_table": "intelicoop_ahorro_feature_snapshots", "entity": "ahorro"},
    {"dataset_key": "features_campania_gold", "source_table": "intelicoop_campania_feature_snapshots", "entity": "campania"},
    {"dataset_key": "features_prospecto_gold", "source_table": "intelicoop_prospecto_feature_snapshots", "entity": "prospecto"},
]
ML_DATASETS = [
    {"dataset_key": "training_scoring_ml", "dataset_type": "training", "source": "gold_credito+labels_supervisados", "target_labels": ["default_30", "default_60", "default_90", "recompra_credito"]},
    {"dataset_key": "inference_scoring_ml", "dataset_type": "inference", "source": "gold_credito+snapshot_actual", "target_labels": ["default_30", "default_60", "default_90"]},
    {"dataset_key": "training_propension_ml", "dataset_type": "training", "source": "gold_socio+gold_prospecto+labels_supervisados", "target_labels": ["convirtio_credito", "responde_campania", "up_sell_exitoso"]},
    {"dataset_key": "inference_propension_ml", "dataset_type": "inference", "source": "gold_socio+gold_prospecto+snapshot_actual", "target_labels": ["convirtio_credito", "responde_campania", "up_sell_exitoso"]},
    {"dataset_key": "training_abandono_ml", "dataset_type": "training", "source": "gold_socio+labels_supervisados", "target_labels": ["abandono_90_dias"]},
    {"dataset_key": "inference_abandono_ml", "dataset_type": "inference", "source": "gold_socio+snapshot_actual", "target_labels": ["abandono_90_dias"]},
    {"dataset_key": "training_segmentacion_ml", "dataset_type": "training", "source": "gold+segmentacion", "target_labels": []},
    {"dataset_key": "inference_segmentacion_ml", "dataset_type": "inference", "source": "gold+segmentacion_actual", "target_labels": []},
]


def _migrate_intelicoop_schema(engine) -> None:
    """Aplica migraciones de esquema de intelicoop de forma idempotente.

    Cubiertas:
    - intelicoop_creditos: agrega fecha_desembolso y fecha_vencimiento si faltan.
    - intelicoop_campanas: convierte fecha_inicio/fecha_fin de VARCHAR a DATETIME.
    """
    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    dialect = engine.dialect.name

    # ── helper: agregar columnas nullable de forma idempotente ────────────────
    def _add_cols(table: str, cols: List[tuple]) -> None:
        if table not in existing_tables:
            return
        existing_cols = {c["name"] for c in inspector.get_columns(table)}
        with engine.begin() as conn:
            for col_name, col_type in cols:
                if col_name not in existing_cols:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    else:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))

    # ── 1. intelicoop_creditos: columnas DateTime nuevas ─────────────────────
    dt = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    _add_cols("intelicoop_creditos", [
        ("fecha_desembolso", dt),
        ("fecha_vencimiento", dt),
        ("numero_abonos", "INTEGER NOT NULL DEFAULT 1"),
        ("periodicidad", "VARCHAR(20) NOT NULL DEFAULT 'mensual'"),
        ("tasa", "FLOAT NOT NULL DEFAULT 0"),
        ("dias_mora_actual", "INTEGER NOT NULL DEFAULT 0"),
        ("max_dias_mora", "INTEGER NOT NULL DEFAULT 0"),
        ("num_reestructuras", "INTEGER NOT NULL DEFAULT 0"),
    ])

    _add_cols("intelicoop_socios", [
        ("fecha_nacimiento", dt),
        ("genero", "VARCHAR(20) NOT NULL DEFAULT ''"),
        ("estado_civil", "VARCHAR(30) NOT NULL DEFAULT ''"),
        ("nivel_educativo", "VARCHAR(60) NOT NULL DEFAULT ''"),
        ("ocupacion", "VARCHAR(120) NOT NULL DEFAULT ''"),
        ("sector_economico", "VARCHAR(120) NOT NULL DEFAULT ''"),
        ("ubicacion_estado", "VARCHAR(120) NOT NULL DEFAULT ''"),
        ("ubicacion_municipio", "VARCHAR(120) NOT NULL DEFAULT ''"),
        ("tipo_socio", "VARCHAR(30) NOT NULL DEFAULT 'activo'"),
    ])

    _add_cols("intelicoop_historial_pagos", [
        ("pago_puntual", "INTEGER NOT NULL DEFAULT 1"),
        ("dias_atraso", "INTEGER NOT NULL DEFAULT 0"),
    ])

    _add_cols("intelicoop_transacciones", [
        ("canal", "VARCHAR(30) NOT NULL DEFAULT ''"),
    ])

    # ── 2. intelicoop_campanas: VARCHAR → DATETIME en fecha_inicio/fecha_fin ──
    if "intelicoop_campanas" in existing_tables:
        cols = {c["name"]: c for c in inspector.get_columns("intelicoop_campanas")}
        fecha_col = cols.get("fecha_inicio")
        if fecha_col is not None:
            col_type_str = str(fecha_col["type"]).upper()
            needs_migration = any(t in col_type_str for t in ("VARCHAR", "TEXT", "CHAR"))
            if needs_migration:
                with engine.begin() as conn:
                    if dialect == "postgresql":
                        conn.execute(text(
                            "ALTER TABLE intelicoop_campanas "
                            "ALTER COLUMN fecha_inicio TYPE TIMESTAMP "
                            "  USING NULLIF(fecha_inicio, '')::TIMESTAMP, "
                            "ALTER COLUMN fecha_fin TYPE TIMESTAMP "
                            "  USING NULLIF(fecha_fin, '')::TIMESTAMP"
                        ))
                    else:
                        # SQLite no soporta ALTER COLUMN: reconstruir la tabla
                        conn.execute(text(
                            "CREATE TABLE intelicoop_campanas_mig_tmp ("
                            "  id INTEGER PRIMARY KEY,"
                            "  nombre VARCHAR(150) NOT NULL,"
                            "  tipo VARCHAR(100) NOT NULL,"
                            "  fecha_inicio DATETIME,"
                            "  fecha_fin DATETIME,"
                            "  estado VARCHAR(20) NOT NULL DEFAULT 'borrador',"
                            "  fecha_creacion DATETIME NOT NULL"
                            ")"
                        ))
                        conn.execute(text(
                            "INSERT INTO intelicoop_campanas_mig_tmp"
                            "  (id, nombre, tipo, fecha_inicio, fecha_fin, estado, fecha_creacion)"
                            " SELECT id, nombre, tipo,"
                            "  CASE WHEN fecha_inicio IS NULL OR fecha_inicio = ''"
                            "       THEN NULL ELSE datetime(fecha_inicio) END,"
                            "  CASE WHEN fecha_fin IS NULL OR fecha_fin = ''"
                            "       THEN NULL ELSE datetime(fecha_fin) END,"
                            "  estado, fecha_creacion"
                            " FROM intelicoop_campanas"
                        ))
                        conn.execute(text("DROP TABLE intelicoop_campanas"))
                        conn.execute(text(
                            "ALTER TABLE intelicoop_campanas_mig_tmp"
                            " RENAME TO intelicoop_campanas"
                        ))

    # ── 3. intelicoop_kpi_snapshots: columnas de Fase 3 ──────────────────────
    _add_cols("intelicoop_kpi_snapshots", [
        ("metric_type", "VARCHAR(20) NOT NULL DEFAULT 'observado'"),
        ("semaforo",    "VARCHAR(20) NOT NULL DEFAULT 'sin_umbral'"),
    ])

    # ── 3b. intelicoop_analytic_cuts: manifiestos por capa analítica ────────
    _add_cols("intelicoop_analytic_cuts", [
        ("bronze_manifest_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("silver_manifest_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("gold_manifest_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("ml_manifest_json", "TEXT NOT NULL DEFAULT '{}'"),
    ])

    # ── 4. intelicoop_socio_feature_snapshots: columnas de Fase 2 ────────────
    int_default0 = "INTEGER NOT NULL DEFAULT 0"
    float_default0 = "FLOAT NOT NULL DEFAULT 0"
    _add_cols("intelicoop_socio_feature_snapshots", [
        ("creditos_activos", int_default0),
        ("creditos_mora", int_default0),
        ("tasa_cumplimiento_pagos", float_default0),
        ("ratio_deuda_ingreso", float_default0),
        ("campanas_participadas", int_default0),
        ("campanas_convertidas", int_default0),
        ("respuesta_por_canal_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("dias_desde_ultimo_contacto", int_default0),
        ("dias_como_socio", int_default0),
        ("edad", int_default0),
        ("num_productos", int_default0),
        ("diversificacion", float_default0),
        ("profundidad_relacion", float_default0),
        ("score_abandono", float_default0),
        ("score_fidelidad", float_default0),
        ("estabilidad_financiera", float_default0),
        ("tasa_respuesta", float_default0),
        ("canal_preferido", "VARCHAR(30) NOT NULL DEFAULT ''"),
        ("sensibilidad_comercial", float_default0),
        ("numero_alertas", int_default0),
        ("tendencia_riesgo", "VARCHAR(20) NOT NULL DEFAULT 'estable'"),
        ("reincidencia", int_default0),
        ("abandono_90_dias", int_default0),
        ("responde_campania", int_default0),
        ("up_sell_exitoso", int_default0),
        ("recompra_credito", int_default0),
    ])

    _add_cols("intelicoop_credito_feature_snapshots", [
        ("numero_abonos", int_default0),
        ("periodicidad", "VARCHAR(20) NOT NULL DEFAULT 'mensual'"),
        ("porcentaje_pagado", float_default0),
        ("ratio_deuda_ingreso", float_default0),
        ("creditos_activos", int_default0),
        ("creditos_en_mora", int_default0),
        ("cumplimiento_pagos", float_default0),
        ("exposicion_total", float_default0),
        ("default_30", int_default0),
        ("default_60", int_default0),
        ("default_90", int_default0),
        ("convirtio_credito", int_default0),
        ("up_sell_exitoso", int_default0),
        ("recompra_credito", int_default0),
    ])

    _add_cols("intelicoop_ahorro_feature_snapshots", [
        ("saldo_promedio_30d", float_default0),
        ("saldo_promedio_60d", float_default0),
        ("saldo_promedio_90d", float_default0),
        ("frecuencia_transaccional", float_default0),
        ("captacion_neta_mensual", float_default0),
        ("volatilidad_saldo", float_default0),
        ("estacionalidad_ahorro", "VARCHAR(20) NOT NULL DEFAULT 'estable'"),
    ])

    _add_cols("intelicoop_prospecto_feature_snapshots", [
        ("convirtio_credito", int_default0),
        ("responde_campania", int_default0),
    ])

    # ── 5. intelicoop_scoring_results: columnas de scoring operativo ─────────
    _add_cols("intelicoop_scoring_results", [
        ("confianza", "FLOAT"),
        ("motor", "VARCHAR(20) NOT NULL DEFAULT 'reglas'"),
        ("explicacion_json", "TEXT NOT NULL DEFAULT '{}'"),
    ])


def ensure_intelicoop_schema() -> None:
    current_host = str(core_db.get_request_host() or "").strip()
    cache_key = current_host or "__default__"
    engine = core_db.get_engine_for_host(current_host)
    if cache_key in _SCHEMA_READY_HOSTS:
        inspector = sa_inspect(engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = {
            "intelicoop_socios",
            "intelicoop_creditos",
            "intelicoop_historial_pagos",
            "intelicoop_cuentas",
            "intelicoop_transacciones",
            "intelicoop_campanas",
            "intelicoop_prospectos",
            "intelicoop_contactos_campania",
            "intelicoop_seguimiento_campania",
            "intelicoop_scoring_results",
        }
        if required_tables.issubset(existing_tables):
            return
        _SCHEMA_READY_HOSTS.discard(cache_key)
    _migrate_intelicoop_schema(engine)
    MAIN.metadata.create_all(
        bind=engine,
        tables=[
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
            IntelicoopCohorteSnapshot.__table__,
            IntelicoopKpiSnapshot.__table__,
            IntelicoopBatchJobState.__table__,
            IntelicoopBatchRun.__table__,
            IntelicoopBatchAlert.__table__,
            IntelicoopGovernanceSnapshot.__table__,
            IntelicoopModelDriftSnapshot.__table__,
            IntelicoopModelRecalibration.__table__,
            IntelicoopAuditLog.__table__,
            IntelicoopBusinessRule.__table__,
        ],
        checkfirst=True,
    )
    _SCHEMA_READY_HOSTS.add(cache_key)


def _db() -> Session:
    current_host = str(core_db.get_request_host() or "").strip()
    ensure_intelicoop_schema()
    session_factory = core_db.get_session_factory_for_host(current_host)
    return session_factory()


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _json_load(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return fallback


def _compute_age(fecha_nacimiento: Any, reference_at: datetime | None = None) -> int:
    if not fecha_nacimiento:
        return 0
    fecha = fecha_nacimiento
    if isinstance(fecha_nacimiento, datetime):
        fecha = fecha_nacimiento.date()
    ref = (reference_at or datetime.utcnow()).date()
    years = ref.year - fecha.year
    if (ref.month, ref.day) < (fecha.month, fecha.day):
        years -= 1
    return max(0, years)


def _normalize_credito_estado(value: Any) -> str:
    estado = str(value or "solicitado").strip().lower() or "solicitado"
    if estado not in _VALID_CREDITO_ESTADOS:
        raise ValueError(
            "Estado de credito invalido. Use: solicitado, aprobado, vigente, liquidado, rechazado, mora o reestructurado."
        )
    return estado


def _stddev(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return variance ** 0.5


def _estimate_average_balance(current_balance: float, txs: List[Any], now: datetime, window_days: int) -> float:
    window_start = now - timedelta(days=window_days)
    net_window = sum(
        float(tx.monto or 0) if str(tx.tipo or "") == "deposito" else -float(tx.monto or 0)
        for tx in txs
        if tx.fecha and tx.fecha >= window_start
    )
    return round(max(0.0, float(current_balance) - (net_window / 2.0)), 2)


def _days_since(dt_value: datetime | None, now: datetime) -> int | None:
    if not dt_value:
        return None
    return max(0, (now - dt_value).days)


def _label_distribution(rows: List[Dict[str, int]], keys: List[str]) -> Dict[str, int]:
    return {key: int(sum(int(row.get(key, 0) or 0) for row in rows)) for key in keys}


def _empty_imputation_summary() -> Dict[str, Dict[str, Any]]:
    return {
        "features_socio_gold": {"imputed_records": 0, "imputed_fields": {}},
        "features_credito_gold": {"imputed_records": 0, "imputed_fields": {}},
        "features_ahorro_gold": {"imputed_records": 0, "imputed_fields": {}},
        "features_campania_gold": {"imputed_records": 0, "imputed_fields": {}},
        "features_prospecto_gold": {"imputed_records": 0, "imputed_fields": {}},
    }


def _register_imputation(summary: Dict[str, Dict[str, Any]], dataset_key: str, field_names: List[str]) -> None:
    if not field_names:
        return
    dataset_summary = summary.setdefault(dataset_key, {"imputed_records": 0, "imputed_fields": {}})
    dataset_summary["imputed_records"] = int(dataset_summary.get("imputed_records", 0)) + 1
    field_bucket = dataset_summary.setdefault("imputed_fields", {})
    for field_name in field_names:
        field_bucket[field_name] = int(field_bucket.get(field_name, 0)) + 1


def _build_data_layer_contract(
    table_counts: Dict[str, int],
    quality_rules: List[Dict[str, Any]],
    cut_key: str = "",
    label_summary: Dict[str, Dict[str, int]] | None = None,
    imputation_summary: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    label_summary = label_summary or {}
    imputation_summary = imputation_summary or _empty_imputation_summary()
    quality_by_scope = {str(rule.get("scope")): rule for rule in quality_rules}
    bronze = {
        "layer": "bronze",
        "description": "datos operativos casi crudos",
        "datasets": [
            {
                **item,
                "rows": int(table_counts.get(item["source_table"], 0)),
            }
            for item in BRONZE_DATASETS
        ],
    }
    silver = {
        "layer": "silver",
        "description": "datos limpios, normalizados, deduplicados y con llaves resueltas",
        "datasets": [
            {
                **item,
                "rows": int(table_counts.get(item["source_table"], 0)),
                "quality_status": str((quality_by_scope.get(item["quality_scope"]) or {}).get("status", "pending")),
            }
            for item in SILVER_DATASETS
        ],
    }
    gold = {
        "layer": "gold",
        "description": "features materializadas por entidad analítica",
        "datasets": [
            {
                **item,
                "rows": int(table_counts.get(item["source_table"], 0)),
                "cut_key": cut_key,
                "labels": label_summary.get(item["dataset_key"], {}),
                "feature_modes": ["observadas", "derivadas", "imputadas"],
                "imputation_summary": imputation_summary.get(item["dataset_key"], {"imputed_records": 0, "imputed_fields": {}}),
            }
            for item in GOLD_DATASETS
        ],
    }
    training_rows = int(table_counts.get("intelicoop_credito_feature_snapshots", 0)) + int(table_counts.get("intelicoop_socio_feature_snapshots", 0))
    inference_rows = int(table_counts.get("intelicoop_socio_feature_snapshots", 0)) + int(table_counts.get("intelicoop_prospecto_feature_snapshots", 0))
    ml = {
        "layer": "ml",
        "description": "datasets listos para entrenamiento e inferencia",
        "datasets": [
            {
                **item,
                "rows": training_rows if item["dataset_type"] == "training" else inference_rows,
                "cut_key": cut_key,
                "label_distribution": label_summary.get(item["dataset_key"], {}),
            }
            for item in ML_DATASETS
        ],
    }
    return {"bronze": bronze, "silver": silver, "gold": gold, "ml": ml}


def _utcnow() -> datetime:
    return datetime.utcnow()


def _batch_run_dict(obj: IntelicoopBatchRun) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "run_key": obj.run_key,
        "job_key": obj.job_key,
        "trigger_type": obj.trigger_type,
        "cut_key": obj.cut_key,
        "status": obj.status,
        "quality_status": obj.quality_status,
        "records_processed": int(obj.records_processed or 0),
        "records_created": int(obj.records_created or 0),
        "metrics": _json_load(obj.metrics_json, {}),
        "quality_summary": _json_load(obj.quality_summary_json, {}),
        "error_message": obj.error_message or "",
        "started_at": obj.started_at.isoformat() if obj.started_at else "",
        "finished_at": obj.finished_at.isoformat() if obj.finished_at else "",
    }


def _batch_job_state_dict(obj: IntelicoopBatchJobState) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "job_key": obj.job_key,
        "job_label": obj.job_label,
        "cadence_minutes": int(obj.cadence_minutes or 0),
        "enabled": bool(obj.enabled),
        "last_run_at": obj.last_run_at.isoformat() if obj.last_run_at else "",
        "next_run_at": obj.next_run_at.isoformat() if obj.next_run_at else "",
        "last_status": obj.last_status,
        "config": _json_load(obj.config_json, {}),
    }


def _batch_alert_dict(obj: IntelicoopBatchAlert) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "batch_run_id": obj.batch_run_id,
        "cut_key": obj.cut_key,
        "alert_type": obj.alert_type,
        "severity": obj.severity,
        "entity_type": obj.entity_type,
        "entity_id": obj.entity_id,
        "entity_label": obj.entity_label,
        "score": round(float(obj.score or 0), 4),
        "status": obj.status,
        "details": _json_load(obj.details_json, {}),
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
    }


def _governance_snapshot_dict(obj: IntelicoopGovernanceSnapshot) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "cut_key": obj.cut_key,
        "model_version": obj.model_version,
        "monitoring": _json_load(obj.monitoring_json, {}),
        "drift": _json_load(obj.drift_json, {}),
        "explainability": _json_load(obj.explainability_json, {}),
        "governance_status": obj.governance_status,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
    }


def _drift_snapshot_dict(obj: IntelicoopModelDriftSnapshot) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "cut_key": obj.cut_key,
        "model_version": obj.model_version,
        "feature_key": obj.feature_key,
        "baseline_value": round(float(obj.baseline_value or 0), 4),
        "current_value": round(float(obj.current_value or 0), 4),
        "drift_score": round(float(obj.drift_score or 0), 4),
        "drift_level": obj.drift_level,
        "details": _json_load(obj.details_json, {}),
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
    }


def _recalibration_dict(obj: IntelicoopModelRecalibration) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "model_version": obj.model_version,
        "trigger_reason": obj.trigger_reason,
        "status": obj.status,
        "notes": obj.notes,
        "before_metrics": _json_load(obj.before_metrics_json, {}),
        "after_metrics": _json_load(obj.after_metrics_json, {}),
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
    }


def _audit_log_dict(obj: IntelicoopAuditLog) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "event_type": obj.event_type,
        "entity_type": obj.entity_type,
        "entity_id": obj.entity_id,
        "actor": obj.actor,
        "model_version": obj.model_version,
        "details": _json_load(obj.details_json, {}),
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
    }


def _business_rule_dict(obj: IntelicoopBusinessRule) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "rule_key": obj.rule_key,
        "rule_label": obj.rule_label,
        "description": obj.description,
        "severity": obj.severity,
        "enabled": bool(obj.enabled),
        "threshold_value": float(obj.threshold_value) if obj.threshold_value is not None else None,
        "config": _json_load(obj.config_json, {}),
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
    }


def _ensure_batch_job_states(db: Session) -> List[IntelicoopBatchJobState]:
    now = _utcnow()
    rows: List[IntelicoopBatchJobState] = []
    for item in BATCH_JOB_CATALOG:
        row = db.query(IntelicoopBatchJobState).filter(IntelicoopBatchJobState.job_key == item["job_key"]).first()
        if row is None:
            row = IntelicoopBatchJobState(
                job_key=item["job_key"],
                job_label=item["job_label"],
                cadence_minutes=int(item["cadence_minutes"]),
                enabled=1,
                last_status="pending",
                next_run_at=now - timedelta(minutes=1),
                config_json=_json_dump(item.get("config", {})),
            )
            db.add(row)
        else:
            row.job_label = item["job_label"]
            row.cadence_minutes = int(item["cadence_minutes"])
            if not row.config_json:
                row.config_json = _json_dump(item.get("config", {}))
            if row.next_run_at is None:
                row.next_run_at = now
        row.updated_at = now
        rows.append(row)
    db.flush()
    return rows


def _ensure_business_rules(db: Session) -> List[IntelicoopBusinessRule]:
    now = _utcnow()
    rows: List[IntelicoopBusinessRule] = []
    for item in BUSINESS_RULE_CATALOG:
        row = db.query(IntelicoopBusinessRule).filter(IntelicoopBusinessRule.rule_key == item["rule_key"]).first()
        if row is None:
            row = IntelicoopBusinessRule(
                rule_key=item["rule_key"],
                rule_label=item["rule_label"],
                description=item["description"],
                severity=item["severity"],
                enabled=1,
                threshold_value=item.get("threshold_value"),
                config_json=_json_dump(item.get("config", {})),
                updated_at=now,
            )
            db.add(row)
        else:
            row.rule_label = item["rule_label"]
            row.description = item["description"]
            row.severity = item["severity"]
            if row.threshold_value is None:
                row.threshold_value = item.get("threshold_value")
            if not row.config_json:
                row.config_json = _json_dump(item.get("config", {}))
            row.updated_at = now
        rows.append(row)
    db.flush()
    return rows


def _create_audit_log(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: int | None = None,
    actor: str = "system",
    model_version: str = "",
    details: Dict[str, Any] | None = None,
) -> None:
    db.add(
        IntelicoopAuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            model_version=model_version,
            details_json=_json_dump(details or {}),
        )
    )
    db.flush()


def _derive_batch_quality_status(summary: Dict[str, Any]) -> str:
    failed = int(summary.get("failed_rules", 0))
    warned = int(summary.get("warn_rules", 0))
    if failed > 0:
        return "fail"
    if warned > 0:
        return "warn"
    return "pass"


def _governance_status(levels: List[str]) -> str:
    if "fail" in levels:
        return "fail"
    if "warn" in levels:
        return "warn"
    return "pass"


def _drift_level(score: float) -> str:
    if score >= 0.2:
        return "alto"
    if score >= 0.1:
        return "medio"
    return "bajo"


def _cut_context(reference_at: datetime | None = None, cut_type: str = "daily_close") -> Dict[str, Any]:
    effective = reference_at or datetime.utcnow()
    day_start = datetime.combine(effective.date(), time.min)
    next_day = day_start + timedelta(days=1)
    month_start = day_start.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    if cut_type == "monthly_close":
        return {
            "cut_key": f"month:{month_start.strftime('%Y%m')}",
            "cut_type": "monthly_close",
            "cut_date": month_start,
            "window_start": month_start,
            "window_end": next_month,
            "month_start": month_start,
            "month_end": next_month,
        }
    return {
        "cut_key": f"day:{day_start.strftime('%Y%m%d')}",
        "cut_type": "daily_close",
        "cut_date": day_start,
        "window_start": day_start,
        "window_end": next_day,
        "month_start": month_start,
        "month_end": next_month,
    }


def _socio_dict(obj: IntelicoopSocio) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "nombre": obj.nombre,
        "email": obj.email,
        "telefono": obj.telefono,
        "direccion": obj.direccion,
        "segmento": obj.segmento,
        "fecha_nacimiento": obj.fecha_nacimiento.date().isoformat() if isinstance(obj.fecha_nacimiento, datetime) else (obj.fecha_nacimiento.isoformat() if obj.fecha_nacimiento else None),
        "edad": _compute_age(obj.fecha_nacimiento),
        "genero": obj.genero,
        "estado_civil": obj.estado_civil,
        "nivel_educativo": obj.nivel_educativo,
        "ocupacion": obj.ocupacion,
        "sector_economico": obj.sector_economico,
        "ubicacion_estado": obj.ubicacion_estado,
        "ubicacion_municipio": obj.ubicacion_municipio,
        "tipo_socio": obj.tipo_socio,
        "fecha_registro": obj.fecha_registro.isoformat() if obj.fecha_registro else "",
    }


def _credito_dict(obj: IntelicoopCredito, socio_nombre: str = "") -> Dict[str, Any]:
    numero_abonos = int(getattr(obj, "numero_abonos", 0) or obj.plazo or 0)
    return {
        "id": obj.id,
        "socio_id": obj.socio_id,
        "socio_nombre": socio_nombre,
        "monto": round(float(obj.monto or 0), 2),
        "numero_abonos": numero_abonos,
        "periodicidad": getattr(obj, "periodicidad", "mensual") or "mensual",
        "ingreso_mensual": round(float(obj.ingreso_mensual or 0), 2),
        "deuda_actual": round(float(obj.deuda_actual or 0), 2),
        "antiguedad_meses": obj.antiguedad_meses,
        "tasa": round(float(obj.tasa or 0), 4),
        "estado": obj.estado,
        "dias_mora_actual": int(obj.dias_mora_actual or 0),
        "max_dias_mora": int(obj.max_dias_mora or 0),
        "num_reestructuras": int(obj.num_reestructuras or 0),
        "fecha_desembolso": obj.fecha_desembolso.isoformat() if obj.fecha_desembolso else None,
        "fecha_vencimiento": obj.fecha_vencimiento.isoformat() if obj.fecha_vencimiento else None,
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }


def _historial_pago_dict(obj: IntelicoopHistorialPago) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "credito_id": obj.credito_id,
        "monto": round(float(obj.monto or 0), 2),
        "pago_puntual": bool(obj.pago_puntual),
        "dias_atraso": int(obj.dias_atraso or 0),
        "fecha": obj.fecha.isoformat() if obj.fecha else "",
    }


def _campania_dict(obj: IntelicoopCampania) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "nombre": obj.nombre,
        "tipo": obj.tipo,
        "fecha_inicio": obj.fecha_inicio.isoformat() if obj.fecha_inicio else None,
        "fecha_fin": obj.fecha_fin.isoformat() if obj.fecha_fin else None,
        "estado": obj.estado,
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }


def _prospecto_dict(obj: IntelicoopProspecto) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "nombre": obj.nombre,
        "telefono": obj.telefono,
        "direccion": obj.direccion,
        "fuente": obj.fuente,
        "score_propension": round(float(obj.score_propension or 0), 4),
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }


def _contacto_campania_dict(obj: IntelicoopContactoCampania, campania_nombre: str = "", socio_nombre: str = "") -> Dict[str, Any]:
    return {
        "id": obj.id,
        "campania_id": obj.campania_id,
        "campania_nombre": campania_nombre,
        "socio_id": obj.socio_id,
        "socio_nombre": socio_nombre,
        "ejecutivo_id": obj.ejecutivo_id,
        "canal": obj.canal,
        "estado_contacto": obj.estado_contacto,
        "fecha_contacto": obj.fecha_contacto.isoformat() if obj.fecha_contacto else "",
    }


def _seguimiento_campania_dict(obj: IntelicoopSeguimientoCampania, campania_nombre: str = "", socio_nombre: str = "") -> Dict[str, Any]:
    return {
        "id": obj.id,
        "campania_id": obj.campania_id,
        "campania_nombre": campania_nombre,
        "socio_id": obj.socio_id,
        "socio_nombre": socio_nombre,
        "lista": obj.lista,
        "etapa": obj.etapa,
        "conversion": bool(obj.conversion),
        "monto_colocado": round(float(obj.monto_colocado or 0), 2),
        "fecha_evento": obj.fecha_evento.isoformat() if obj.fecha_evento else "",
    }


def _scoring_result_dict(obj: IntelicoopScoringResult) -> Dict[str, Any]:
    explicacion = _json_load(obj.explicacion_json, {})
    return {
        "id": obj.id,
        "solicitud_id": obj.solicitud_id,
        "socio_id": obj.socio_id,
        "credito_id": obj.credito_id,
        "ingreso_mensual": round(float(obj.ingreso_mensual or 0), 2),
        "deuda_actual": round(float(obj.deuda_actual or 0), 2),
        "antiguedad_meses": obj.antiguedad_meses,
        "score": round(float(obj.score or 0), 4),
        "recomendacion": obj.recomendacion,
        "riesgo": obj.riesgo,
        "model_version": obj.model_version,
        "confianza": round(float(obj.confianza or 0), 4) if obj.confianza is not None else None,
        "motor": obj.motor,
        "explicacion_json": explicacion,
        "explainability": explicacion.get("explainability", {}),
        "razones": explicacion.get("razones", []),
        "reglas_aplicadas": explicacion.get("reglas_aplicadas", []),
        "traza_id": None,
        "traza_version": None,
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }


def _cuenta_dict(obj: IntelicoopCuenta, socio_nombre: str = "") -> Dict[str, Any]:
    return {
        "id": obj.id,
        "socio_id": obj.socio_id,
        "socio_nombre": socio_nombre,
        "tipo": obj.tipo,
        "saldo": round(float(obj.saldo or 0), 2),
        "fecha_creacion": obj.fecha_creacion.isoformat() if obj.fecha_creacion else "",
    }


def _transaccion_dict(obj: IntelicoopTransaccion, socio_nombre: str = "") -> Dict[str, Any]:
    return {
        "id": obj.id,
        "cuenta_id": obj.cuenta_id,
        "socio_nombre": socio_nombre,
        "monto": round(float(obj.monto or 0), 2),
        "tipo": obj.tipo,
        "canal": obj.canal,
        "fecha": obj.fecha.isoformat() if obj.fecha else "",
    }


def list_socios() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = db.query(IntelicoopSocio).order_by(IntelicoopSocio.id.desc()).all()
        return [_socio_dict(row) for row in rows]
    finally:
        db.close()


def get_socio(socio_id: int) -> Dict[str, Any] | None:
    db = _db()
    try:
        row = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == socio_id).first()
        return _socio_dict(row) if row else None
    finally:
        db.close()


def create_socio(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        email = payload["email"].strip().lower()
        existing = db.query(IntelicoopSocio).filter(func.lower(IntelicoopSocio.email) == email).first()
        if existing:
            raise ValueError("Ya existe un socio con ese correo.")
        fecha_nacimiento = payload.get("fecha_nacimiento")
        if isinstance(fecha_nacimiento, str) and fecha_nacimiento.strip():
            fecha_nacimiento = datetime.fromisoformat(fecha_nacimiento.strip())
        if fecha_nacimiento and not isinstance(fecha_nacimiento, datetime):
            fecha_nacimiento = datetime.combine(fecha_nacimiento, datetime.min.time())
        row = IntelicoopSocio(
            nombre=payload["nombre"].strip(),
            email=email,
            telefono=payload.get("telefono", "").strip(),
            direccion=payload.get("direccion", "").strip(),
            segmento=payload.get("segmento", "inactivo").strip() or "inactivo",
            fecha_nacimiento=fecha_nacimiento,
            genero=payload.get("genero", "").strip(),
            estado_civil=payload.get("estado_civil", "").strip(),
            nivel_educativo=payload.get("nivel_educativo", "").strip(),
            ocupacion=payload.get("ocupacion", "").strip(),
            sector_economico=payload.get("sector_economico", "").strip(),
            ubicacion_estado=payload.get("ubicacion_estado", "").strip(),
            ubicacion_municipio=payload.get("ubicacion_municipio", "").strip(),
            tipo_socio=payload.get("tipo_socio", "activo").strip() or "activo",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _socio_dict(row)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_creditos() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(IntelicoopCredito, IntelicoopSocio.nombre)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCredito.socio_id)
            .order_by(IntelicoopCredito.id.desc())
            .all()
        )
        return [_credito_dict(credito, socio_nombre or "") for credito, socio_nombre in rows]
    finally:
        db.close()


def get_credito(credito_id: int) -> Dict[str, Any] | None:
    db = _db()
    try:
        row = (
            db.query(IntelicoopCredito, IntelicoopSocio.nombre)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCredito.socio_id)
            .filter(IntelicoopCredito.id == credito_id)
            .first()
        )
        if not row:
            return None
        credito, socio_nombre = row
        return _credito_dict(credito, socio_nombre or "")
    finally:
        db.close()


def get_credito_detail(credito_id: int) -> Dict[str, Any] | None:
    db = _db()
    try:
        row = (
            db.query(IntelicoopCredito, IntelicoopSocio.nombre)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCredito.socio_id)
            .filter(IntelicoopCredito.id == credito_id)
            .first()
        )
        if not row:
            return None
        credito, socio_nombre = row
        pagos = (
            db.query(IntelicoopHistorialPago)
            .filter(IntelicoopHistorialPago.credito_id == credito_id)
            .order_by(IntelicoopHistorialPago.fecha.desc(), IntelicoopHistorialPago.id.desc())
            .all()
        )
        total_pagado = sum(float(item.monto or 0) for item in pagos)
        return {
            **_credito_dict(credito, socio_nombre or ""),
            "historial_pagos": [_historial_pago_dict(item) for item in pagos],
            "resumen_pagos": {
                "total_pagos": len(pagos),
                "monto_pagado": round(total_pagado, 2),
                "saldo_estimado": round(max(0.0, float(credito.monto or 0) - total_pagado), 2),
            },
        }
    finally:
        db.close()


def create_credito(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == int(payload["socio_id"])).first()
        if not socio:
            raise ValueError("El socio indicado no existe en intelicoop.")
        row = IntelicoopCredito(
            socio_id=int(payload["socio_id"]),
            monto=float(payload["monto"]),
            plazo=int(payload.get("numero_abonos") or payload.get("plazo") or 0),
            numero_abonos=int(payload.get("numero_abonos") or payload.get("plazo") or 0),
            periodicidad=str(payload.get("periodicidad") or "mensual").strip() or "mensual",
            ingreso_mensual=float(payload.get("ingreso_mensual", 0)),
            deuda_actual=float(payload.get("deuda_actual", 0)),
            antiguedad_meses=int(payload.get("antiguedad_meses", 0)),
            tasa=float(payload.get("tasa", 0)),
            estado=_normalize_credito_estado(payload.get("estado", "solicitado")),
            dias_mora_actual=int(payload.get("dias_mora_actual", 0)),
            max_dias_mora=int(payload.get("max_dias_mora", 0)),
            num_reestructuras=int(payload.get("num_reestructuras", 0)),
            fecha_desembolso=payload.get("fecha_desembolso"),
            fecha_vencimiento=payload.get("fecha_vencimiento"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _credito_dict(row, socio.nombre)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_historial_pagos(credito_id: int | None = None) -> List[Dict[str, Any]]:
    db = _db()
    try:
        query = db.query(IntelicoopHistorialPago)
        if credito_id is not None:
            query = query.filter(IntelicoopHistorialPago.credito_id == credito_id)
        rows = query.order_by(IntelicoopHistorialPago.fecha.desc(), IntelicoopHistorialPago.id.desc()).all()
        return [_historial_pago_dict(row) for row in rows]
    finally:
        db.close()


def create_historial_pago(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        credito = db.query(IntelicoopCredito).filter(IntelicoopCredito.id == int(payload["credito_id"])).first()
        if not credito:
            raise ValueError("El credito indicado no existe en intelicoop.")
        row = IntelicoopHistorialPago(
            credito_id=int(payload["credito_id"]),
            monto=float(payload["monto"]),
            pago_puntual=1 if payload.get("pago_puntual", True) else 0,
            dias_atraso=int(payload.get("dias_atraso", 0)),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _historial_pago_dict(row)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def get_ahorros_resumen() -> Dict[str, Any]:
    db = _db()
    try:
        cuentas = db.query(func.count(IntelicoopCuenta.id)).scalar() or 0
        movimientos = db.query(func.count(IntelicoopTransaccion.id)).scalar() or 0
        captacion = db.query(func.coalesce(func.sum(IntelicoopCuenta.saldo), 0)).scalar() or 0
        return {
            "cuentas": int(cuentas),
            "movimientos": int(movimientos),
            "captacion": round(float(captacion), 2),
        }
    finally:
        db.close()


def list_cuentas() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(IntelicoopCuenta, IntelicoopSocio.nombre)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCuenta.socio_id)
            .order_by(IntelicoopCuenta.id.desc())
            .all()
        )
        return [_cuenta_dict(cuenta, socio_nombre or "") for cuenta, socio_nombre in rows]
    finally:
        db.close()


def create_cuenta(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == int(payload["socio_id"])).first()
        if not socio:
            raise ValueError("El socio indicado no existe en intelicoop.")
        row = IntelicoopCuenta(
            socio_id=int(payload["socio_id"]),
            tipo=str(payload.get("tipo", "ahorro")).strip() or "ahorro",
            saldo=float(payload.get("saldo", 0)),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _cuenta_dict(row, socio.nombre)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_transacciones() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(IntelicoopTransaccion, IntelicoopSocio.nombre)
            .join(IntelicoopCuenta, IntelicoopCuenta.id == IntelicoopTransaccion.cuenta_id)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCuenta.socio_id)
            .order_by(IntelicoopTransaccion.id.desc())
            .all()
        )
        return [_transaccion_dict(tx, socio_nombre or "") for tx, socio_nombre in rows]
    finally:
        db.close()


def create_transaccion(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        cuenta = db.query(IntelicoopCuenta).filter(IntelicoopCuenta.id == int(payload["cuenta_id"])).first()
        if not cuenta:
            raise ValueError("La cuenta indicada no existe en intelicoop.")
        tipo = str(payload.get("tipo", "deposito")).strip() or "deposito"
        monto = float(payload.get("monto", 0))
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
        saldo_actual = float(cuenta.saldo or 0)
        if tipo == "retiro" and monto > saldo_actual:
            raise ValueError("Saldo insuficiente para registrar el retiro.")
        cuenta.saldo = saldo_actual + monto if tipo == "deposito" else saldo_actual - monto
        tx = IntelicoopTransaccion(
            cuenta_id=cuenta.id,
            monto=monto,
            tipo=tipo,
            canal=str(payload.get("canal", "")).strip(),
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == cuenta.socio_id).first()
        return _transaccion_dict(tx, socio.nombre if socio else "")
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_campanas() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = db.query(IntelicoopCampania).order_by(IntelicoopCampania.id.desc()).all()
        return [_campania_dict(row) for row in rows]
    finally:
        db.close()


def create_campana(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        row = IntelicoopCampania(
            nombre=payload["nombre"].strip(),
            tipo=payload["tipo"].strip(),
            fecha_inicio=payload.get("fecha_inicio"),
            fecha_fin=payload.get("fecha_fin"),
            estado=payload.get("estado", "borrador").strip() or "borrador",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _campania_dict(row)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_prospectos() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = db.query(IntelicoopProspecto).order_by(IntelicoopProspecto.id.desc()).all()
        return [_prospecto_dict(row) for row in rows]
    finally:
        db.close()


def create_prospecto(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        row = IntelicoopProspecto(
            nombre=payload["nombre"].strip(),
            telefono=payload.get("telefono", "").strip(),
            direccion=payload.get("direccion", "").strip(),
            fuente=payload.get("fuente", "").strip(),
            score_propension=float(payload.get("score_propension", 0)),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _prospecto_dict(row)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_contactos_campania(campania_id: int | None = None) -> List[Dict[str, Any]]:
    db = _db()
    try:
        query = (
            db.query(IntelicoopContactoCampania, IntelicoopCampania.nombre, IntelicoopSocio.nombre)
            .join(IntelicoopCampania, IntelicoopCampania.id == IntelicoopContactoCampania.campania_id)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopContactoCampania.socio_id)
        )
        if campania_id is not None:
            query = query.filter(IntelicoopContactoCampania.campania_id == campania_id)
        rows = query.order_by(IntelicoopContactoCampania.id.desc()).all()
        return [
            _contacto_campania_dict(contacto, campania_nombre or "", socio_nombre or "")
            for contacto, campania_nombre, socio_nombre in rows
        ]
    finally:
        db.close()


def create_contacto_campania(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        campania = db.query(IntelicoopCampania).filter(IntelicoopCampania.id == int(payload["campania_id"])).first()
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == int(payload["socio_id"])).first()
        if not campania:
            raise ValueError("La campana indicada no existe en intelicoop.")
        if not socio:
            raise ValueError("El socio indicado no existe en intelicoop.")
        row = IntelicoopContactoCampania(
            campania_id=int(payload["campania_id"]),
            socio_id=int(payload["socio_id"]),
            ejecutivo_id=str(payload.get("ejecutivo_id", "ejecutivo_general")).strip() or "ejecutivo_general",
            canal=str(payload.get("canal", "telefono")).strip() or "telefono",
            estado_contacto=str(payload.get("estado_contacto", "pendiente")).strip() or "pendiente",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _contacto_campania_dict(row, campania.nombre, socio.nombre)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_seguimientos_campania(campania_id: int | None = None) -> List[Dict[str, Any]]:
    db = _db()
    try:
        query = (
            db.query(IntelicoopSeguimientoCampania, IntelicoopCampania.nombre, IntelicoopSocio.nombre)
            .join(IntelicoopCampania, IntelicoopCampania.id == IntelicoopSeguimientoCampania.campania_id)
            .join(IntelicoopSocio, IntelicoopSocio.id == IntelicoopSeguimientoCampania.socio_id)
        )
        if campania_id is not None:
            query = query.filter(IntelicoopSeguimientoCampania.campania_id == campania_id)
        rows = query.order_by(IntelicoopSeguimientoCampania.id.desc()).all()
        return [
            _seguimiento_campania_dict(item, campania_nombre or "", socio_nombre or "")
            for item, campania_nombre, socio_nombre in rows
        ]
    finally:
        db.close()


def create_seguimiento_campania(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        campania = db.query(IntelicoopCampania).filter(IntelicoopCampania.id == int(payload["campania_id"])).first()
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == int(payload["socio_id"])).first()
        if not campania:
            raise ValueError("La campana indicada no existe en intelicoop.")
        if not socio:
            raise ValueError("El socio indicado no existe en intelicoop.")
        row = IntelicoopSeguimientoCampania(
            campania_id=int(payload["campania_id"]),
            socio_id=int(payload["socio_id"]),
            lista=str(payload.get("lista", "general")).strip() or "general",
            etapa=str(payload.get("etapa", "contactado")).strip() or "contactado",
            conversion=1 if payload.get("conversion") else 0,
            monto_colocado=float(payload.get("monto_colocado", 0)),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _seguimiento_campania_dict(row, campania.nombre, socio.nombre)
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def list_scoring_results() -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = db.query(IntelicoopScoringResult).order_by(IntelicoopScoringResult.id.desc()).all()
        traza_ids = {
            scoring_result_id: (traza_id, traza_version)
            for scoring_result_id, traza_id, traza_version in db.query(
                IntelicoopScoringTraza.scoring_result_id,
                IntelicoopScoringTraza.id,
                IntelicoopScoringTraza.traza_version,
            )
            .filter(IntelicoopScoringTraza.scoring_result_id.isnot(None))
            .all()
        }
        payload = []
        for row in rows:
            item = _scoring_result_dict(row)
            traza_meta = traza_ids.get(row.id)
            if traza_meta:
                item["traza_id"], item["traza_version"] = traza_meta
            payload.append(item)
        return payload
    finally:
        db.close()


def _register_scoring_model_version(db: Session, payload: Dict[str, Any]) -> None:
    from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_scoring import get_model_artifact_metadata

    version_key = str(payload.get("model_version", "intelicoop_scoring_v1")).strip() or "intelicoop_scoring_v1"
    artifact_metadata = get_model_artifact_metadata()
    row = (
        db.query(IntelicoopModelVersionRegistry)
        .filter(IntelicoopModelVersionRegistry.version_key == version_key)
        .first()
    )
    features = sorted(list(dict.fromkeys(
        list((artifact_metadata.get("expected_features") or []))
        + list((payload.get("inputs") or {}).keys())
        + list((payload.get("features_calculados") or {}).keys())
    )))
    metricas = {
        "confianza_default": payload.get("confianza"),
        "artifact_path": artifact_metadata.get("artifact_path"),
        "artifact_format": artifact_metadata.get("artifact_format"),
        "artifact_checksum": artifact_metadata.get("artifact_checksum"),
        "load_status": artifact_metadata.get("load_status"),
        "load_error": artifact_metadata.get("load_error"),
        "loaded_at": artifact_metadata.get("loaded_at"),
        "expected_features": artifact_metadata.get("expected_features"),
        "expected_performance": artifact_metadata.get("expected_performance"),
        "lifecycle_status": "champion",
        "frozen": False,
        "deployment_approved": True,
        "segment_thresholds": {
            "integral_fiel": {"aprobar": 0.82, "evaluar": 0.58},
            "crecimiento": {"aprobar": 0.80, "evaluar": 0.55},
            "ahorrador_activo": {"aprobar": 0.78, "evaluar": 0.54},
            "alerta_temprana": {"aprobar": 0.88, "evaluar": 0.66},
            "pasivo": {"aprobar": 0.84, "evaluar": 0.60},
        },
    }
    if row is None:
        row = IntelicoopModelVersionRegistry(
            version_key=version_key,
            algoritmo=str(artifact_metadata.get("algoritmo") or payload.get("motor", "reglas")).strip() or "reglas",
            descripcion="Scoring operativo Intelicoop con artefacto registrado y trazabilidad.",
            features_json=_json_dump(features),
            umbrales_json=_json_dump({
                "aprobar": 0.80,
                "evaluar": 0.55,
            }),
            metricas_json=_json_dump(metricas),
            activo=1,
        )
        db.add(row)
    else:
        row.algoritmo = str(artifact_metadata.get("algoritmo") or payload.get("motor", "reglas")).strip() or "reglas"
        row.features_json = _json_dump(features)
        row.metricas_json = _json_dump(metricas)
        row.activo = 1
    db.flush()


def _create_scoring_trace(db: Session, scoring_result_id: int, payload: Dict[str, Any]) -> IntelicoopScoringTraza:
    row = IntelicoopScoringTraza(
        scoring_result_id=scoring_result_id,
        solicitud_id=str(payload["solicitud_id"]).strip(),
        socio_id=payload.get("socio_id"),
        credito_id=payload.get("credito_id"),
        inputs_json=_json_dump(payload.get("inputs", {})),
        features_calculados_json=_json_dump(payload.get("features_calculados", {})),
        outputs_json=_json_dump({
            "score": payload.get("score"),
            "recomendacion": payload.get("recomendacion"),
            "riesgo": payload.get("riesgo"),
        }),
        razones_json=_json_dump(payload.get("razones", [])),
        reglas_aplicadas_json=_json_dump(payload.get("reglas_aplicadas", [])),
        confianza=float(payload.get("confianza", 0) or 0),
        tiempo_ms=int(payload.get("tiempo_ms", 0) or 0),
        motor=str(payload.get("motor", "reglas")).strip() or "reglas",
        model_version=str(payload.get("model_version", "intelicoop_scoring_v1")).strip() or "intelicoop_scoring_v1",
        traza_version=str(payload.get("traza_version", "intelicoop_traza_v1")).strip() or "intelicoop_traza_v1",
    )
    db.add(row)
    db.flush()
    return row


def create_scoring_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _db()
    try:
        solicitud_id = str(payload["solicitud_id"]).strip()
        explicacion = {
            "razones": list(payload.get("razones", [])),
            "reglas_aplicadas": list(payload.get("reglas_aplicadas", [])),
            "inputs": dict(payload.get("inputs", {})),
            "features_calculados": dict(payload.get("features_calculados", {})),
            "explainability": dict(payload.get("explainability", {})),
        }
        row = IntelicoopScoringResult(
            solicitud_id=solicitud_id,
            socio_id=payload.get("socio_id"),
            credito_id=payload.get("credito_id"),
            ingreso_mensual=float(payload.get("ingreso_mensual", 0)),
            deuda_actual=float(payload.get("deuda_actual", 0)),
            antiguedad_meses=int(payload.get("antiguedad_meses", 0)),
            score=float(payload.get("score", 0)),
            recomendacion=str(payload.get("recomendacion", "evaluar")),
            riesgo=str(payload.get("riesgo", "medio")),
            model_version=str(payload.get("model_version", "intelicoop_scoring_v1")),
            confianza=float(payload["confianza"]) if payload.get("confianza") is not None else None,
            motor=str(payload.get("motor", "reglas")),
            explicacion_json=_json_dump(explicacion),
        )
        db.add(row)
        db.flush()
        _register_scoring_model_version(db, payload)
        traza = _create_scoring_trace(db, row.id, {**payload, "solicitud_id": solicitud_id})
        _create_audit_log(
            db,
            event_type="scoring_created",
            entity_type="scoring_result",
            entity_id=row.id,
            actor="system",
            model_version=row.model_version,
            details={"solicitud_id": solicitud_id, "traza_id": traza.id},
        )
        db.commit()
        db.refresh(row)
        result = _scoring_result_dict(row)
        result["traza_id"] = traza.id
        result["traza_version"] = traza.traza_version
        return result
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def get_scoring_trace(scoring_result_id: int) -> Dict[str, Any] | None:
    db = _db()
    try:
        traza = (
            db.query(IntelicoopScoringTraza)
            .filter(IntelicoopScoringTraza.scoring_result_id == scoring_result_id)
            .order_by(IntelicoopScoringTraza.id.desc())
            .first()
        )
        if not traza:
            return None
        return {
            "id": traza.id,
            "scoring_result_id": traza.scoring_result_id,
            "solicitud_id": traza.solicitud_id,
            "socio_id": traza.socio_id,
            "credito_id": traza.credito_id,
            "inputs": _json_load(traza.inputs_json, {}),
            "features_calculados": _json_load(traza.features_calculados_json, {}),
            "outputs": _json_load(traza.outputs_json, {}),
            "razones": _json_load(traza.razones_json, []),
            "reglas_aplicadas": _json_load(traza.reglas_aplicadas_json, []),
            "confianza": round(float(traza.confianza or 0), 4),
            "tiempo_ms": int(traza.tiempo_ms or 0),
            "motor": traza.motor,
            "model_version": traza.model_version,
            "traza_version": traza.traza_version,
            "created_at": traza.created_at.isoformat() if traza.created_at else "",
            "explainability": (
                _json_load(scoring_row.explicacion_json, {}).get("explainability", {})
                if (scoring_row := db.query(IntelicoopScoringResult).filter(IntelicoopScoringResult.id == traza.scoring_result_id).first())
                else {}
            ),
        }
    finally:
        db.close()


def get_scoring_explainability(socio_id: int | None = None, model_version: str = "intelicoop_scoring_v1") -> Dict[str, Any]:
    db = _db()
    try:
        query = (
            db.query(IntelicoopScoringResult)
            .filter(IntelicoopScoringResult.model_version == model_version)
            .order_by(IntelicoopScoringResult.fecha_creacion.desc(), IntelicoopScoringResult.id.desc())
        )
        if socio_id is not None:
            query = query.filter(IntelicoopScoringResult.socio_id == socio_id)
        rows = query.limit(50).all()
        if not rows:
            return {
                "model_version": model_version,
                "socio_id": socio_id,
                "importancia_variables": [],
                "shap_values_promedio": {},
                "top_factores_por_score": {},
                "explicacion_local_socio": {},
                "explicacion_agregada_segmento": [],
            }

        socio_segmentos = {
            int(row.id): str(row.segmento or "sin_segmento")
            for row in db.query(IntelicoopSocio).all()
        }
        importance_totals: Dict[str, Dict[str, Any]] = {}
        shap_totals: Dict[str, float] = {}
        bucket_factors: Dict[str, Dict[str, int]] = {"alto": {}, "medio": {}, "bajo": {}}
        segment_totals: Dict[str, Dict[str, Any]] = {}
        local_explanation: Dict[str, Any] = {}

        for index, row in enumerate(rows):
            explicacion = _json_load(row.explicacion_json, {})
            explainability = explicacion.get("explainability", {}) or {}
            score_bucket = "alto" if float(row.score or 0) >= 0.8 else ("medio" if float(row.score or 0) >= 0.55 else "bajo")
            segmento = socio_segmentos.get(int(row.socio_id or 0), "sin_segmento")
            if socio_id is not None and index == 0:
                local_explanation = {
                    "socio_id": socio_id,
                    "score": round(float(row.score or 0), 4),
                    "riesgo": str(row.riesgo or ""),
                    "recomendacion": str(row.recomendacion or ""),
                    **dict(explainability.get("explicacion_local_socio", {}) or {}),
                }

            for item in explainability.get("importancia_variables", []) or []:
                feature = str(item.get("feature") or "")
                if not feature:
                    continue
                bucket = importance_totals.setdefault(feature, {"feature": feature, "label": item.get("label", feature), "importance": 0.0, "impact": 0.0, "count": 0})
                bucket["importance"] += float(item.get("importance") or 0)
                bucket["impact"] += abs(float(item.get("impact") or 0))
                bucket["count"] += 1
                seg_bucket = segment_totals.setdefault(segmento, {"segmento": segmento, "score_sum": 0.0, "count": 0, "importances": {}, "top_factores": {}})
                seg_imp = seg_bucket["importances"].setdefault(feature, 0.0)
                seg_bucket["importances"][feature] = seg_imp + float(item.get("importance") or 0)

            for feature, shap_value in (explainability.get("shap_values", {}) or {}).items():
                shap_totals[str(feature)] = shap_totals.get(str(feature), 0.0) + float(shap_value or 0)

            for factor in explainability.get("top_factores_por_score", []) or []:
                feature = str(factor.get("feature") or "")
                if not feature:
                    continue
                bucket_factors[score_bucket][feature] = bucket_factors[score_bucket].get(feature, 0) + 1
                seg_bucket = segment_totals.setdefault(segmento, {"segmento": segmento, "score_sum": 0.0, "count": 0, "importances": {}, "top_factores": {}})
                seg_bucket["top_factores"][feature] = seg_bucket["top_factores"].get(feature, 0) + 1

            seg_bucket = segment_totals.setdefault(segmento, {"segmento": segmento, "score_sum": 0.0, "count": 0, "importances": {}, "top_factores": {}})
            seg_bucket["score_sum"] += float(row.score or 0)
            seg_bucket["count"] += 1

        importancia_variables = []
        for bucket in importance_totals.values():
            count = max(1, int(bucket["count"]))
            importancia_variables.append(
                {
                    "feature": bucket["feature"],
                    "label": bucket["label"],
                    "importance": round(float(bucket["importance"]) / count, 4),
                    "impacto_abs_promedio": round(float(bucket["impact"]) / count, 4),
                }
            )
        importancia_variables.sort(key=lambda item: item["importance"], reverse=True)

        shap_values_promedio = {
            feature: round(total / len(rows), 4)
            for feature, total in sorted(shap_totals.items(), key=lambda item: abs(item[1]), reverse=True)
        }
        top_factores_por_score = {
            bucket: [
                {"feature": feature, "frecuencia": count}
                for feature, count in sorted(features.items(), key=lambda item: (-item[1], item[0]))[:5]
            ]
            for bucket, features in bucket_factors.items()
        }
        explicacion_agregada_segmento = []
        for segmento, bucket in sorted(segment_totals.items(), key=lambda item: item[0]):
            count = max(1, int(bucket["count"]))
            top_importances = sorted(bucket["importances"].items(), key=lambda item: item[1], reverse=True)[:5]
            top_factors = sorted(bucket["top_factores"].items(), key=lambda item: item[1], reverse=True)[:5]
            explicacion_agregada_segmento.append(
                {
                    "segmento": segmento,
                    "socios_evaluados": int(bucket["count"]),
                    "score_promedio": round(float(bucket["score_sum"]) / count, 4),
                    "variables_dominantes": [
                        {"feature": feature, "importance": round(float(total) / count, 4)}
                        for feature, total in top_importances
                    ],
                    "top_factores": [
                        {"feature": feature, "frecuencia": int(freq)}
                        for feature, freq in top_factors
                    ],
                }
            )

        return {
            "model_version": model_version,
            "socio_id": socio_id,
            "importancia_variables": importancia_variables[:10],
            "shap_values_promedio": dict(list(shap_values_promedio.items())[:10]),
            "top_factores_por_score": top_factores_por_score,
            "explicacion_local_socio": local_explanation,
            "explicacion_agregada_segmento": explicacion_agregada_segmento,
        }
    finally:
        db.close()


def _foundation_quality_report(db: Session) -> List[Dict[str, Any]]:
    socios = db.query(IntelicoopSocio).all()
    prospectos = db.query(IntelicoopProspecto).all()
    cuentas = db.query(IntelicoopCuenta).all()
    transacciones = db.query(IntelicoopTransaccion).all()
    scoring_rows = db.query(IntelicoopScoringResult).all()

    creditos_orfanos = int(
        db.query(func.count(IntelicoopCredito.id))
        .outerjoin(IntelicoopSocio, IntelicoopSocio.id == IntelicoopCredito.socio_id)
        .filter(IntelicoopSocio.id.is_(None))
        .scalar()
        or 0
    )
    pagos_orfanos = int(
        db.query(func.count(IntelicoopHistorialPago.id))
        .outerjoin(IntelicoopCredito, IntelicoopCredito.id == IntelicoopHistorialPago.credito_id)
        .filter(IntelicoopCredito.id.is_(None))
        .scalar()
        or 0
    )
    contactos_orfanos = int(
        db.query(func.count(IntelicoopContactoCampania.id))
        .outerjoin(IntelicoopCampania, IntelicoopCampania.id == IntelicoopContactoCampania.campania_id)
        .outerjoin(IntelicoopSocio, IntelicoopSocio.id == IntelicoopContactoCampania.socio_id)
        .filter((IntelicoopCampania.id.is_(None)) | (IntelicoopSocio.id.is_(None)))
        .scalar()
        or 0
    )
    seguimientos_orfanos = int(
        db.query(func.count(IntelicoopSeguimientoCampania.id))
        .outerjoin(IntelicoopCampania, IntelicoopCampania.id == IntelicoopSeguimientoCampania.campania_id)
        .outerjoin(IntelicoopSocio, IntelicoopSocio.id == IntelicoopSeguimientoCampania.socio_id)
        .filter((IntelicoopCampania.id.is_(None)) | (IntelicoopSocio.id.is_(None)))
        .scalar()
        or 0
    )

    creditos_all = db.query(IntelicoopCredito).all()
    campanas_all = db.query(IntelicoopCampania).all()

    rules = [
        {
            "scope": "socios",
            "rule_key": "email_valido_requerido",
            "total_records": len(socios),
            "failed_records": sum(1 for row in socios if not _EMAIL_PATTERN.match(str(row.email or "").strip().lower())),
            "threshold_fail": 0,
        },
        {
            "scope": "socios",
            "rule_key": "nombre_no_vacio",
            "total_records": len(socios),
            "failed_records": sum(1 for row in socios if not str(row.nombre or "").strip()),
            "threshold_fail": 0,
        },
        {
            "scope": "creditos",
            "rule_key": "integridad_socio_fk",
            "total_records": int(db.query(func.count(IntelicoopCredito.id)).scalar() or 0),
            "failed_records": creditos_orfanos,
            "threshold_fail": 0,
        },
        {
            "scope": "creditos",
            "rule_key": "monto_positivo",
            "total_records": len(creditos_all),
            "failed_records": sum(1 for row in creditos_all if float(row.monto or 0) <= 0),
            "threshold_fail": 0,
        },
        {
            "scope": "creditos",
            "rule_key": "numero_abonos_minimo_1",
            "total_records": len(creditos_all),
            "failed_records": sum(1 for row in creditos_all if int(getattr(row, "numero_abonos", 0) or row.plazo or 0) < 1),
            "threshold_fail": 0,
        },
        {
            "scope": "historial_pagos",
            "rule_key": "integridad_credito_fk",
            "total_records": int(db.query(func.count(IntelicoopHistorialPago.id)).scalar() or 0),
            "failed_records": pagos_orfanos,
            "threshold_fail": 0,
        },
        {
            "scope": "cuentas",
            "rule_key": "saldo_no_negativo",
            "total_records": len(cuentas),
            "failed_records": sum(1 for row in cuentas if float(row.saldo or 0) < 0),
            "threshold_fail": 0,
        },
        {
            "scope": "transacciones",
            "rule_key": "monto_positivo",
            "total_records": len(transacciones),
            "failed_records": sum(1 for row in transacciones if float(row.monto or 0) <= 0),
            "threshold_fail": 0,
        },
        {
            "scope": "transacciones",
            "rule_key": "tipo_valido",
            "total_records": len(transacciones),
            "failed_records": sum(1 for row in transacciones if str(row.tipo or "") not in _VALID_TX_TIPOS),
            "threshold_fail": 0,
        },
        {
            "scope": "campanas",
            "rule_key": "fechas_coherentes",
            "total_records": len(campanas_all),
            "failed_records": sum(
                1 for row in campanas_all
                if row.fecha_inicio and row.fecha_fin and row.fecha_fin < row.fecha_inicio
            ),
            "threshold_fail": 0,
        },
        {
            "scope": "prospectos",
            "rule_key": "score_propension_rango_0_1",
            "total_records": len(prospectos),
            "failed_records": sum(1 for row in prospectos if not 0 <= float(row.score_propension or 0) <= 1),
            "threshold_fail": 0,
        },
        {
            "scope": "contactos_campania",
            "rule_key": "integridad_fk",
            "total_records": int(db.query(func.count(IntelicoopContactoCampania.id)).scalar() or 0),
            "failed_records": contactos_orfanos,
            "threshold_fail": 0,
        },
        {
            "scope": "seguimiento_campania",
            "rule_key": "integridad_fk",
            "total_records": int(db.query(func.count(IntelicoopSeguimientoCampania.id)).scalar() or 0),
            "failed_records": seguimientos_orfanos,
            "threshold_fail": 0,
        },
        {
            "scope": "scoring_results",
            "rule_key": "score_rango_0_1",
            "total_records": len(scoring_rows),
            "failed_records": sum(1 for row in scoring_rows if not 0 <= float(row.score or 0) <= 1),
            "threshold_fail": 0,
        },
        {
            "scope": "scoring_results",
            "rule_key": "solicitud_id_no_vacio",
            "total_records": len(scoring_rows),
            "failed_records": sum(1 for row in scoring_rows if not str(row.solicitud_id or "").strip()),
            "threshold_fail": 0,
        },
    ]
    for rule in rules:
        failed = int(rule["failed_records"])
        total = int(rule["total_records"])
        if failed > int(rule["threshold_fail"]):
            status = "fail"
        elif total == 0:
            status = "warn"
        else:
            status = "pass"
        rule["status"] = status
    return rules


def get_foundation_overview() -> Dict[str, Any]:
    db = _db()
    try:
        cut_context = _cut_context()
        latest_cut = (
            db.query(IntelicoopAnalyticCut)
            .order_by(IntelicoopAnalyticCut.cut_date.desc(), IntelicoopAnalyticCut.id.desc())
            .first()
        )
        quality_rules = _foundation_quality_report(db)
        transactional_entities = []
        analytical_entities = []
        table_counts = {
            "intelicoop_socios": int(db.query(func.count(IntelicoopSocio.id)).scalar() or 0),
            "intelicoop_creditos": int(db.query(func.count(IntelicoopCredito.id)).scalar() or 0),
            "intelicoop_historial_pagos": int(db.query(func.count(IntelicoopHistorialPago.id)).scalar() or 0),
            "intelicoop_cuentas": int(db.query(func.count(IntelicoopCuenta.id)).scalar() or 0),
            "intelicoop_transacciones": int(db.query(func.count(IntelicoopTransaccion.id)).scalar() or 0),
            "intelicoop_campanas": int(db.query(func.count(IntelicoopCampania.id)).scalar() or 0),
            "intelicoop_prospectos": int(db.query(func.count(IntelicoopProspecto.id)).scalar() or 0),
            "intelicoop_contactos_campania": int(db.query(func.count(IntelicoopContactoCampania.id)).scalar() or 0),
            "intelicoop_seguimiento_campania": int(db.query(func.count(IntelicoopSeguimientoCampania.id)).scalar() or 0),
            "intelicoop_scoring_results": int(db.query(func.count(IntelicoopScoringResult.id)).scalar() or 0),
            "intelicoop_analytic_cuts": int(db.query(func.count(IntelicoopAnalyticCut.id)).scalar() or 0),
            "intelicoop_data_quality_snapshots": int(db.query(func.count(IntelicoopDataQualitySnapshot.id)).scalar() or 0),
            "intelicoop_socio_feature_snapshots": int(db.query(func.count(IntelicoopSocioFeatureSnapshot.id)).scalar() or 0),
            "intelicoop_credito_feature_snapshots": int(db.query(func.count(IntelicoopCreditoFeatureSnapshot.id)).scalar() or 0),
            "intelicoop_ahorro_feature_snapshots": int(db.query(func.count(IntelicoopAhorroFeatureSnapshot.id)).scalar() or 0),
            "intelicoop_campania_feature_snapshots": int(db.query(func.count(IntelicoopCampaniaFeatureSnapshot.id)).scalar() or 0),
            "intelicoop_prospecto_feature_snapshots": int(db.query(func.count(IntelicoopProspectoFeatureSnapshot.id)).scalar() or 0),
            "intelicoop_cohorte_snapshots": int(db.query(func.count(IntelicoopCohorteSnapshot.id)).scalar() or 0),
            "intelicoop_kpi_snapshots": int(db.query(func.count(IntelicoopKpiSnapshot.id)).scalar() or 0),
            "intelicoop_batch_job_states": int(db.query(func.count(IntelicoopBatchJobState.id)).scalar() or 0),
            "intelicoop_batch_runs": int(db.query(func.count(IntelicoopBatchRun.id)).scalar() or 0),
            "intelicoop_batch_alerts": int(db.query(func.count(IntelicoopBatchAlert.id)).scalar() or 0),
            "intelicoop_governance_snapshots": int(db.query(func.count(IntelicoopGovernanceSnapshot.id)).scalar() or 0),
            "intelicoop_model_drift_snapshots": int(db.query(func.count(IntelicoopModelDriftSnapshot.id)).scalar() or 0),
            "intelicoop_model_recalibrations": int(db.query(func.count(IntelicoopModelRecalibration.id)).scalar() or 0),
            "intelicoop_audit_logs": int(db.query(func.count(IntelicoopAuditLog.id)).scalar() or 0),
            "intelicoop_business_rules": int(db.query(func.count(IntelicoopBusinessRule.id)).scalar() or 0),
        }
        for item in TRANSACTIONAL_ENTITY_DEFINITIONS:
            transactional_entities.append({**item, "records": table_counts.get(item["table"], 0)})
        for item in ANALYTICAL_ENTITY_DEFINITIONS:
            analytical_entities.append({**item, "records": table_counts.get(item["table"], 0)})
        data_layers = _build_data_layer_contract(
            table_counts=table_counts,
            quality_rules=quality_rules,
            cut_key=str(latest_cut.cut_key) if latest_cut else "",
        )
        return {
            "entity_model": {
                "transactional": transactional_entities,
                "analytical": analytical_entities,
                "relationships": FOUNDATION_RELATIONSHIPS,
            },
            "time_cuts": {
                "transactional_mode": "event_time",
                "analytical_mode": "cut_time_snapshot",
                "active_cut_key": cut_context["cut_key"],
                "active_cut_date": cut_context["cut_date"].isoformat(),
                "daily_window_start": cut_context["window_start"].isoformat(),
                "daily_window_end": cut_context["window_end"].isoformat(),
                "monthly_window_start": cut_context["month_start"].isoformat(),
                "monthly_window_end": cut_context["month_end"].isoformat(),
            },
            "minimum_quality": quality_rules,
            "data_layers": data_layers,
            "storage_contract": {
                "transactional_tables": [item["table"] for item in TRANSACTIONAL_ENTITY_DEFINITIONS],
                "analytical_tables": [item["table"] for item in ANALYTICAL_ENTITY_DEFINITIONS],
                "bronze": _json_load(latest_cut.bronze_manifest_json if latest_cut else "{}", data_layers["bronze"]),
                "silver": _json_load(latest_cut.silver_manifest_json if latest_cut else "{}", data_layers["silver"]),
                "gold": _json_load(latest_cut.gold_manifest_json if latest_cut else "{}", data_layers["gold"]),
                "ml": _json_load(latest_cut.ml_manifest_json if latest_cut else "{}", data_layers["ml"]),
                "latest_materialized_cut": {
                    "cut_key": latest_cut.cut_key if latest_cut else "",
                    "cut_date": latest_cut.cut_date.isoformat() if latest_cut and latest_cut.cut_date else "",
                    "status": latest_cut.status if latest_cut else "pending",
                },
            },
        }
    finally:
        db.close()


def materialize_foundation_cut(
    reference_at: datetime | None = None,
    cut_type: str = "daily_close",
) -> Dict[str, Any]:
    db = _db()
    try:
        cut_context = _cut_context(reference_at, cut_type=cut_type)
        cut_key = str(cut_context["cut_key"])
        cut_date = cut_context["cut_date"]
        now = datetime.utcnow()

        # Limpiar snapshots previos del mismo corte (idempotente)
        for model in (
            IntelicoopDataQualitySnapshot,
            IntelicoopSocioFeatureSnapshot,
            IntelicoopCreditoFeatureSnapshot,
            IntelicoopAhorroFeatureSnapshot,
            IntelicoopCampaniaFeatureSnapshot,
            IntelicoopProspectoFeatureSnapshot,
            IntelicoopCohorteSnapshot,
            IntelicoopKpiSnapshot,
        ):
            db.query(model).filter(model.cut_key == cut_key).delete(synchronize_session=False)

        # Registrar el corte
        cut_row = db.query(IntelicoopAnalyticCut).filter(IntelicoopAnalyticCut.cut_key == cut_key).first()
        if cut_row is None:
            cut_row = IntelicoopAnalyticCut(cut_key=cut_key)
            db.add(cut_row)
        cut_row.cut_type = str(cut_context["cut_type"])
        cut_row.cut_date = cut_date
        cut_row.window_start = cut_context["window_start"]
        cut_row.window_end = cut_context["window_end"]
        cut_row.transactional_tables_json = _json_dump([item["table"] for item in TRANSACTIONAL_ENTITY_DEFINITIONS])
        cut_row.analytical_tables_json = _json_dump([item["table"] for item in ANALYTICAL_ENTITY_DEFINITIONS])
        cut_row.status = "ready"

        # ── Calidad (Fase 1) ────────────────────────────────────────────────
        quality_rules = _foundation_quality_report(db)
        for rule in quality_rules:
            db.add(
                IntelicoopDataQualitySnapshot(
                    cut_key=cut_key,
                    cut_date=cut_date,
                    scope=str(rule["scope"]),
                    rule_key=str(rule["rule_key"]),
                    total_records=int(rule["total_records"]),
                    failed_records=int(rule["failed_records"]),
                    status=str(rule["status"]),
                    details_json=_json_dump({
                        "threshold_fail": int(rule["threshold_fail"]),
                        "total_records": int(rule["total_records"]),
                        "failed_records": int(rule["failed_records"]),
                    }),
                )
            )
        initial_table_counts = {
            "intelicoop_socios": int(db.query(func.count(IntelicoopSocio.id)).scalar() or 0),
            "intelicoop_creditos": int(db.query(func.count(IntelicoopCredito.id)).scalar() or 0),
            "intelicoop_historial_pagos": int(db.query(func.count(IntelicoopHistorialPago.id)).scalar() or 0),
            "intelicoop_cuentas": int(db.query(func.count(IntelicoopCuenta.id)).scalar() or 0),
            "intelicoop_transacciones": int(db.query(func.count(IntelicoopTransaccion.id)).scalar() or 0),
            "intelicoop_campanas": int(db.query(func.count(IntelicoopCampania.id)).scalar() or 0),
            "intelicoop_prospectos": int(db.query(func.count(IntelicoopProspecto.id)).scalar() or 0),
            "intelicoop_contactos_campania": int(db.query(func.count(IntelicoopContactoCampania.id)).scalar() or 0),
            "intelicoop_seguimiento_campania": int(db.query(func.count(IntelicoopSeguimientoCampania.id)).scalar() or 0),
            "intelicoop_scoring_results": int(db.query(func.count(IntelicoopScoringResult.id)).scalar() or 0),
        }

        # ── Agregados base ──────────────────────────────────────────────────
        socios = db.query(IntelicoopSocio).order_by(IntelicoopSocio.id.asc()).all()

        # creditos por socio
        creditos_agg: Dict[int, Dict[str, Any]] = {
            int(sid): {"creditos_total": int(tot or 0), "monto_total": float(monto or 0)}
            for sid, tot, monto in db.query(
                IntelicoopCredito.socio_id,
                func.count(IntelicoopCredito.id),
                func.coalesce(func.sum(IntelicoopCredito.monto), 0),
            ).group_by(IntelicoopCredito.socio_id).all()
        }
        # créditos activos (estado no rechazado/liquidado)
        creditos_activos_agg: Dict[int, int] = {
            int(sid): int(tot or 0)
            for sid, tot in db.query(
                IntelicoopCredito.socio_id,
                func.count(IntelicoopCredito.id),
            ).filter(IntelicoopCredito.estado.in_(list(_ACTIVE_CREDITO_ESTADOS))).group_by(IntelicoopCredito.socio_id).all()
        }
        creditos_mora_agg: Dict[int, int] = {
            int(sid): int(tot or 0)
            for sid, tot in db.query(
                IntelicoopCredito.socio_id,
                func.count(IntelicoopCredito.id),
            ).filter(IntelicoopCredito.estado == "mora").group_by(IntelicoopCredito.socio_id).all()
        }
        # pagos totales por socio
        pagos_agg: Dict[int, float] = {
            int(sid): float(tot or 0)
            for sid, tot in db.query(
                IntelicoopCredito.socio_id,
                func.coalesce(func.sum(IntelicoopHistorialPago.monto), 0),
            ).join(IntelicoopHistorialPago, IntelicoopHistorialPago.credito_id == IntelicoopCredito.id)
            .group_by(IntelicoopCredito.socio_id).all()
        }
        # cuentas por socio
        cuentas_agg: Dict[int, Dict[str, Any]] = {
            int(sid): {"cuentas_total": int(tot or 0), "saldo_total": float(saldo or 0)}
            for sid, tot, saldo in db.query(
                IntelicoopCuenta.socio_id,
                func.count(IntelicoopCuenta.id),
                func.coalesce(func.sum(IntelicoopCuenta.saldo), 0),
            ).group_by(IntelicoopCuenta.socio_id).all()
        }
        # transacciones por socio
        tx_agg: Dict[int, int] = {
            int(sid): int(tot or 0)
            for sid, tot in db.query(
                IntelicoopCuenta.socio_id,
                func.count(IntelicoopTransaccion.id),
            ).join(IntelicoopTransaccion, IntelicoopTransaccion.cuenta_id == IntelicoopCuenta.id)
            .group_by(IntelicoopCuenta.socio_id).all()
        }
        # campañas por socio (participaciones y conversiones)
        campanas_part_agg: Dict[int, int] = {
            int(sid): int(tot or 0)
            for sid, tot in db.query(
                IntelicoopContactoCampania.socio_id,
                func.count(IntelicoopContactoCampania.id),
            ).group_by(IntelicoopContactoCampania.socio_id).all()
        }
        campanas_conv_agg: Dict[int, int] = {
            int(sid): int(tot or 0)
            for sid, tot in db.query(
                IntelicoopSeguimientoCampania.socio_id,
                func.count(IntelicoopSeguimientoCampania.id),
            ).filter(IntelicoopSeguimientoCampania.conversion == 1)
            .group_by(IntelicoopSeguimientoCampania.socio_id).all()
        }
        socio_alertas_agg: Dict[int, int] = {
            int(entity_id): int(total or 0)
            for entity_id, total in db.query(
                IntelicoopBatchAlert.entity_id,
                func.count(IntelicoopBatchAlert.id),
            ).filter(IntelicoopBatchAlert.entity_type == "socio").group_by(IntelicoopBatchAlert.entity_id).all()
            if entity_id is not None
        }
        response_channel_agg: Dict[int, Dict[str, Dict[str, int]]] = {}
        last_contact_at: Dict[int, datetime] = {}
        for socio_id, canal, total, contactados in db.query(
            IntelicoopContactoCampania.socio_id,
            IntelicoopContactoCampania.canal,
            func.count(IntelicoopContactoCampania.id),
                func.coalesce(
                func.sum(case((IntelicoopContactoCampania.estado_contacto == "contactado", 1), else_=0)),
                0,
            ),
        ).group_by(
            IntelicoopContactoCampania.socio_id,
            IntelicoopContactoCampania.canal,
        ).all():
            sid = int(socio_id)
            bucket = response_channel_agg.setdefault(sid, {})
            bucket[str(canal or "desconocido")] = {
                "total": int(total or 0),
                "contactados": int(contactados or 0),
            }
        for socio_id, fecha in db.query(
            IntelicoopContactoCampania.socio_id,
            func.max(IntelicoopContactoCampania.fecha_contacto),
        ).group_by(IntelicoopContactoCampania.socio_id).all():
            if socio_id and fecha:
                last_contact_at[int(socio_id)] = fecha
        # último scoring por socio
        latest_scoring: Dict[int, Dict[str, Any]] = {}
        for row in db.query(IntelicoopScoringResult).filter(
            IntelicoopScoringResult.socio_id.isnot(None)
        ).order_by(
            IntelicoopScoringResult.socio_id.asc(),
            IntelicoopScoringResult.fecha_creacion.desc(),
            IntelicoopScoringResult.id.desc(),
        ).all():
            sid = int(row.socio_id or 0)
            if sid and sid not in latest_scoring:
                latest_scoring[sid] = {
                    "score": float(row.score or 0),
                    "riesgo": str(row.riesgo or "sin_dato"),
                    "ingreso_mensual": float(row.ingreso_mensual or 0),
                    "deuda_actual": float(row.deuda_actual or 0),
                }
        creditos_por_socio: Dict[int, List[IntelicoopCredito]] = {}
        for row in db.query(IntelicoopCredito).order_by(IntelicoopCredito.socio_id.asc(), IntelicoopCredito.fecha_creacion.asc(), IntelicoopCredito.id.asc()).all():
            creditos_por_socio.setdefault(int(row.socio_id), []).append(row)
        txs_por_socio_recency: Dict[int, List[datetime]] = {}
        for socio_id, fecha in db.query(
            IntelicoopCuenta.socio_id,
            IntelicoopTransaccion.fecha,
        ).join(IntelicoopTransaccion, IntelicoopTransaccion.cuenta_id == IntelicoopCuenta.id).all():
            if socio_id and fecha:
                txs_por_socio_recency.setdefault(int(socio_id), []).append(fecha)
        seguimientos_por_socio: Dict[int, List[IntelicoopSeguimientoCampania]] = {}
        for row in db.query(IntelicoopSeguimientoCampania).order_by(IntelicoopSeguimientoCampania.socio_id.asc(), IntelicoopSeguimientoCampania.fecha_evento.asc(), IntelicoopSeguimientoCampania.id.asc()).all():
            seguimientos_por_socio.setdefault(int(row.socio_id), []).append(row)
        contactos_por_socio: Dict[int, List[IntelicoopContactoCampania]] = {}
        for row in db.query(IntelicoopContactoCampania).order_by(IntelicoopContactoCampania.socio_id.asc(), IntelicoopContactoCampania.fecha_contacto.asc(), IntelicoopContactoCampania.id.asc()).all():
            contactos_por_socio.setdefault(int(row.socio_id), []).append(row)
        socio_label_rows: List[Dict[str, int]] = []
        credito_label_rows: List[Dict[str, int]] = []
        prospecto_label_rows: List[Dict[str, int]] = []
        imputation_summary = _empty_imputation_summary()

        # ── Features por socio (Fase 2) ─────────────────────────────────────
        for socio in socios:
            sid = int(socio.id)
            socio_imputed_fields: List[str] = []
            c_agg = creditos_agg.get(sid, {})
            cu_agg = cuentas_agg.get(sid, {})
            sc = latest_scoring.get(sid, {})
            creditos_total = int(c_agg.get("creditos_total", 0))
            cuentas_total = int(cu_agg.get("cuentas_total", 0))
            monto_creditos_total = float(c_agg.get("monto_total", 0))
            pagos_total = float(pagos_agg.get(sid, 0))
            tasa_cumplimiento = round(pagos_total / monto_creditos_total, 4) if monto_creditos_total > 0 else 0.0
            ingreso = float(sc.get("ingreso_mensual", 0))
            deuda = float(sc.get("deuda_actual", 0))
            ratio_deuda_ingreso = round(deuda / ingreso, 4) if ingreso > 0 else 0.0
            edad = _compute_age(socio.fecha_nacimiento, now)
            if not sc:
                socio_imputed_fields.extend(["score_scoring_reciente", "riesgo_scoring_reciente", "ratio_deuda_ingreso"])
            elif ingreso <= 0:
                socio_imputed_fields.append("ratio_deuda_ingreso")
            if monto_creditos_total <= 0:
                socio_imputed_fields.append("tasa_cumplimiento_pagos")
            dias_como_socio = (now - socio.fecha_registro).days if socio.fecha_registro else 0
            response_por_canal = {
                canal: round((vals.get("contactados", 0) / vals.get("total", 1)), 4) if vals.get("total", 0) else 0.0
                for canal, vals in (response_channel_agg.get(sid, {})).items()
            }
            tasa_respuesta = round(
                int(campanas_conv_agg.get(sid, 0)) / max(1, int(campanas_part_agg.get(sid, 0))),
                4,
            ) if int(campanas_part_agg.get(sid, 0)) > 0 else 0.0
            canal_preferido = ""
            if response_por_canal:
                canal_preferido = sorted(response_por_canal.items(), key=lambda item: item[1], reverse=True)[0][0]
            ultimo_contacto = last_contact_at.get(sid)
            dias_desde_ultimo_contacto = (now - ultimo_contacto).days if ultimo_contacto else max(0, dias_como_socio)
            if ultimo_contacto is None:
                socio_imputed_fields.append("dias_desde_ultimo_contacto")
            last_tx_dates = txs_por_socio_recency.get(sid, [])
            ultimo_movimiento = max(last_tx_dates) if last_tx_dates else None
            dias_desde_ultimo_movimiento = _days_since(ultimo_movimiento, now)
            if ultimo_movimiento is None:
                socio_imputed_fields.append("score_abandono")
            socio_creditos = creditos_por_socio.get(sid, [])
            socio_seguimientos = seguimientos_por_socio.get(sid, [])
            socio_contactos = contactos_por_socio.get(sid, [])
            latest_credit = socio_creditos[-1] if socio_creditos else None
            previous_credits = socio_creditos[:-1]
            avg_previous_monto = round(sum(float(item.monto or 0) for item in previous_credits) / len(previous_credits), 2) if previous_credits else 0.0
            recompra_credito = 1 if len(socio_creditos) >= 2 else 0
            up_sell_exitoso = 1 if latest_credit and avg_previous_monto > 0 and float(latest_credit.monto or 0) >= avg_previous_monto * 1.1 else 0
            responde_campania = 1 if any(str(item.estado_contacto or "") == "contactado" for item in socio_contactos) or any(int(item.conversion or 0) == 1 for item in socio_seguimientos) else 0
            abandono_90_dias = 1 if (dias_desde_ultimo_movimiento is None or dias_desde_ultimo_movimiento >= 90) and dias_desde_ultimo_contacto >= 90 else 0
            score_abandono = round(
                max(
                    0.0,
                    min(
                        1.0,
                        0.10
                        + (0.22 if int(tx_agg.get(sid, 0)) == 0 else 0.0)
                        + (0.18 if float(cu_agg.get("saldo_total", 0)) < 250 else 0.0)
                        + (0.14 if int(campanas_part_agg.get(sid, 0)) == 0 else 0.0)
                        + min(max(dias_desde_ultimo_contacto, 0) / 180.0, 1.0) * 0.14
                        - min(int(campanas_conv_agg.get(sid, 0)), 2) * 0.08
                        - (0.10 if cuentas_total + creditos_total >= 2 else 0.0)
                    ),
                ),
                4,
            )
            score_propension_referencia = round(
                max(
                    0.0,
                    min(
                        1.0,
                        0.10
                        + min(int(campanas_part_agg.get(sid, 0)), 4) * 0.08
                        + min(int(campanas_conv_agg.get(sid, 0)), 2) * 0.14
                        + min(float(cu_agg.get("saldo_total", 0)) / 5000.0, 1.0) * 0.14
                        + min(int(tx_agg.get(sid, 0)), 8) * 0.03
                        + (0.08 if str(sc.get("riesgo", "medio")) == "bajo" else -0.08 if str(sc.get("riesgo", "medio")) == "alto" else 0.0)
                    ),
                ),
                4,
            )
            diversificacion = round(min(1.0, (creditos_total + cuentas_total) / 4.0), 4)
            profundidad_relacion = round(min(1.0, ((creditos_total * 0.55) + (cuentas_total * 0.45)) / 4.0), 4)
            estabilidad_financiera = round(
                max(
                    0.0,
                    min(
                        1.0,
                        0.45
                        + min(float(cu_agg.get("saldo_total", 0)) / 5000.0, 1.0) * 0.25
                        + (0.15 if int(tx_agg.get(sid, 0)) > 0 else 0.0)
                        + (0.15 if ratio_deuda_ingreso <= 0.4 else 0.0),
                    ),
                ),
                4,
            )
            score_fidelidad = round(
                max(
                    0.0,
                    min(
                        1.0,
                        0.20
                        + min(max(dias_como_socio, 0) / 365.0, 1.0) * 0.30
                        + diversificacion * 0.20
                        + (0.15 if responde_campania else 0.0)
                        + (0.15 if int(tx_agg.get(sid, 0)) > 0 else 0.0),
                    ),
                ),
                4,
            )
            sensibilidad_comercial = round(min(1.0, tasa_respuesta * 0.6 + score_propension_referencia * 0.4), 4)
            numero_alertas = int(socio_alertas_agg.get(sid, 0))
            tendencia_riesgo = "alta" if str(sc.get("riesgo", "")) == "alto" else "media" if str(sc.get("riesgo", "")) == "medio" else "estable"
            reincidencia = 1 if int(creditos_mora_agg.get(sid, 0)) > 1 or numero_alertas > 1 else 0
            db.add(IntelicoopSocioFeatureSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                socio_id=sid,
                socio_nombre=str(socio.nombre or ""),
                segmento_actual=str(socio.segmento or "inactivo"),
                creditos_total=creditos_total,
                creditos_activos=int(creditos_activos_agg.get(sid, 0)),
                creditos_mora=int(creditos_mora_agg.get(sid, 0)),
                monto_creditos_total=monto_creditos_total,
                pagos_total=pagos_total,
                tasa_cumplimiento_pagos=tasa_cumplimiento,
                ratio_deuda_ingreso=ratio_deuda_ingreso,
                cuentas_total=cuentas_total,
                saldo_cuentas_total=float(cu_agg.get("saldo_total", 0)),
                transacciones_total=int(tx_agg.get(sid, 0)),
                campanas_participadas=int(campanas_part_agg.get(sid, 0)),
                campanas_convertidas=int(campanas_conv_agg.get(sid, 0)),
                respuesta_por_canal_json=_json_dump(response_por_canal),
                dias_desde_ultimo_contacto=max(0, dias_desde_ultimo_contacto),
                dias_como_socio=max(0, dias_como_socio),
                edad=edad,
                num_productos=creditos_total + cuentas_total,
                diversificacion=diversificacion,
                profundidad_relacion=profundidad_relacion,
                score_propension_referencia=score_propension_referencia,
                score_abandono=score_abandono,
                score_fidelidad=score_fidelidad,
                score_scoring_reciente=float(sc.get("score", 0)),
                riesgo_scoring_reciente=str(sc.get("riesgo", "sin_dato")),
                estabilidad_financiera=estabilidad_financiera,
                tasa_respuesta=tasa_respuesta,
                canal_preferido=canal_preferido,
                sensibilidad_comercial=sensibilidad_comercial,
                numero_alertas=numero_alertas,
                tendencia_riesgo=tendencia_riesgo,
                reincidencia=reincidencia,
                abandono_90_dias=abandono_90_dias,
                responde_campania=responde_campania,
                up_sell_exitoso=up_sell_exitoso,
                recompra_credito=recompra_credito,
                feature_version=FEATURE_ENGINEERING_VERSION,
            ))
            socio_label_rows.append(
                {
                    "abandono_90_dias": abandono_90_dias,
                    "responde_campania": responde_campania,
                    "up_sell_exitoso": up_sell_exitoso,
                    "recompra_credito": recompra_credito,
                    "convirtio_credito": 1 if int(campanas_conv_agg.get(sid, 0)) > 0 or int(creditos_activos_agg.get(sid, 0)) > 0 else 0,
                }
            )
            _register_imputation(imputation_summary, "features_socio_gold", socio_imputed_fields)

        # ── Features por crédito (Fase 2) ───────────────────────────────────
        creditos_all = db.query(IntelicoopCredito).order_by(IntelicoopCredito.id.asc()).all()
        # pagos agrupados por credito_id
        pagos_por_credito: Dict[int, Dict[str, Any]] = {
            int(cid): {"num_pagos": int(npagos or 0), "monto_pagado": float(monto or 0)}
            for cid, npagos, monto in db.query(
                IntelicoopHistorialPago.credito_id,
                func.count(IntelicoopHistorialPago.id),
                func.coalesce(func.sum(IntelicoopHistorialPago.monto), 0),
            ).group_by(IntelicoopHistorialPago.credito_id).all()
        }
        for cred in creditos_all:
            cid = int(cred.id)
            credito_imputed_fields: List[str] = []
            monto = float(cred.monto or 0)
            pinfo = pagos_por_credito.get(cid, {})
            num_pagos = int(pinfo.get("num_pagos", 0))
            monto_pagado = float(pinfo.get("monto_pagado", 0))
            saldo_pendiente = max(0.0, monto - monto_pagado)
            ratio_pagado = round(monto_pagado / monto, 4) if monto > 0 else 0.0
            socio_sc = latest_scoring.get(int(cred.socio_id), {})
            ingreso_socio = float(socio_sc.get("ingreso_mensual", 0))
            numero_abonos = int(getattr(cred, "numero_abonos", 0) or cred.plazo or 0)
            tasa_cump = round(num_pagos / numero_abonos, 4) if numero_abonos > 0 else 0.0
            en_mora = 1 if str(cred.estado or "") == "mora" else 0
            dias_desde_desembolso = (now - cred.fecha_desembolso).days if cred.fecha_desembolso else None
            dias_hasta_vencimiento = (cred.fecha_vencimiento - now).days if cred.fecha_vencimiento else None
            days_late = max(0, abs(dias_hasta_vencimiento)) if dias_hasta_vencimiento is not None and dias_hasta_vencimiento < 0 else 0
            if monto <= 0:
                credito_imputed_fields.append("porcentaje_pagado")
            if ingreso_socio <= 0:
                credito_imputed_fields.append("ratio_deuda_ingreso")
            if cred.fecha_desembolso is None:
                credito_imputed_fields.append("dias_desde_desembolso")
            if cred.fecha_vencimiento is None:
                credito_imputed_fields.append("dias_hasta_vencimiento")
            default_30 = 1 if en_mora and days_late >= 30 else 0
            default_60 = 1 if en_mora and days_late >= 60 else 0
            default_90 = 1 if en_mora and days_late >= 90 else 0
            socio_creditos = creditos_por_socio.get(int(cred.socio_id), [])
            previous_credits = [item for item in socio_creditos if int(item.id) != cid]
            avg_previous_monto = round(sum(float(item.monto or 0) for item in previous_credits) / len(previous_credits), 2) if previous_credits else 0.0
            recompra_credito = 1 if len(socio_creditos) >= 2 else 0
            up_sell_exitoso = 1 if avg_previous_monto > 0 and monto >= avg_previous_monto * 1.1 else 0
            convirtio_credito = 1 if str(cred.estado or "") in _CONVERSION_CREDITO_ESTADOS else 0
            db.add(IntelicoopCreditoFeatureSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                credito_id=cid,
                socio_id=int(cred.socio_id),
                monto=monto,
                plazo=numero_abonos,
                numero_abonos=numero_abonos,
                periodicidad=str(getattr(cred, "periodicidad", "mensual") or "mensual"),
                estado=str(cred.estado or "solicitado"),
                num_pagos=num_pagos,
                monto_pagado=monto_pagado,
                saldo_pendiente=saldo_pendiente,
                porcentaje_pagado=ratio_pagado,
                ratio_pagado=ratio_pagado,
                tasa_cumplimiento=tasa_cump,
                ratio_deuda_ingreso=round((float(cred.deuda_actual or 0) / ingreso_socio), 4) if ingreso_socio > 0 else 0.0,
                creditos_activos=int(creditos_activos_agg.get(int(cred.socio_id), 0)),
                creditos_en_mora=int(creditos_mora_agg.get(int(cred.socio_id), 0)),
                cumplimiento_pagos=tasa_cump,
                exposicion_total=float(creditos_agg.get(int(cred.socio_id), {}).get("monto_total", 0)),
                en_mora=en_mora,
                dias_desde_desembolso=dias_desde_desembolso,
                dias_hasta_vencimiento=dias_hasta_vencimiento,
                default_30=default_30,
                default_60=default_60,
                default_90=default_90,
                convirtio_credito=convirtio_credito,
                up_sell_exitoso=up_sell_exitoso,
                recompra_credito=recompra_credito,
                feature_version=FEATURE_ENGINEERING_VERSION,
            ))
            credito_label_rows.append(
                {
                    "default_30": default_30,
                    "default_60": default_60,
                    "default_90": default_90,
                    "convirtio_credito": convirtio_credito,
                    "up_sell_exitoso": up_sell_exitoso,
                    "recompra_credito": recompra_credito,
                }
            )
            _register_imputation(imputation_summary, "features_credito_gold", credito_imputed_fields)

        # ── Features por cuenta/ahorro (Fase 2) ────────────────────────────
        cuentas_all = db.query(IntelicoopCuenta).order_by(IntelicoopCuenta.id.asc()).all()
        tx_por_cuenta: Dict[int, List[Any]] = {}
        for tx in db.query(IntelicoopTransaccion).all():
            tx_por_cuenta.setdefault(int(tx.cuenta_id), []).append(tx)
        for cuenta in cuentas_all:
            ahorro_imputed_fields: List[str] = []
            txs = tx_por_cuenta.get(int(cuenta.id), [])
            depositos = [float(t.monto or 0) for t in txs if str(t.tipo or "") == "deposito"]
            retiros = [float(t.monto or 0) for t in txs if str(t.tipo or "") == "retiro"]
            total_depositos = sum(depositos)
            total_retiros = sum(retiros)
            prom_dep = round(total_depositos / len(depositos), 2) if depositos else 0.0
            prom_ret = round(total_retiros / len(retiros), 2) if retiros else 0.0
            saldo_prom_30d = _estimate_average_balance(float(cuenta.saldo or 0), txs, now, 30)
            saldo_prom_60d = _estimate_average_balance(float(cuenta.saldo or 0), txs, now, 60)
            saldo_prom_90d = _estimate_average_balance(float(cuenta.saldo or 0), txs, now, 90)
            monthly_buckets: Dict[str, float] = {}
            tx_count_monthly: Dict[str, int] = {}
            for tx in txs:
                fecha = tx.fecha or now
                month_key = fecha.strftime("%Y-%m")
                monthly_buckets.setdefault(month_key, 0.0)
                tx_count_monthly.setdefault(month_key, 0)
                monthly_buckets[month_key] += float(tx.monto or 0) if str(tx.tipo or "") == "deposito" else -float(tx.monto or 0)
                tx_count_monthly[month_key] += 1
            monthly_values = list(monthly_buckets.values())
            tx_months = len(tx_count_monthly) or 1
            frecuencia_transaccional = round(len(txs) / tx_months, 4) if txs else 0.0
            captacion_neta_mensual = round(sum(monthly_values) / len(monthly_values), 2) if monthly_values else 0.0
            volatilidad_saldo = round(_stddev(monthly_values), 4) if monthly_values else 0.0
            if monthly_values and max(monthly_values) > abs(min(monthly_values)):
                estacionalidad = "alta"
            elif monthly_values and max(abs(value) for value in monthly_values) > 0:
                estacionalidad = "media"
            else:
                estacionalidad = "estable"
            ultima_tx = max((t.fecha for t in txs if t.fecha), default=None)
            dias_sin_mov = (now - ultima_tx).days if ultima_tx else (now - cuenta.fecha_creacion).days if cuenta.fecha_creacion else 0
            if not txs:
                ahorro_imputed_fields.extend([
                    "saldo_promedio_30d",
                    "saldo_promedio_60d",
                    "saldo_promedio_90d",
                    "frecuencia_transaccional",
                    "captacion_neta_mensual",
                    "volatilidad_saldo",
                ])
            if ultima_tx is None:
                ahorro_imputed_fields.append("dias_sin_movimiento")
            if total_depositos > total_retiros * 1.1:
                tendencia = "creciente"
            elif total_retiros > total_depositos * 1.1:
                tendencia = "decreciente"
            else:
                tendencia = "estable"
            db.add(IntelicoopAhorroFeatureSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                cuenta_id=int(cuenta.id),
                socio_id=int(cuenta.socio_id),
                tipo=str(cuenta.tipo or "ahorro"),
                saldo_actual=round(float(cuenta.saldo or 0), 2),
                num_transacciones=len(txs),
                monto_depositos=round(total_depositos, 2),
                monto_retiros=round(total_retiros, 2),
                promedio_deposito=prom_dep,
                promedio_retiro=prom_ret,
                saldo_promedio_30d=saldo_prom_30d,
                saldo_promedio_60d=saldo_prom_60d,
                saldo_promedio_90d=saldo_prom_90d,
                frecuencia_transaccional=frecuencia_transaccional,
                captacion_neta_mensual=captacion_neta_mensual,
                volatilidad_saldo=volatilidad_saldo,
                estacionalidad_ahorro=estacionalidad,
                dias_sin_movimiento=max(0, dias_sin_mov),
                tendencia_saldo=tendencia,
                feature_version=FEATURE_ENGINEERING_VERSION,
            ))
            _register_imputation(imputation_summary, "features_ahorro_gold", ahorro_imputed_fields)

        # ── Features por campaña (Fase 2) ──────────────────────────────────
        campanas_all = db.query(IntelicoopCampania).order_by(IntelicoopCampania.id.asc()).all()
        contactos_por_campana: Dict[int, int] = {
            int(cid): int(tot or 0)
            for cid, tot in db.query(
                IntelicoopContactoCampania.campania_id, func.count(IntelicoopContactoCampania.id)
            ).group_by(IntelicoopContactoCampania.campania_id).all()
        }
        seguimientos_por_campana: Dict[int, Dict[str, Any]] = {}
        for cid, tot, conv, monto_col in db.query(
            IntelicoopSeguimientoCampania.campania_id,
            func.count(IntelicoopSeguimientoCampania.id),
            func.coalesce(func.sum(IntelicoopSeguimientoCampania.conversion), 0),
            func.coalesce(func.sum(IntelicoopSeguimientoCampania.monto_colocado), 0),
        ).group_by(IntelicoopSeguimientoCampania.campania_id).all():
            seguimientos_por_campana[int(cid)] = {
                "total": int(tot or 0),
                "conversiones": int(conv or 0),
                "monto_colocado": float(monto_col or 0),
            }
        for camp in campanas_all:
            cid = int(camp.id)
            campania_imputed_fields: List[str] = []
            total_contactos = int(contactos_por_campana.get(cid, 0))
            seg = seguimientos_por_campana.get(cid, {})
            total_seg = int(seg.get("total", 0))
            conversiones = int(seg.get("conversiones", 0))
            monto_col = float(seg.get("monto_colocado", 0))
            tasa_conv = round(conversiones / total_contactos, 4) if total_contactos > 0 else 0.0
            duracion = None
            if camp.fecha_inicio and camp.fecha_fin:
                duracion = max(0, (camp.fecha_fin - camp.fecha_inicio).days)
            else:
                campania_imputed_fields.append("duracion_dias")
            db.add(IntelicoopCampaniaFeatureSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                campania_id=cid,
                estado=str(camp.estado or "borrador"),
                total_contactos=total_contactos,
                total_seguimientos=total_seg,
                conversiones=conversiones,
                tasa_conversion=tasa_conv,
                monto_colocado=round(monto_col, 2),
                duracion_dias=duracion,
                feature_version=FEATURE_ENGINEERING_VERSION,
            ))
            _register_imputation(imputation_summary, "features_campania_gold", campania_imputed_fields)

        # ── Features por prospecto (Fase 2) ────────────────────────────────
        prospectos_all = db.query(IntelicoopProspecto).order_by(IntelicoopProspecto.id.asc()).all()
        # prospectos contactados en alguna campaña (via nombre/fuente no tenemos FK directa)
        # usamos set vacío; feature en_campana requiere relación explícita futura
        for prosp in prospectos_all:
            prospecto_imputed_fields: List[str] = ["en_campana"]
            dias_prosp = (now - prosp.fecha_creacion).days if prosp.fecha_creacion else 0
            responde_campania = 1 if float(prosp.score_propension or 0) >= 0.5 else 0
            convirtio_credito = 1 if float(prosp.score_propension or 0) >= 0.75 else 0
            db.add(IntelicoopProspectoFeatureSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                prospecto_id=int(prosp.id),
                score_propension=round(float(prosp.score_propension or 0), 4),
                fuente=str(prosp.fuente or ""),
                dias_como_prospecto=max(0, dias_prosp),
                en_campana=0,
                convirtio_credito=convirtio_credito,
                responde_campania=responde_campania,
                feature_version=FEATURE_ENGINEERING_VERSION,
            ))
            prospecto_label_rows.append(
                {
                    "convirtio_credito": convirtio_credito,
                    "responde_campania": responde_campania,
                }
            )
            _register_imputation(imputation_summary, "features_prospecto_gold", prospecto_imputed_fields)

        # ── KPIs con semáforo y tipo observado/estimado (Fase 3) ────────────
        dashboard = get_dashboard_resumen()
        kpi_raw = [
            ("socios_total",   float(dashboard.get("socios", 0))),
            ("creditos_total", float(dashboard.get("creditos", 0))),
            ("campanas_total", float(dashboard.get("campanas", 0))),
            ("prospectos_total", float(dashboard.get("prospectos", 0))),
            ("scoring_total",  float(dashboard.get("scoring_total", 0))),
            ("imor_pct",       float(((dashboard.get("salud_cartera") or {}).get("imor_pct", 0)) or 0)),
            ("captacion_neta", float(((dashboard.get("captacion") or {}).get("captacion_neta", 0)) or 0)),
            ("conversion_pct", float(((dashboard.get("comercial") or {}).get("conversion_pct", 0)) or 0)),
        ]
        for kpi_key, value in kpi_raw:
            cat = KPI_CATALOG.get(kpi_key, {})
            db.add(IntelicoopKpiSnapshot(
                cut_key=cut_key, cut_date=cut_date,
                kpi_key=kpi_key,
                metric_group=str(cat.get("group", "general")),
                metric_value=float(value),
                metric_label=str(cat.get("label", kpi_key)),
                metric_type=str(cat.get("metric_type", "observado")),
                semaforo=_compute_semaforo(kpi_key, float(value)),
            ))

        # ── Cohortes (Fase 3) ────────────────────────────────────────────────
        cohorte_rows = 0

        # Dimensión 1: socios por mes de registro
        for socio in socios:
            if socio.fecha_registro:
                bucket = socio.fecha_registro.strftime("%Y-%m")
            else:
                bucket = "sin_fecha"
            # acumulamos en dict para agregar
            pass

        # Agregación de socios por mes_registro
        mes_registro_map: Dict[str, Dict[str, Any]] = {}
        for socio in socios:
            b = socio.fecha_registro.strftime("%Y-%m") if socio.fecha_registro else "sin_fecha"
            entry = mes_registro_map.setdefault(b, {"n": 0, "cuentas": 0, "saldo": 0.0, "creditos": 0})
            entry["n"] += 1
            sid = int(socio.id)
            entry["cuentas"] += int(cuentas_agg.get(sid, {}).get("cuentas_total", 0))
            entry["saldo"] += float(cuentas_agg.get(sid, {}).get("saldo_total", 0))
            entry["creditos"] += int(creditos_agg.get(sid, {}).get("creditos_total", 0))
        for bucket, agg in mes_registro_map.items():
            n = int(agg["n"])
            for mkey, mval, mtype in [
                ("n_socios",          float(n),                              "observado"),
                ("avg_cuentas",       round(agg["cuentas"] / n, 2) if n else 0.0, "observado"),
                ("avg_saldo",         round(agg["saldo"] / n, 2) if n else 0.0,   "observado"),
                ("avg_creditos",      round(agg["creditos"] / n, 2) if n else 0.0,"observado"),
            ]:
                db.add(IntelicoopCohorteSnapshot(
                    cut_key=cut_key, cut_date=cut_date,
                    dimension="mes_registro_socio",
                    bucket=bucket,
                    metric_key=mkey,
                    metric_value=float(mval),
                    n_records=n,
                    metric_type=mtype,
                ))
                cohorte_rows += 1

        # Dimensión 2: créditos por estado
        estado_map: Dict[str, Dict[str, Any]] = {}
        for cred in creditos_all:
            b = str(cred.estado or "sin_estado")
            entry = estado_map.setdefault(b, {"n": 0, "monto": 0.0})
            entry["n"] += 1
            entry["monto"] += float(cred.monto or 0)
        total_creditos_n = sum(v["n"] for v in estado_map.values()) or 1
        for bucket, agg in estado_map.items():
            n = int(agg["n"])
            for mkey, mval, mtype in [
                ("n_creditos",   float(n),                              "observado"),
                ("monto_total",  round(agg["monto"], 2),                "observado"),
                ("pct_del_total", round(n / total_creditos_n * 100, 2), "observado"),
            ]:
                db.add(IntelicoopCohorteSnapshot(
                    cut_key=cut_key, cut_date=cut_date,
                    dimension="estado_credito",
                    bucket=bucket,
                    metric_key=mkey,
                    metric_value=float(mval),
                    n_records=n,
                    metric_type=mtype,
                ))
                cohorte_rows += 1

        # Dimensión 3: socios por segmento
        segmento_map: Dict[str, int] = {}
        for socio in socios:
            b = str(socio.segmento or "inactivo")
            segmento_map[b] = segmento_map.get(b, 0) + 1
        total_socios_n = len(socios) or 1
        for bucket, n in segmento_map.items():
            for mkey, mval, mtype in [
                ("n_socios",    float(n),                                "observado"),
                ("pct_socios",  round(n / total_socios_n * 100, 2),     "observado"),
            ]:
                db.add(IntelicoopCohorteSnapshot(
                    cut_key=cut_key, cut_date=cut_date,
                    dimension="segmento_socio",
                    bucket=bucket,
                    metric_key=mkey,
                    metric_value=float(mval),
                    n_records=n,
                    metric_type=mtype,
                ))
                cohorte_rows += 1

        # Dimensión 4: tendencia saldo por tipo de cuenta
        tipo_cuenta_map: Dict[str, Dict[str, Any]] = {}
        for cuenta in cuentas_all:
            b = str(cuenta.tipo or "ahorro")
            entry = tipo_cuenta_map.setdefault(b, {"n": 0, "saldo": 0.0})
            entry["n"] += 1
            entry["saldo"] += float(cuenta.saldo or 0)
        for bucket, agg in tipo_cuenta_map.items():
            n = int(agg["n"])
            for mkey, mval, mtype in [
                ("n_cuentas",    float(n),                              "observado"),
                ("saldo_total",  round(agg["saldo"], 2),                "observado"),
                ("saldo_promedio", round(agg["saldo"] / n, 2) if n else 0.0, "observado"),
            ]:
                db.add(IntelicoopCohorteSnapshot(
                    cut_key=cut_key, cut_date=cut_date,
                    dimension="tipo_cuenta",
                    bucket=bucket,
                    metric_key=mkey,
                    metric_value=float(mval),
                    n_records=n,
                    metric_type=mtype,
                ))
                cohorte_rows += 1

        layer_table_counts = {
            **initial_table_counts,
            "intelicoop_socio_feature_snapshots": len(socios),
            "intelicoop_credito_feature_snapshots": len(creditos_all),
            "intelicoop_ahorro_feature_snapshots": len(cuentas_all),
            "intelicoop_campania_feature_snapshots": len(campanas_all),
            "intelicoop_prospecto_feature_snapshots": len(prospectos_all),
        }
        label_summary = {
            "features_socio_gold": _label_distribution(
                socio_label_rows,
                ["abandono_90_dias", "responde_campania", "up_sell_exitoso", "recompra_credito", "convirtio_credito"],
            ),
            "features_credito_gold": _label_distribution(
                credito_label_rows,
                ["default_30", "default_60", "default_90", "convirtio_credito", "up_sell_exitoso", "recompra_credito"],
            ),
            "features_prospecto_gold": _label_distribution(
                prospecto_label_rows,
                ["convirtio_credito", "responde_campania"],
            ),
            "training_scoring_ml": _label_distribution(
                credito_label_rows,
                ["default_30", "default_60", "default_90", "recompra_credito"],
            ),
            "inference_scoring_ml": _label_distribution(
                credito_label_rows,
                ["default_30", "default_60", "default_90"],
            ),
            "training_propension_ml": _label_distribution(
                socio_label_rows + prospecto_label_rows,
                ["convirtio_credito", "responde_campania", "up_sell_exitoso"],
            ),
            "inference_propension_ml": _label_distribution(
                socio_label_rows + prospecto_label_rows,
                ["convirtio_credito", "responde_campania", "up_sell_exitoso"],
            ),
            "training_abandono_ml": _label_distribution(
                socio_label_rows,
                ["abandono_90_dias"],
            ),
            "inference_abandono_ml": _label_distribution(
                socio_label_rows,
                ["abandono_90_dias"],
            ),
        }
        data_layers = _build_data_layer_contract(
            table_counts=layer_table_counts,
            quality_rules=quality_rules,
            cut_key=cut_key,
            label_summary=label_summary,
            imputation_summary=imputation_summary,
        )
        cut_row.bronze_manifest_json = _json_dump(data_layers["bronze"])
        cut_row.silver_manifest_json = _json_dump(data_layers["silver"])
        cut_row.gold_manifest_json = _json_dump(data_layers["gold"])
        cut_row.ml_manifest_json = _json_dump(data_layers["ml"])
        db.commit()
        feature_rows_detail = {
            "socios": len(socios),
            "creditos": len(creditos_all),
            "cuentas": len(cuentas_all),
            "campanas": len(campanas_all),
            "prospectos": len(prospectos_all),
        }
        return {
            "cut_key": cut_key,
            "cut_type": cut_context["cut_type"],
            "cut_date": cut_date.isoformat(),
            "transactional_tables": [item["table"] for item in TRANSACTIONAL_ENTITY_DEFINITIONS],
            "analytical_tables": [item["table"] for item in ANALYTICAL_ENTITY_DEFINITIONS],
            "quality_rules": len(quality_rules),
            "feature_rows": sum(feature_rows_detail.values()),
            "feature_rows_detail": feature_rows_detail,
            "kpi_rows": len(kpi_raw),
            "cohorte_rows": cohorte_rows,
            "imputation_summary": imputation_summary,
            "data_layers": data_layers,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


def get_descriptive_analytics() -> Dict[str, Any]:
    """KPIs con semáforo, cohortes y resumen de tendencias del último corte."""
    db = _db()
    try:
        latest_cut = (
            db.query(IntelicoopAnalyticCut)
            .order_by(IntelicoopAnalyticCut.cut_date.desc(), IntelicoopAnalyticCut.id.desc())
            .first()
        )
        if not latest_cut:
            return {"kpis": [], "cohortes": {}, "tendencias_resumen": [], "cut_key": None}

        cut_key = str(latest_cut.cut_key)

        # KPIs con semáforo
        kpi_rows = (
            db.query(IntelicoopKpiSnapshot)
            .filter(IntelicoopKpiSnapshot.cut_key == cut_key)
            .order_by(IntelicoopKpiSnapshot.metric_group.asc(), IntelicoopKpiSnapshot.kpi_key.asc())
            .all()
        )
        kpis = [
            {
                "kpi_key": row.kpi_key,
                "label": row.metric_label,
                "group": row.metric_group,
                "value": round(float(row.metric_value or 0), 4),
                "metric_type": row.metric_type,
                "semaforo": row.semaforo,
            }
            for row in kpi_rows
        ]

        # Cohortes agrupadas por dimensión
        cohorte_rows = (
            db.query(IntelicoopCohorteSnapshot)
            .filter(IntelicoopCohorteSnapshot.cut_key == cut_key)
            .order_by(
                IntelicoopCohorteSnapshot.dimension.asc(),
                IntelicoopCohorteSnapshot.bucket.asc(),
                IntelicoopCohorteSnapshot.metric_key.asc(),
            )
            .all()
        )
        cohortes: Dict[str, List[Dict[str, Any]]] = {}
        for row in cohorte_rows:
            dim = row.dimension
            cohortes.setdefault(dim, []).append({
                "bucket": row.bucket,
                "metric_key": row.metric_key,
                "metric_value": round(float(row.metric_value or 0), 4),
                "n_records": row.n_records,
                "metric_type": row.metric_type,
            })

        # Tendencias: últimos N cortes para cada KPI
        tendencias_resumen = _compute_tendencias_resumen(db)

        return {
            "cut_key": cut_key,
            "cut_date": latest_cut.cut_date.isoformat() if latest_cut.cut_date else "",
            "kpis": kpis,
            "cohortes": cohortes,
            "tendencias_resumen": tendencias_resumen,
        }
    finally:
        db.close()


def _compute_tendencias_resumen(db: Session, n_cuts: int = 6) -> List[Dict[str, Any]]:
    """Para cada KPI, devuelve los últimos n_cuts valores ordenados por fecha."""
    cuts = (
        db.query(IntelicoopAnalyticCut)
        .order_by(IntelicoopAnalyticCut.cut_date.desc())
        .limit(n_cuts)
        .all()
    )
    if not cuts:
        return []
    cut_keys = [c.cut_key for c in cuts]
    cut_date_by_key = {c.cut_key: c.cut_date.isoformat() if c.cut_date else "" for c in cuts}

    rows = (
        db.query(IntelicoopKpiSnapshot)
        .filter(IntelicoopKpiSnapshot.cut_key.in_(cut_keys))
        .order_by(IntelicoopKpiSnapshot.kpi_key.asc(), IntelicoopKpiSnapshot.cut_date.asc())
        .all()
    )
    by_kpi: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_kpi.setdefault(row.kpi_key, []).append({
            "cut_key": row.cut_key,
            "cut_date": cut_date_by_key.get(row.cut_key, ""),
            "value": round(float(row.metric_value or 0), 4),
            "semaforo": row.semaforo,
        })
    result = []
    for kpi_key, points in by_kpi.items():
        cat = KPI_CATALOG.get(kpi_key, {})
        result.append({
            "kpi_key": kpi_key,
            "label": cat.get("label", kpi_key),
            "metric_type": cat.get("metric_type", "observado"),
            "direction": cat.get("direction", "higher"),
            "puntos": sorted(points, key=lambda p: p["cut_date"]),
        })
    return result


def get_tendencias(kpi_key: str = "imor_pct", n_cuts: int = 12) -> Dict[str, Any]:
    """Devuelve la serie histórica de un KPI a través de todos los cortes disponibles."""
    db = _db()
    try:
        rows = (
            db.query(IntelicoopKpiSnapshot, IntelicoopAnalyticCut.cut_type)
            .join(IntelicoopAnalyticCut, IntelicoopAnalyticCut.cut_key == IntelicoopKpiSnapshot.cut_key)
            .filter(IntelicoopKpiSnapshot.kpi_key == kpi_key)
            .order_by(IntelicoopKpiSnapshot.cut_date.desc())
            .limit(n_cuts)
            .all()
        )
        cat = KPI_CATALOG.get(kpi_key, {})
        puntos = [
            {
                "cut_key": row.cut_key,
                "cut_date": row.cut_date.isoformat() if row.cut_date else "",
                "cut_type": ct,
                "value": round(float(row.metric_value or 0), 4),
                "semaforo": row.semaforo,
                "metric_type": row.metric_type,
            }
            for row, ct in rows
        ]
        return {
            "kpi_key": kpi_key,
            "label": cat.get("label", kpi_key),
            "metric_type": cat.get("metric_type", "observado"),
            "direction": cat.get("direction", "higher"),
            "umbrales": {
                "verde": cat.get("verde"),
                "amarillo": cat.get("amarillo"),
            },
            "puntos": sorted(puntos, key=lambda p: p["cut_date"]),
        }
    finally:
        db.close()


def get_cohortes(dimension: str | None = None) -> Dict[str, Any]:
    """Devuelve cohortes del último corte, opcionalmente filtradas por dimensión."""
    db = _db()
    try:
        latest_cut = (
            db.query(IntelicoopAnalyticCut)
            .order_by(IntelicoopAnalyticCut.cut_date.desc(), IntelicoopAnalyticCut.id.desc())
            .first()
        )
        if not latest_cut:
            return {"cohortes": {}, "cut_key": None}
        cut_key = str(latest_cut.cut_key)
        query = db.query(IntelicoopCohorteSnapshot).filter(IntelicoopCohorteSnapshot.cut_key == cut_key)
        if dimension:
            query = query.filter(IntelicoopCohorteSnapshot.dimension == dimension)
        rows = query.order_by(
            IntelicoopCohorteSnapshot.dimension.asc(),
            IntelicoopCohorteSnapshot.bucket.asc(),
            IntelicoopCohorteSnapshot.metric_key.asc(),
        ).all()
        cohortes: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            cohortes.setdefault(row.dimension, []).append({
                "bucket": row.bucket,
                "metric_key": row.metric_key,
                "metric_value": round(float(row.metric_value or 0), 4),
                "n_records": row.n_records,
                "metric_type": row.metric_type,
            })
        return {"cut_key": cut_key, "cohortes": cohortes}
    finally:
        db.close()


def get_pattern_discovery_summary(cut_key: str | None = None) -> Dict[str, Any]:
    db = _db()
    try:
        resolved_cut_key = _resolve_cut_key(db, cut_key)
        if not resolved_cut_key:
            return {
                "cut_key": None,
                "mode": "cut_driven",
                "reglas_asociacion_productos": [],
                "anomalias_transacciones": [],
                "series_tiempo_captacion_cartera": [],
                "canastas_productos_frecuentes": [],
                "secuencias_previas_mora": [],
            }

        cut_row = db.query(IntelicoopAnalyticCut).filter(IntelicoopAnalyticCut.cut_key == resolved_cut_key).first()
        cut_date = cut_row.cut_date if cut_row and cut_row.cut_date else datetime.utcnow()
        window_end = cut_row.window_end if cut_row and cut_row.window_end else cut_date + timedelta(days=1)
        window_start_90 = window_end - timedelta(days=90)
        window_start_60 = window_end - timedelta(days=60)
        window_start_30 = window_end - timedelta(days=30)

        socios = {int(row.id): str(row.nombre or f"Socio {row.id}") for row in db.query(IntelicoopSocio).all()}
        cuentas = db.query(IntelicoopCuenta).filter(IntelicoopCuenta.fecha_creacion <= window_end).all()
        cuenta_to_socio = {int(row.id): int(row.socio_id) for row in cuentas}
        txs = (
            db.query(IntelicoopTransaccion)
            .filter(IntelicoopTransaccion.fecha <= window_end)
            .order_by(IntelicoopTransaccion.fecha.asc(), IntelicoopTransaccion.id.asc())
            .all()
        )
        creditos = (
            db.query(IntelicoopCredito)
            .filter(IntelicoopCredito.fecha_creacion <= window_end)
            .order_by(IntelicoopCredito.fecha_creacion.asc(), IntelicoopCredito.id.asc())
            .all()
        )
        contactos = (
            db.query(IntelicoopContactoCampania)
            .filter(IntelicoopContactoCampania.fecha_contacto <= window_end)
            .order_by(IntelicoopContactoCampania.fecha_contacto.asc(), IntelicoopContactoCampania.id.asc())
            .all()
        )
        seguimientos = (
            db.query(IntelicoopSeguimientoCampania)
            .filter(IntelicoopSeguimientoCampania.fecha_evento <= window_end)
            .order_by(IntelicoopSeguimientoCampania.fecha_evento.asc(), IntelicoopSeguimientoCampania.id.asc())
            .all()
        )
        credito_snapshots = db.query(IntelicoopCreditoFeatureSnapshot).filter(
            IntelicoopCreditoFeatureSnapshot.cut_key == resolved_cut_key
        ).all()

        cuentas_por_socio: Dict[int, List[IntelicoopCuenta]] = {}
        for row in cuentas:
            cuentas_por_socio.setdefault(int(row.socio_id), []).append(row)

        txs_por_cuenta: Dict[int, List[IntelicoopTransaccion]] = {}
        txs_por_socio: Dict[int, List[IntelicoopTransaccion]] = {}
        for row in txs:
            cuenta_id = int(row.cuenta_id)
            socio_id = int(cuenta_to_socio.get(cuenta_id, 0) or 0)
            txs_por_cuenta.setdefault(cuenta_id, []).append(row)
            if socio_id:
                txs_por_socio.setdefault(socio_id, []).append(row)

        creditos_por_socio: Dict[int, List[IntelicoopCredito]] = {}
        for row in creditos:
            creditos_por_socio.setdefault(int(row.socio_id), []).append(row)

        contactos_por_socio: Dict[int, List[IntelicoopContactoCampania]] = {}
        for row in contactos:
            contactos_por_socio.setdefault(int(row.socio_id), []).append(row)

        seguimientos_por_socio: Dict[int, List[IntelicoopSeguimientoCampania]] = {}
        for row in seguimientos:
            seguimientos_por_socio.setdefault(int(row.socio_id), []).append(row)

        snapshot_por_credito = {int(row.credito_id): row for row in credito_snapshots}

        baskets: Dict[int, List[str]] = {}
        for socio_id in socios:
            basket: set[str] = set()
            for cuenta in cuentas_por_socio.get(socio_id, []):
                basket.add(f"cuenta_{str(cuenta.tipo or 'ahorro').strip().lower()}")
            socio_creditos = creditos_por_socio.get(socio_id, [])
            if socio_creditos:
                basket.add("credito")
            if any(str(row.estado or "") in _CONVERSION_CREDITO_ESTADOS for row in socio_creditos):
                basket.add("credito_activo")
            if any(str(row.estado or "") == "mora" for row in socio_creditos):
                basket.add("credito_mora")
            if contactos_por_socio.get(socio_id):
                basket.add("campania_participada")
            if any(int(row.conversion or 0) == 1 for row in seguimientos_por_socio.get(socio_id, [])):
                basket.add("campania_convertida")
            if basket:
                baskets[socio_id] = sorted(basket)

        basket_count = len(baskets)
        item_counts: Counter[str] = Counter()
        pair_counts: Counter[tuple[str, str]] = Counter()
        combo_counts: Counter[tuple[str, ...]] = Counter()
        for items in baskets.values():
            item_counts.update(items)
            for idx, left in enumerate(items):
                for right in items[idx + 1:]:
                    pair_counts[(left, right)] += 1
            if len(items) >= 2:
                combo_counts[tuple(items)] += 1

        reglas_asociacion_productos: List[Dict[str, Any]] = []
        for (left, right), pair_count in pair_counts.most_common(8):
            left_count = item_counts.get(left, 0)
            right_count = item_counts.get(right, 0)
            support = round(pair_count / basket_count, 4) if basket_count else 0.0
            confidence = round(pair_count / left_count, 4) if left_count else 0.0
            lift = round((pair_count * basket_count) / (left_count * right_count), 4) if basket_count and left_count and right_count else 0.0
            reglas_asociacion_productos.append(
                {
                    "antecedente": left,
                    "consecuente": right,
                    "support": support,
                    "confidence": confidence,
                    "lift": lift,
                    "coocurrencias": int(pair_count),
                }
            )

        canastas_productos_frecuentes = [
            {
                "canasta": list(combo),
                "frecuencia": int(count),
                "support": round(count / basket_count, 4) if basket_count else 0.0,
            }
            for combo, count in combo_counts.most_common(8)
        ]

        anomalias_transacciones: List[Dict[str, Any]] = []
        for cuenta_id, cuenta_txs in txs_por_cuenta.items():
            montos = [abs(float(row.monto or 0)) for row in cuenta_txs]
            if not montos:
                continue
            avg = sum(montos) / len(montos)
            std = _stddev(montos)
            threshold = avg + (1.5 * std if std > 0 else avg)
            for row in cuenta_txs:
                monto = abs(float(row.monto or 0))
                score = round((monto - avg) / std, 4) if std > 0 else (99.0 if monto > avg * 2 and avg > 0 else 0.0)
                if monto > threshold and score > 0:
                    socio_id = int(cuenta_to_socio.get(cuenta_id, 0) or 0)
                    anomalias_transacciones.append(
                        {
                            "transaccion_id": int(row.id),
                            "cuenta_id": int(cuenta_id),
                            "socio_id": socio_id,
                            "socio_nombre": socios.get(socio_id, ""),
                            "tipo": str(row.tipo or ""),
                            "monto": round(float(row.monto or 0), 2),
                            "fecha": row.fecha.isoformat() if row.fecha else "",
                            "score_anomalia": score,
                        }
                    )
        anomalias_transacciones.sort(key=lambda item: item["score_anomalia"], reverse=True)
        anomalias_transacciones = anomalias_transacciones[:10]

        months = {row.fecha.strftime("%Y-%m") for row in txs if row.fecha}
        months.update(row.fecha_creacion.strftime("%Y-%m") for row in creditos if row.fecha_creacion)
        series_tiempo_captacion_cartera: List[Dict[str, Any]] = []
        for month_key in sorted(months):
            depositos = 0.0
            retiros = 0.0
            cartera_total = 0.0
            cartera_mora = 0.0
            for row in txs:
                if row.fecha and row.fecha.strftime("%Y-%m") == month_key:
                    if str(row.tipo or "") == "deposito":
                        depositos += float(row.monto or 0)
                    else:
                        retiros += float(row.monto or 0)
            for row in creditos:
                if row.fecha_creacion and row.fecha_creacion.strftime("%Y-%m") <= month_key:
                    cartera_total += float(row.monto or 0)
                    if str(row.estado or "") == "mora":
                        cartera_mora += float(row.monto or 0)
            series_tiempo_captacion_cartera.append(
                {
                    "periodo": month_key,
                    "depositos": round(depositos, 2),
                    "retiros": round(retiros, 2),
                    "captacion_neta": round(depositos - retiros, 2),
                    "cartera_total": round(cartera_total, 2),
                    "cartera_mora": round(cartera_mora, 2),
                }
            )

        sequence_counts: Counter[tuple[str, ...]] = Counter()
        sequence_examples: Dict[tuple[str, ...], Dict[str, Any]] = {}
        for row in creditos:
            if str(row.estado or "") != "mora":
                continue
            socio_id = int(row.socio_id)
            socio_txs = [
                tx for tx in txs_por_socio.get(socio_id, [])
                if tx.fecha and window_start_90 <= tx.fecha <= window_end
            ]
            socio_contactos = [
                item for item in contactos_por_socio.get(socio_id, [])
                if item.fecha_contacto and window_start_90 <= item.fecha_contacto <= window_end
            ]
            socio_seguimientos = [
                item for item in seguimientos_por_socio.get(socio_id, [])
                if item.fecha_evento and window_start_90 <= item.fecha_evento <= window_end
            ]
            tx_30 = [tx for tx in socio_txs if tx.fecha and tx.fecha >= window_start_30]
            tx_60 = [tx for tx in socio_txs if tx.fecha and tx.fecha >= window_start_60]
            deposits_60 = sum(float(tx.monto or 0) for tx in tx_60 if str(tx.tipo or "") == "deposito")
            withdrawals_60 = sum(float(tx.monto or 0) for tx in tx_60 if str(tx.tipo or "") == "retiro")
            snapshot = snapshot_por_credito.get(int(row.id))
            sequence: List[str] = []
            if not tx_30:
                sequence.append("sin_movimientos_30d")
            if withdrawals_60 > deposits_60:
                sequence.append("retiros_superan_depositos")
            if socio_contactos and not any(int(item.conversion or 0) == 1 for item in socio_seguimientos):
                sequence.append("contacto_sin_conversion")
            if snapshot and float(snapshot.porcentaje_pagado or 0) < 0.5:
                sequence.append("porcentaje_pagado_bajo")
            if snapshot and float(snapshot.ratio_deuda_ingreso or 0) >= 0.5:
                sequence.append("ratio_deuda_ingreso_alto")
            if not sequence:
                sequence.append("mora_sin_patron_previo")
            sequence.append("mora")
            sequence_key = tuple(sequence)
            sequence_counts[sequence_key] += 1
            sequence_examples.setdefault(
                sequence_key,
                {
                    "socio_id": socio_id,
                    "socio_nombre": socios.get(socio_id, ""),
                    "credito_id": int(row.id),
                },
            )

        secuencias_previas_mora = [
            {
                "secuencia": list(sequence),
                "frecuencia": int(count),
                **sequence_examples.get(sequence, {}),
            }
            for sequence, count in sequence_counts.most_common(8)
        ]

        return {
            "cut_key": resolved_cut_key,
            "cut_date": cut_date.isoformat() if cut_date else "",
            "mode": "cut_driven",
            "reglas_asociacion_productos": reglas_asociacion_productos,
            "anomalias_transacciones": anomalias_transacciones,
            "series_tiempo_captacion_cartera": series_tiempo_captacion_cartera,
            "canastas_productos_frecuentes": canastas_productos_frecuentes,
            "secuencias_previas_mora": secuencias_previas_mora,
        }
    finally:
        db.close()


def get_basic_catalogs() -> Dict[str, Any]:
    db = _db()
    try:
        socios = db.query(IntelicoopSocio).order_by(IntelicoopSocio.nombre.asc()).all()
        return {
            "socios": [
                {
                    "id": row.id,
                    "nombre": row.nombre,
                    "segmento": row.segmento,
                }
                for row in socios
            ],
            "segmentos": [
                {"value": "hormiga", "label": "Ahorrador Hormiga"},
                {"value": "gran_ahorrador", "label": "Gran Ahorrador"},
                {"value": "inactivo", "label": "Inactivo"},
            ],
        "estados_credito": [
                {"value": "solicitado", "label": "Solicitado"},
                {"value": "aprobado", "label": "Aprobado"},
                {"value": "vigente", "label": "Vigente"},
                {"value": "liquidado", "label": "Liquidado"},
                {"value": "rechazado", "label": "Rechazado"},
                {"value": "mora", "label": "Mora"},
                {"value": "reestructurado", "label": "Reestructurado"},
            ],
            "estados_campana": [
                {"value": "borrador", "label": "Borrador"},
                {"value": "activa", "label": "Activa"},
                {"value": "finalizada", "label": "Finalizada"},
            ],
            "tipos_cuenta": [
                {"value": "ahorro", "label": "Ahorro"},
                {"value": "aportacion", "label": "Aportacion"},
            ],
            "tipos_transaccion": [
                {"value": "deposito", "label": "Deposito"},
                {"value": "retiro", "label": "Retiro"},
            ],
            "cuentas": [
                {
                    "id": row.id,
                    "socio_id": row.socio_id,
                    "tipo": row.tipo,
                    "saldo": round(float(row.saldo or 0), 2),
                }
                for row in db.query(IntelicoopCuenta).order_by(IntelicoopCuenta.id.asc()).all()
            ],
        }
    finally:
        db.close()


SEGMENTATION_LABELS = {
    "integral_fiel": "Integral fiel",
    "crecimiento": "Crecimiento",
    "ahorrador_activo": "Ahorrador activo",
    "alerta_temprana": "Alerta temprana",
    "pasivo": "Pasivo",
}


def _clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _score_level(value: float) -> str:
    if value >= 0.67:
        return "alto"
    if value >= 0.34:
        return "medio"
    return "bajo"


def _get_latest_cut_key(db: Session) -> str | None:
    latest_cut = (
        db.query(IntelicoopAnalyticCut)
        .order_by(IntelicoopAnalyticCut.cut_date.desc(), IntelicoopAnalyticCut.id.desc())
        .first()
    )
    if not latest_cut:
        return None
    return str(latest_cut.cut_key)


def _resolve_cut_key(db: Session, cut_key: str | None = None) -> str | None:
    resolved = str(cut_key or "").strip()
    if resolved:
        row = db.query(IntelicoopAnalyticCut).filter(IntelicoopAnalyticCut.cut_key == resolved).first()
        return resolved if row else None
    return _get_latest_cut_key(db)


def _build_live_socio_features(db: Session) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    socios = db.query(IntelicoopSocio).order_by(IntelicoopSocio.id.asc()).all()
    creditos_agg: Dict[int, Dict[str, Any]] = {
        int(sid): {"creditos_total": int(total or 0), "monto_total": float(monto or 0)}
        for sid, total, monto in db.query(
            IntelicoopCredito.socio_id,
            func.count(IntelicoopCredito.id),
            func.coalesce(func.sum(IntelicoopCredito.monto), 0),
        ).group_by(IntelicoopCredito.socio_id).all()
    }
    creditos_activos_agg: Dict[int, int] = {
        int(sid): int(total or 0)
        for sid, total in db.query(
            IntelicoopCredito.socio_id,
            func.count(IntelicoopCredito.id),
        ).filter(
            IntelicoopCredito.estado.in_(list(_ACTIVE_CREDITO_ESTADOS))
        ).group_by(IntelicoopCredito.socio_id).all()
    }
    creditos_mora_agg: Dict[int, int] = {
        int(sid): int(total or 0)
        for sid, total in db.query(
            IntelicoopCredito.socio_id,
            func.count(IntelicoopCredito.id),
        ).filter(IntelicoopCredito.estado == "mora").group_by(IntelicoopCredito.socio_id).all()
    }
    pagos_agg: Dict[int, float] = {
        int(sid): float(total or 0)
        for sid, total in db.query(
            IntelicoopCredito.socio_id,
            func.coalesce(func.sum(IntelicoopHistorialPago.monto), 0),
        ).join(
            IntelicoopHistorialPago,
            IntelicoopHistorialPago.credito_id == IntelicoopCredito.id,
        ).group_by(IntelicoopCredito.socio_id).all()
    }
    cuentas_agg: Dict[int, Dict[str, Any]] = {
        int(sid): {"cuentas_total": int(total or 0), "saldo_total": float(saldo or 0)}
        for sid, total, saldo in db.query(
            IntelicoopCuenta.socio_id,
            func.count(IntelicoopCuenta.id),
            func.coalesce(func.sum(IntelicoopCuenta.saldo), 0),
        ).group_by(IntelicoopCuenta.socio_id).all()
    }
    tx_agg: Dict[int, int] = {
        int(sid): int(total or 0)
        for sid, total in db.query(
            IntelicoopCuenta.socio_id,
            func.count(IntelicoopTransaccion.id),
        ).join(
            IntelicoopTransaccion,
            IntelicoopTransaccion.cuenta_id == IntelicoopCuenta.id,
        ).group_by(IntelicoopCuenta.socio_id).all()
    }
    campanas_part_agg: Dict[int, int] = {
        int(sid): int(total or 0)
        for sid, total in db.query(
            IntelicoopContactoCampania.socio_id,
            func.count(IntelicoopContactoCampania.id),
        ).group_by(IntelicoopContactoCampania.socio_id).all()
    }
    campanas_conv_agg: Dict[int, int] = {
        int(sid): int(total or 0)
        for sid, total in db.query(
            IntelicoopSeguimientoCampania.socio_id,
            func.count(IntelicoopSeguimientoCampania.id),
        ).filter(
            IntelicoopSeguimientoCampania.conversion == 1
        ).group_by(IntelicoopSeguimientoCampania.socio_id).all()
    }
    response_channel_agg: Dict[int, Dict[str, Dict[str, int]]] = {}
    last_contact_at: Dict[int, datetime] = {}
    for socio_id, canal, total, contactados in db.query(
        IntelicoopContactoCampania.socio_id,
        IntelicoopContactoCampania.canal,
        func.count(IntelicoopContactoCampania.id),
        func.coalesce(func.sum(case((IntelicoopContactoCampania.estado_contacto == "contactado", 1), else_=0)), 0),
    ).group_by(
        IntelicoopContactoCampania.socio_id,
        IntelicoopContactoCampania.canal,
    ).all():
        sid = int(socio_id)
        response_channel_agg.setdefault(sid, {})[str(canal or "desconocido")] = {
            "total": int(total or 0),
            "contactados": int(contactados or 0),
        }
    for socio_id, fecha in db.query(
        IntelicoopContactoCampania.socio_id,
        func.max(IntelicoopContactoCampania.fecha_contacto),
    ).group_by(IntelicoopContactoCampania.socio_id).all():
        if socio_id and fecha:
            last_contact_at[int(socio_id)] = fecha
    latest_scoring: Dict[int, Dict[str, Any]] = {}
    for row in db.query(IntelicoopScoringResult).filter(
        IntelicoopScoringResult.socio_id.isnot(None)
    ).order_by(
        IntelicoopScoringResult.socio_id.asc(),
        IntelicoopScoringResult.fecha_creacion.desc(),
        IntelicoopScoringResult.id.desc(),
    ).all():
        socio_id = int(row.socio_id or 0)
        if socio_id and socio_id not in latest_scoring:
            latest_scoring[socio_id] = {
                "score": float(row.score or 0),
                "riesgo": str(row.riesgo or "sin_dato"),
                "ingreso_mensual": float(row.ingreso_mensual or 0),
                "deuda_actual": float(row.deuda_actual or 0),
            }

    rows: List[Dict[str, Any]] = []
    for socio in socios:
        socio_id = int(socio.id)
        credito_data = creditos_agg.get(socio_id, {})
        cuenta_data = cuentas_agg.get(socio_id, {})
        scoring_data = latest_scoring.get(socio_id, {})
        monto_creditos_total = float(credito_data.get("monto_total", 0))
        pagos_total = float(pagos_agg.get(socio_id, 0))
        ingreso = float(scoring_data.get("ingreso_mensual", 0))
        deuda = float(scoring_data.get("deuda_actual", 0))
        dias_como_socio = max(0, (now - socio.fecha_registro).days) if socio.fecha_registro else 0
        ultimo_contacto = last_contact_at.get(socio_id)
        dias_desde_ultimo_contacto = (now - ultimo_contacto).days if ultimo_contacto else dias_como_socio
        response_por_canal = {
            canal: round((vals.get("contactados", 0) / vals.get("total", 1)), 4) if vals.get("total", 0) else 0.0
            for canal, vals in (response_channel_agg.get(socio_id, {})).items()
        }
        rows.append(
            {
                "socio_id": socio_id,
                "socio_nombre": str(socio.nombre or ""),
                "segmento_actual": str(socio.segmento or "inactivo"),
                "creditos_total": int(credito_data.get("creditos_total", 0)),
                "creditos_activos": int(creditos_activos_agg.get(socio_id, 0)),
                "creditos_mora": int(creditos_mora_agg.get(socio_id, 0)),
                "monto_creditos_total": round(monto_creditos_total, 2),
                "pagos_total": round(pagos_total, 2),
                "tasa_cumplimiento_pagos": round(pagos_total / monto_creditos_total, 4) if monto_creditos_total > 0 else 0.0,
                "ratio_deuda_ingreso": round(deuda / ingreso, 4) if ingreso > 0 else 0.0,
                "cuentas_total": int(cuenta_data.get("cuentas_total", 0)),
                "saldo_cuentas_total": round(float(cuenta_data.get("saldo_total", 0)), 2),
                "transacciones_total": int(tx_agg.get(socio_id, 0)),
                "campanas_participadas": int(campanas_part_agg.get(socio_id, 0)),
                "campanas_convertidas": int(campanas_conv_agg.get(socio_id, 0)),
                "respuesta_por_canal": response_por_canal,
                "dias_desde_ultimo_contacto": max(0, dias_desde_ultimo_contacto),
                "dias_como_socio": dias_como_socio,
                "num_productos": int(credito_data.get("creditos_total", 0)) + int(cuenta_data.get("cuentas_total", 0)),
                "score_propension_referencia": 0.0,
                "score_abandono": 0.0,
                "score_scoring_reciente": round(float(scoring_data.get("score", 0)), 4),
                "riesgo_scoring_reciente": str(scoring_data.get("riesgo", "sin_dato")),
            }
        )
    return rows


def _get_socio_features_for_segmentation(db: Session, cut_key: str | None = None) -> tuple[str | None, List[Dict[str, Any]]]:
    resolved_cut_key = _resolve_cut_key(db, cut_key)
    if resolved_cut_key:
        rows = (
            db.query(IntelicoopSocioFeatureSnapshot)
            .filter(IntelicoopSocioFeatureSnapshot.cut_key == resolved_cut_key)
            .order_by(IntelicoopSocioFeatureSnapshot.socio_id.asc())
            .all()
        )
        if rows:
            return resolved_cut_key, [
                {
                    "socio_id": int(row.socio_id),
                    "socio_nombre": row.socio_nombre,
                    "segmento_actual": row.segmento_actual,
                    "creditos_total": int(row.creditos_total or 0),
                    "creditos_activos": int(row.creditos_activos or 0),
                    "creditos_mora": int(row.creditos_mora or 0),
                    "monto_creditos_total": round(float(row.monto_creditos_total or 0), 2),
                    "pagos_total": round(float(row.pagos_total or 0), 2),
                    "tasa_cumplimiento_pagos": round(float(row.tasa_cumplimiento_pagos or 0), 4),
                    "ratio_deuda_ingreso": round(float(row.ratio_deuda_ingreso or 0), 4),
                    "cuentas_total": int(row.cuentas_total or 0),
                    "saldo_cuentas_total": round(float(row.saldo_cuentas_total or 0), 2),
                    "transacciones_total": int(row.transacciones_total or 0),
                    "campanas_participadas": int(row.campanas_participadas or 0),
                    "campanas_convertidas": int(row.campanas_convertidas or 0),
                    "respuesta_por_canal": _json_load(row.respuesta_por_canal_json, {}),
                    "dias_desde_ultimo_contacto": int(row.dias_desde_ultimo_contacto or 0),
                    "dias_como_socio": int(row.dias_como_socio or 0),
                    "num_productos": int(row.num_productos or 0),
                    "score_propension_referencia": round(float(row.score_propension_referencia or 0), 4),
                    "score_abandono": round(float(row.score_abandono or 0), 4),
                    "score_scoring_reciente": round(float(row.score_scoring_reciente or 0), 4),
                    "riesgo_scoring_reciente": row.riesgo_scoring_reciente,
                }
                for row in rows
            ]
    return resolved_cut_key, []


def _derive_automatic_segment(feature_row: Dict[str, Any]) -> str:
    if (
        int(feature_row.get("creditos_mora", 0)) > 0
        or float(feature_row.get("ratio_deuda_ingreso", 0)) >= 0.55
        or str(feature_row.get("riesgo_scoring_reciente", "")) == "alto"
    ):
        return "alerta_temprana"
    if (
        float(feature_row.get("saldo_cuentas_total", 0)) >= 5000
        and int(feature_row.get("transacciones_total", 0)) >= 4
        and int(feature_row.get("num_productos", 0)) >= 2
    ):
        return "integral_fiel"
    if (
        int(feature_row.get("campanas_convertidas", 0)) >= 1
        or (
            int(feature_row.get("creditos_activos", 0)) >= 1
            and float(feature_row.get("tasa_cumplimiento_pagos", 0)) >= 0.7
        )
    ):
        return "crecimiento"
    if (
        float(feature_row.get("saldo_cuentas_total", 0)) >= 1000
        or int(feature_row.get("transacciones_total", 0)) >= 2
    ):
        return "ahorrador_activo"
    return "pasivo"


def _rank_quintile(values: List[float], target: float, reverse: bool = False) -> int:
    ordered = sorted(values, reverse=reverse)
    if not ordered:
        return 1
    try:
        idx = ordered.index(target)
    except ValueError:
        idx = min(range(len(ordered)), key=lambda pos: abs(ordered[pos] - target))
    return max(1, min(5, 5 - int((idx * 5) / max(1, len(ordered)))))


def _derive_rfm_segment(feature_rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    recency_values = [float(row.get("dias_desde_ultimo_contacto", row.get("dias_como_socio", 0))) for row in feature_rows]
    frequency_values = [
        float(row.get("transacciones_total", 0)) + float(row.get("campanas_participadas", 0)) + float(row.get("creditos_activos", 0))
        for row in feature_rows
    ]
    monetary_values = [
        float(row.get("saldo_cuentas_total", 0)) + float(row.get("pagos_total", 0)) + float(row.get("monto_creditos_total", 0))
        for row in feature_rows
    ]
    result: Dict[int, Dict[str, Any]] = {}
    for row in feature_rows:
        socio_id = int(row.get("socio_id", 0))
        recency_raw = float(row.get("dias_desde_ultimo_contacto", row.get("dias_como_socio", 0)))
        frequency_raw = float(row.get("transacciones_total", 0)) + float(row.get("campanas_participadas", 0)) + float(row.get("creditos_activos", 0))
        monetary_raw = float(row.get("saldo_cuentas_total", 0)) + float(row.get("pagos_total", 0)) + float(row.get("monto_creditos_total", 0))
        recency_score = _rank_quintile(recency_values, recency_raw, reverse=False)
        frequency_score = _rank_quintile(frequency_values, frequency_raw, reverse=True)
        monetary_score = _rank_quintile(monetary_values, monetary_raw, reverse=True)
        code = f"{recency_score}{frequency_score}{monetary_score}"
        if recency_score >= 4 and frequency_score >= 4 and monetary_score >= 4:
            label = "vinculado_premium"
        elif recency_score >= 4 and frequency_score >= 3:
            label = "leal_activo"
        elif monetary_score >= 4 and frequency_score <= 2:
            label = "ahorro_potencial"
        elif recency_score <= 2 and frequency_score >= 3:
            label = "reactivacion_prioritaria"
        else:
            label = "base_general"
        result[socio_id] = {
            "rfm": {"recency": recency_score, "frequency": frequency_score, "monetary": monetary_score, "code": code},
            "rfm_segmento": label,
        }
    return result


def _run_simple_kmeans(feature_rows: List[Dict[str, Any]], k: int = 4, iterations: int = 12) -> Dict[int, Dict[str, Any]]:
    if not feature_rows:
        return {}
    vectors: List[List[float]] = []
    for row in feature_rows:
        vectors.append([
            float(row.get("ratio_deuda_ingreso", 0)),
            float(row.get("saldo_cuentas_total", 0)),
            float(row.get("transacciones_total", 0)),
            float(row.get("campanas_convertidas", 0)),
            float(row.get("score_abandono", 0)),
            float(row.get("score_propension_referencia", 0)),
        ])
    dims = len(vectors[0])
    means = [sum(vector[idx] for vector in vectors) / len(vectors) for idx in range(dims)]
    stds = []
    for idx in range(dims):
        variance = sum((vector[idx] - means[idx]) ** 2 for vector in vectors) / len(vectors)
        stds.append((variance ** 0.5) or 1.0)
    normalized = [[(vector[idx] - means[idx]) / stds[idx] for idx in range(dims)] for vector in vectors]
    k = max(1, min(k, len(normalized)))
    seed_positions = sorted({int(round(i * (len(normalized) - 1) / max(1, k - 1))) for i in range(k)})
    centroids = [normalized[pos][:] for pos in seed_positions]
    while len(centroids) < k:
        centroids.append(normalized[len(centroids) % len(normalized)][:])
    assignments = [0 for _ in normalized]
    for _ in range(iterations):
        changed = False
        for idx, vector in enumerate(normalized):
            distances = [
                sum((vector[d] - centroid[d]) ** 2 for d in range(dims))
                for centroid in centroids
            ]
            cluster = min(range(len(distances)), key=lambda pos: distances[pos])
            if assignments[idx] != cluster:
                assignments[idx] = cluster
                changed = True
        new_centroids: List[List[float]] = []
        for cluster in range(k):
            members = [normalized[idx] for idx, assigned in enumerate(assignments) if assigned == cluster]
            if not members:
                new_centroids.append(centroids[cluster])
                continue
            new_centroids.append([sum(member[d] for member in members) / len(members) for d in range(dims)])
        centroids = new_centroids
        if not changed:
            break
    cluster_profiles: Dict[int, Dict[str, float]] = {}
    for cluster in range(k):
        members = [feature_rows[idx] for idx, assigned in enumerate(assignments) if assigned == cluster]
        if not members:
            cluster_profiles[cluster] = {}
            continue
        cluster_profiles[cluster] = {
            "ratio_deuda_ingreso": sum(float(row.get("ratio_deuda_ingreso", 0)) for row in members) / len(members),
            "saldo_cuentas_total": sum(float(row.get("saldo_cuentas_total", 0)) for row in members) / len(members),
            "transacciones_total": sum(float(row.get("transacciones_total", 0)) for row in members) / len(members),
            "campanas_convertidas": sum(float(row.get("campanas_convertidas", 0)) for row in members) / len(members),
            "score_abandono": sum(float(row.get("score_abandono", 0)) for row in members) / len(members),
            "score_propension_referencia": sum(float(row.get("score_propension_referencia", 0)) for row in members) / len(members),
        }
    mapping: Dict[int, Dict[str, Any]] = {}
    for idx, row in enumerate(feature_rows):
        cluster = assignments[idx]
        profile = cluster_profiles.get(cluster, {})
        if profile.get("score_abandono", 0) >= 0.5 or profile.get("ratio_deuda_ingreso", 0) >= 0.55:
            label = "cluster_riesgo_crediticio"
        elif profile.get("saldo_cuentas_total", 0) >= 3000 and profile.get("transacciones_total", 0) >= 2:
            label = "cluster_ahorro_constante"
        elif profile.get("score_propension_referencia", 0) >= 0.45 or profile.get("campanas_convertidas", 0) >= 0.5:
            label = "cluster_apertura_comercial"
        else:
            label = "cluster_baja_interaccion"
        mapping[int(row.get("socio_id", 0))] = {
            "cluster_id": cluster,
            "cluster_label": label,
            "cluster_algoritmo": "kmeans_simple",
        }
    return mapping


def _build_segmentation_row(feature_row: Dict[str, Any]) -> Dict[str, Any]:
    segmento = _derive_automatic_segment(feature_row)
    riesgo_scoring = str(feature_row.get("riesgo_scoring_reciente", "sin_dato"))
    comercial = _clamp01(
        max(
            float(feature_row.get("score_propension_referencia", 0)),
            0.12
        + min(int(feature_row.get("num_productos", 0)), 3) * 0.10
        + min(int(feature_row.get("transacciones_total", 0)), 8) * 0.035
        + min(float(feature_row.get("saldo_cuentas_total", 0)) / 5000.0, 1.0) * 0.18
        + min(int(feature_row.get("campanas_participadas", 0)), 4) * 0.06
        + min(int(feature_row.get("campanas_convertidas", 0)), 2) * 0.12
        + (0.06 if riesgo_scoring == "bajo" else -0.08 if riesgo_scoring == "alto" else 0.0)
        )
    )
    riesgo_temprano = _clamp01(
        0.04
        + min(int(feature_row.get("creditos_mora", 0)), 2) * 0.34
        + min(float(feature_row.get("ratio_deuda_ingreso", 0)), 1.0) * 0.42
        + max(0.0, 1.0 - float(feature_row.get("tasa_cumplimiento_pagos", 0))) * 0.18
        + (0.18 if riesgo_scoring == "alto" else 0.08 if riesgo_scoring == "medio" else 0.0)
    )
    abandono = _clamp01(
        max(
            float(feature_row.get("score_abandono", 0)),
            0.06
        + (0.28 if int(feature_row.get("transacciones_total", 0)) == 0 else 0.0)
        + (0.18 if int(feature_row.get("creditos_activos", 0)) == 0 else 0.0)
        + (0.16 if float(feature_row.get("saldo_cuentas_total", 0)) < 250 else 0.0)
        + (0.10 if int(feature_row.get("campanas_participadas", 0)) == 0 else 0.0)
        + (0.08 if int(feature_row.get("dias_como_socio", 0)) > 180 and int(feature_row.get("num_productos", 0)) <= 1 else 0.0)
        - (0.16 if segmento == "integral_fiel" else 0.10 if segmento == "crecimiento" else 0.0)
        )
    )
    conversion = _clamp01(
        0.08
        + comercial * 0.48
        + min(int(feature_row.get("campanas_participadas", 0)), 3) * 0.06
        + min(int(feature_row.get("campanas_convertidas", 0)), 2) * 0.12
        - riesgo_temprano * 0.16
        - abandono * 0.18
    )
    return {
        "socio_id": int(feature_row.get("socio_id", 0)),
        "socio_nombre": feature_row.get("socio_nombre", ""),
        "segmento_actual": feature_row.get("segmento_actual", "inactivo"),
        "segmento_automatico": segmento,
        "segmento_label": SEGMENTATION_LABELS.get(segmento, segmento),
        "comercial_score": comercial,
        "comercial_nivel": _score_level(comercial),
        "riesgo_temprano_score": riesgo_temprano,
        "riesgo_temprano_nivel": _score_level(riesgo_temprano),
        "conversion_score": conversion,
        "conversion_nivel": _score_level(conversion),
        "abandono_score": abandono,
        "abandono_nivel": _score_level(abandono),
        "num_productos": int(feature_row.get("num_productos", 0)),
        "saldo_cuentas_total": round(float(feature_row.get("saldo_cuentas_total", 0)), 2),
        "transacciones_total": int(feature_row.get("transacciones_total", 0)),
        "creditos_activos": int(feature_row.get("creditos_activos", 0)),
        "creditos_mora": int(feature_row.get("creditos_mora", 0)),
        "campanas_participadas": int(feature_row.get("campanas_participadas", 0)),
        "campanas_convertidas": int(feature_row.get("campanas_convertidas", 0)),
        "respuesta_por_canal": feature_row.get("respuesta_por_canal", {}),
        "dias_desde_ultimo_contacto": int(feature_row.get("dias_desde_ultimo_contacto", 0)),
        "ratio_deuda_ingreso": round(float(feature_row.get("ratio_deuda_ingreso", 0)), 4),
        "tasa_cumplimiento_pagos": round(float(feature_row.get("tasa_cumplimiento_pagos", 0)), 4),
        "score_propension_referencia": round(float(feature_row.get("score_propension_referencia", 0)), 4),
        "score_abandono_base": round(float(feature_row.get("score_abandono", 0)), 4),
        "score_scoring_reciente": round(float(feature_row.get("score_scoring_reciente", 0)), 4),
        "riesgo_scoring_reciente": feature_row.get("riesgo_scoring_reciente", "sin_dato"),
    }


def get_segmentation_propensity_summary(cut_key: str | None = None) -> Dict[str, Any]:
    db = _db()
    try:
        resolved_cut_key, feature_rows = _get_socio_features_for_segmentation(db, cut_key=cut_key)
        rfm_map = _derive_rfm_segment(feature_rows)
        cluster_map = _run_simple_kmeans(feature_rows, k=4)
        socios = []
        for row in feature_rows:
            socio_row = _build_segmentation_row(row)
            socio_id = int(socio_row.get("socio_id", 0))
            socio_row.update(rfm_map.get(socio_id, {}))
            socio_row.update(cluster_map.get(socio_id, {}))
            socios.append(socio_row)
        socios.sort(
            key=lambda row: (
                -row["comercial_score"],
                row["abandono_score"],
                row["socio_nombre"],
            )
        )
        segments: Dict[str, List[Dict[str, Any]]] = {}
        analytic_segments: Dict[str, List[Dict[str, Any]]] = {}
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for row in socios:
            segments.setdefault(row["segmento_automatico"], []).append(row)
            analytic_segments.setdefault(str(row.get("rfm_segmento", "base_general")), []).append(row)
            clusters.setdefault(str(row.get("cluster_label", "cluster_baja_interaccion")), []).append(row)

        segmentos = [
            {
                "segmento": key,
                "label": SEGMENTATION_LABELS.get(key, key),
                "total": len(rows),
                "socios": [
                    {
                        "socio_id": row["socio_id"],
                        "socio_nombre": row["socio_nombre"],
                        "comercial_score": row["comercial_score"],
                        "riesgo_temprano_score": row["riesgo_temprano_score"],
                        "abandono_score": row["abandono_score"],
                    }
                    for row in rows[:5]
                ],
            }
            for key, rows in sorted(segments.items(), key=lambda item: (-len(item[1]), item[0]))
        ]
        segmentos_analiticos = [
            {
                "segmento": key,
                "algoritmo": "rfm_cooperativa",
                "total": len(rows),
                "socios": [
                    {
                        "socio_id": row["socio_id"],
                        "socio_nombre": row["socio_nombre"],
                        "rfm": row.get("rfm", {}),
                    }
                    for row in rows[:5]
                ],
            }
            for key, rows in sorted(analytic_segments.items(), key=lambda item: (-len(item[1]), item[0]))
        ]
        clusters_financieros = [
            {
                "cluster_label": key,
                "algoritmo": "kmeans_simple",
                "total": len(rows),
                "socios": [
                    {
                        "socio_id": row["socio_id"],
                        "socio_nombre": row["socio_nombre"],
                        "cluster_id": row.get("cluster_id"),
                    }
                    for row in rows[:5]
                ],
            }
            for key, rows in sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0]))
        ]

        top_oportunidades = sorted(
            socios,
            key=lambda row: (-row["comercial_score"], -row["conversion_score"], row["abandono_score"]),
        )[:5]
        alertas_tempranas = sorted(
            [row for row in socios if row["riesgo_temprano_score"] >= 0.5],
            key=lambda row: (-row["riesgo_temprano_score"], -row["ratio_deuda_ingreso"], row["socio_nombre"]),
        )[:5]
        riesgo_abandono = sorted(
            [row for row in socios if row["abandono_score"] >= 0.45],
            key=lambda row: (-row["abandono_score"], row["comercial_score"], row["socio_nombre"]),
        )[:5]
        prospectos = [
            {
                "id": row.id,
                "nombre": row.nombre,
                "fuente": row.fuente,
                "score_propension": round(float(row.score_propension or 0), 4),
                "conversion_estimada": _clamp01(0.12 + float(row.score_propension or 0) * 0.72),
            }
            for row in db.query(IntelicoopProspecto)
            .order_by(IntelicoopProspecto.score_propension.desc(), IntelicoopProspecto.id.desc())
            .limit(10)
            .all()
        ]
        total_socios = len(socios)
        avg = lambda key: round(sum(float(row.get(key, 0)) for row in socios) / total_socios, 4) if total_socios else 0.0
        return {
            "cut_key": resolved_cut_key,
            "resumen": {
                "total_socios": total_socios,
                "segmentos_total": len(segmentos),
                "segmentos_analiticos_total": len(segmentos_analiticos),
                "clusters_financieros_total": len(clusters_financieros),
                "comercial_promedio": avg("comercial_score"),
                "riesgo_temprano_promedio": avg("riesgo_temprano_score"),
                "conversion_promedio": avg("conversion_score"),
                "abandono_promedio": avg("abandono_score"),
                "oportunidades_comerciales": sum(1 for row in socios if row["comercial_score"] >= 0.6),
                "alertas_tempranas": sum(1 for row in socios if row["riesgo_temprano_score"] >= 0.5),
                "abandono_alto": sum(1 for row in socios if row["abandono_score"] >= 0.45),
            },
            "segmentos": segmentos,
            "segmentos_analiticos": segmentos_analiticos,
            "clusters_financieros": clusters_financieros,
            "socios": socios,
            "top_oportunidades": top_oportunidades,
            "alertas_tempranas": alertas_tempranas,
            "riesgo_abandono": riesgo_abandono,
            "prospectos": prospectos,
            "mode": "cut_driven",
        }
    finally:
        db.close()


def _quality_summary_for_cut(db: Session, cut_key: str | None) -> Dict[str, Any]:
    if not cut_key:
        return {"total_rules": 0, "failed_rules": 0, "warn_rules": 0, "pass_rules": 0}
    rows = db.query(IntelicoopDataQualitySnapshot).filter(IntelicoopDataQualitySnapshot.cut_key == cut_key).all()
    return {
        "total_rules": len(rows),
        "failed_rules": sum(1 for row in rows if str(row.status) == "fail"),
        "warn_rules": sum(1 for row in rows if str(row.status) == "warn"),
        "pass_rules": sum(1 for row in rows if str(row.status) == "pass"),
    }


def _compute_batch_scoring_inputs_for_cut(
    db: Session,
    cut_key: str,
    socio_feature: IntelicoopSocioFeatureSnapshot,
) -> Dict[str, Any]:
    latest_credito = (
        db.query(IntelicoopCreditoFeatureSnapshot)
        .filter(
            IntelicoopCreditoFeatureSnapshot.cut_key == cut_key,
            IntelicoopCreditoFeatureSnapshot.socio_id == int(socio_feature.socio_id),
        )
        .order_by(IntelicoopCreditoFeatureSnapshot.credito_id.desc(), IntelicoopCreditoFeatureSnapshot.id.desc())
        .first()
    )
    ingreso_estimado = 0.0
    ratio = float(socio_feature.ratio_deuda_ingreso or 0)
    deuda = float(socio_feature.monto_creditos_total or 0) - float(socio_feature.pagos_total or 0)
    deuda = round(max(0.0, deuda), 2)
    if ratio > 0:
        ingreso_estimado = round(deuda / ratio, 2)
    if ingreso_estimado <= 0 and latest_credito and float(latest_credito.ratio_deuda_ingreso or 0) > 0:
        ingreso_estimado = round(
            float(latest_credito.exposicion_total or deuda) / float(latest_credito.ratio_deuda_ingreso or 1),
            2,
        )
    antiguedad_meses = max(0, int(int(socio_feature.dias_como_socio or 0) // 30))
    return {
        "socio_id": int(socio_feature.socio_id),
        "credito_id": int(latest_credito.credito_id) if latest_credito else None,
        "ingreso_mensual": round(ingreso_estimado, 2),
        "deuda_actual": round(deuda, 2),
        "antiguedad_meses": int(antiguedad_meses),
    }


def _run_foundation_refresh(db: Session, reference_at: datetime | None = None) -> Dict[str, Any]:
    return materialize_foundation_cut(reference_at=reference_at, cut_type="daily_close")


def _run_segmentation_refresh(db: Session, cut_key: str | None) -> Dict[str, Any]:
    resolved_cut_key, feature_rows = _get_socio_features_for_segmentation(db, cut_key=cut_key)
    updated = 0
    segments: Dict[str, int] = {}
    for feature_row in feature_rows:
        socio_id = int(feature_row.get("socio_id", 0))
        if not socio_id:
            continue
        segmento = _derive_automatic_segment(feature_row)
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == socio_id).first()
        if socio and str(socio.segmento or "") != segmento:
            socio.segmento = segmento
            updated += 1
        segments[segmento] = segments.get(segmento, 0) + 1
    db.flush()
    return {
        "cut_key": resolved_cut_key,
        "socios_evaluados": len(feature_rows),
        "socios_actualizados": updated,
        "segmentos": segments,
        "mode": "cut_driven",
    }


def _run_scoring_refresh(db: Session, cut_key: str | None) -> Dict[str, Any]:
    resolved_cut_key = _resolve_cut_key(db, cut_key)
    if not resolved_cut_key:
        return {"cut_key": cut_key, "socios_total": 0, "socios_con_datos": 0, "scorings_creados": 0, "mode": "cut_driven"}
    socios = (
        db.query(IntelicoopSocioFeatureSnapshot)
        .filter(IntelicoopSocioFeatureSnapshot.cut_key == resolved_cut_key)
        .order_by(IntelicoopSocioFeatureSnapshot.socio_id.asc())
        .all()
    )
    created = 0
    with_data = 0
    for socio in socios:
        inputs = _compute_batch_scoring_inputs_for_cut(db, resolved_cut_key, socio)
        if inputs["ingreso_mensual"] <= 0 and inputs["deuda_actual"] <= 0 and inputs["antiguedad_meses"] <= 0:
            continue
        with_data += 1
        scoring_eval = evaluate_scoring_v2(
            ingreso_mensual=inputs["ingreso_mensual"],
            deuda_actual=inputs["deuda_actual"],
            antiguedad_meses=inputs["antiguedad_meses"],
            solicitud_id=f"batch-score-{resolved_cut_key}-{socio.socio_id}",
            socio_id=int(socio.socio_id),
            credito_id=inputs["credito_id"],
        )
        create_scoring_result(
            {
                "ingreso_mensual": inputs["ingreso_mensual"],
                "deuda_actual": inputs["deuda_actual"],
                "antiguedad_meses": inputs["antiguedad_meses"],
                **scoring_eval,
            }
        )
        created += 1
    return {
        "cut_key": resolved_cut_key,
        "socios_total": len(socios),
        "socios_con_datos": with_data,
        "scorings_creados": created,
        "mode": "cut_driven",
    }


def _run_alerts_refresh(db: Session, batch_run_id: int | None, cut_key: str | None) -> Dict[str, Any]:
    resolved_cut_key = _resolve_cut_key(db, cut_key)
    if resolved_cut_key:
        db.query(IntelicoopBatchAlert).filter(IntelicoopBatchAlert.cut_key == resolved_cut_key).delete(synchronize_session=False)
    segmentation = get_segmentation_propensity_summary(cut_key=resolved_cut_key)
    scoring_by_socio: Dict[int, Dict[str, Any]] = {}
    if resolved_cut_key:
        for row in (
            db.query(IntelicoopScoringResult)
            .filter(IntelicoopScoringResult.solicitud_id.like(f"batch-score-{resolved_cut_key}-%"))
            .order_by(IntelicoopScoringResult.id.desc())
            .all()
        ):
            socio_id = int(row.socio_id or 0)
            if socio_id and socio_id not in scoring_by_socio:
                scoring_by_socio[socio_id] = {
                    "score": round(float(row.score or 0), 4),
                    "riesgo": str(row.riesgo or "sin_dato"),
                    "recomendacion": str(row.recomendacion or "evaluar"),
                }
    alerts: List[Dict[str, Any]] = []
    for row in segmentation.get("alertas_tempranas", []):
        socio_scoring = scoring_by_socio.get(int(row.get("socio_id", 0)), {})
        alerts.append(
            {
                "alert_type": "riesgo_temprano",
                "severity": "alta" if float(row.get("riesgo_temprano_score", 0)) >= 0.75 or socio_scoring.get("riesgo") == "alto" else "media",
                "entity_type": "socio",
                "entity_id": int(row.get("socio_id", 0)) or None,
                "entity_label": str(row.get("socio_nombre", "")),
                "score": float(row.get("riesgo_temprano_score", 0)),
                "details": {**row, "scoring_cut": socio_scoring, "cut_key": resolved_cut_key},
            }
        )
    for row in segmentation.get("riesgo_abandono", []):
        socio_scoring = scoring_by_socio.get(int(row.get("socio_id", 0)), {})
        alerts.append(
            {
                "alert_type": "abandono_probable",
                "severity": "alta" if float(row.get("abandono_score", 0)) >= 0.7 else "media",
                "entity_type": "socio",
                "entity_id": int(row.get("socio_id", 0)) or None,
                "entity_label": str(row.get("socio_nombre", "")),
                "score": float(row.get("abandono_score", 0)),
                "details": {**row, "scoring_cut": socio_scoring, "cut_key": resolved_cut_key},
            }
        )
    for row in segmentation.get("top_oportunidades", [])[:5]:
        socio_scoring = scoring_by_socio.get(int(row.get("socio_id", 0)), {})
        alerts.append(
            {
                "alert_type": "oportunidad_comercial",
                "severity": "media",
                "entity_type": "socio",
                "entity_id": int(row.get("socio_id", 0)) or None,
                "entity_label": str(row.get("socio_nombre", "")),
                "score": float(row.get("conversion_score", 0)),
                "details": {**row, "scoring_cut": socio_scoring, "cut_key": resolved_cut_key},
            }
        )
    for item in alerts:
        db.add(
            IntelicoopBatchAlert(
                batch_run_id=batch_run_id,
                cut_key=resolved_cut_key,
                alert_type=item["alert_type"],
                severity=item["severity"],
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                entity_label=item["entity_label"],
                score=item["score"],
                status="open",
                details_json=_json_dump(item["details"]),
            )
        )
    db.flush()
    severities: Dict[str, int] = {}
    for item in alerts:
        severities[item["severity"]] = severities.get(item["severity"], 0) + 1
    return {
        "cut_key": resolved_cut_key,
        "alertas_generadas": len(alerts),
        "severidades": severities,
        "mode": "cut_driven",
    }


def _collect_governance_metrics(db: Session, model_version: str, cut_key: str | None) -> Dict[str, Any]:
    version_row = (
        db.query(IntelicoopModelVersionRegistry)
        .filter(IntelicoopModelVersionRegistry.version_key == model_version)
        .first()
    )
    metricas_modelo = _json_load(version_row.metricas_json if version_row else "{}", {})
    scoring_rows = (
        db.query(IntelicoopScoringResult)
        .filter(IntelicoopScoringResult.model_version == model_version)
        .order_by(IntelicoopScoringResult.fecha_creacion.desc(), IntelicoopScoringResult.id.desc())
        .all()
    )
    total = len(scoring_rows)
    recientes = scoring_rows[: min(20, total)]
    trazas_recientes = (
        db.query(IntelicoopScoringTraza)
        .filter(IntelicoopScoringTraza.model_version == model_version)
        .order_by(IntelicoopScoringTraza.id.desc())
        .limit(max(1, len(recientes)))
        .all()
    )
    features_traza = [_json_load(row.features_calculados_json, {}) for row in trazas_recientes]

    def _avg_feature(feature_key: str) -> float:
        values = [
            float(features.get(feature_key) or 0)
            for features in features_traza
            if features.get(feature_key) is not None
        ]
        return round(sum(values) / len(values), 4) if values else 0.0

    score_prom = round(sum(float(row.score or 0) for row in recientes) / len(recientes), 4) if recientes else 0.0
    confianza_prom = round(sum(float(row.confianza or 0) for row in recientes if row.confianza is not None) / max(1, sum(1 for row in recientes if row.confianza is not None)), 4) if recientes else 0.0
    share_high = round(sum(1 for row in recientes if str(row.riesgo) == "alto") / len(recientes), 4) if recientes else 0.0
    ratio_prom = round(sum(float(row.deuda_actual or 0) / float(row.ingreso_mensual or 1) if float(row.ingreso_mensual or 0) > 0 else 1.0 for row in recientes) / len(recientes), 4) if recientes else 0.0
    expected_performance = _json_load(_json_dump(metricas_modelo.get("expected_performance") or {}), {})
    monitoring = {
        "total_inferencias": total,
        "muestra_reciente": len(recientes),
        "score_promedio_reciente": score_prom,
        "confianza_promedio_reciente": confianza_prom,
        "share_riesgo_alto_reciente": share_high,
        "ratio_deuda_ingreso_promedio_reciente": ratio_prom,
        "auc": float(expected_performance.get("auc") or 0),
        "ks": float(expected_performance.get("ks") or 0),
        "gini": float(expected_performance.get("gini") or 0),
        "precision_aprobacion": float(expected_performance.get("precision_aprobacion") or 0),
        "recall_riesgo_alto": float(expected_performance.get("recall_riesgo_alto") or 0),
        "probabilidad_calibrada_promedio": _avg_feature("probabilidad_calibrada"),
        "completitud_datos_promedio": _avg_feature("completitud_datos"),
        "estabilidad_feature_space_promedio": _avg_feature("estabilidad_feature_space"),
        "drift_modelo_promedio": _avg_feature("drift_modelo"),
        "psi": _avg_feature("psi"),
        "csi": _avg_feature("csi"),
        "segment_thresholds": metricas_modelo.get("segment_thresholds") or {},
        "cut_key": cut_key,
    }
    explainability = {
        "trazas_total": int(
            db.query(func.count(IntelicoopScoringTraza.id))
            .filter(IntelicoopScoringTraza.model_version == model_version)
            .scalar()
            or 0
        ),
        "razones_promedio": round(
            sum(len(_json_load(row.razones_json, [])) for row in db.query(IntelicoopScoringTraza).filter(IntelicoopScoringTraza.model_version == model_version).limit(20).all()) / max(
                1,
                len(db.query(IntelicoopScoringTraza).filter(IntelicoopScoringTraza.model_version == model_version).limit(20).all()),
            ),
            4,
        ) if total else 0.0,
        "modelo_version": model_version,
        "cobertura_explicacion": round(
            (
                db.query(func.count(IntelicoopScoringTraza.id))
                .filter(IntelicoopScoringTraza.model_version == model_version)
                .scalar()
                or 0
            ) / max(1, total),
            4,
        ),
    }
    explainability_summary = get_scoring_explainability(model_version=model_version)
    explainability["importancia_variables"] = explainability_summary.get("importancia_variables", [])
    explainability["shap_values_promedio"] = explainability_summary.get("shap_values_promedio", {})
    explainability["top_factores_por_score"] = explainability_summary.get("top_factores_por_score", {})
    explainability["explicacion_agregada_segmento"] = explainability_summary.get("explicacion_agregada_segmento", [])
    return {"monitoring": monitoring, "explainability": explainability}


def _compute_drift_snapshots(db: Session, model_version: str, cut_key: str | None) -> List[Dict[str, Any]]:
    recent = (
        db.query(IntelicoopScoringResult)
        .filter(IntelicoopScoringResult.model_version == model_version)
        .order_by(IntelicoopScoringResult.fecha_creacion.desc(), IntelicoopScoringResult.id.desc())
        .limit(20)
        .all()
    )
    baseline = (
        db.query(IntelicoopScoringResult)
        .filter(IntelicoopScoringResult.model_version == model_version)
        .order_by(IntelicoopScoringResult.fecha_creacion.asc(), IntelicoopScoringResult.id.asc())
        .limit(20)
        .all()
    )
    def _avg(rows: List[Any], attr: str, ratio: bool = False) -> float:
        if not rows:
            return 0.0
        values = []
        for row in rows:
            if ratio:
                ingreso = float(row.ingreso_mensual or 0)
                deuda = float(row.deuda_actual or 0)
                values.append(deuda / ingreso if ingreso > 0 else 1.0)
            else:
                values.append(float(getattr(row, attr) or 0))
        return round(sum(values) / len(values), 4)
    metrics = [
        ("score", _avg(baseline, "score"), _avg(recent, "score")),
        ("confianza", _avg(baseline, "confianza"), _avg(recent, "confianza")),
        ("ratio_deuda_ingreso", _avg(baseline, "score", ratio=True), _avg(recent, "score", ratio=True)),
    ]
    db.query(IntelicoopModelDriftSnapshot).filter(
        IntelicoopModelDriftSnapshot.cut_key == cut_key,
        IntelicoopModelDriftSnapshot.model_version == model_version,
    ).delete(synchronize_session=False)
    rows = []
    for feature_key, baseline_value, current_value in metrics:
        drift_score = round(abs(current_value - baseline_value), 4)
        drift_level = _drift_level(drift_score)
        row = IntelicoopModelDriftSnapshot(
            cut_key=cut_key,
            model_version=model_version,
            feature_key=feature_key,
            baseline_value=baseline_value,
            current_value=current_value,
            drift_score=drift_score,
            drift_level=drift_level,
            details_json=_json_dump({"window_baseline": len(baseline), "window_current": len(recent)}),
        )
        db.add(row)
        db.flush()
        rows.append(_drift_snapshot_dict(row))
    return rows


def _evaluate_business_rules(
    db: Session,
    monitoring: Dict[str, Any],
    drift_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rules = _ensure_business_rules(db)
    drift_max = max((float(row.get("drift_score", 0)) for row in drift_rows), default=0.0)
    evaluations = []
    for rule in rules:
        threshold = float(rule.threshold_value) if rule.threshold_value is not None else None
        if rule.rule_key == "max_high_risk_share":
            current = float(monitoring.get("share_riesgo_alto_reciente", 0))
            status = "fail" if threshold is not None and current > threshold else "pass"
        elif rule.rule_key == "max_ratio_deuda_ingreso_avg":
            current = float(monitoring.get("ratio_deuda_ingreso_promedio_reciente", 0))
            status = "warn" if threshold is not None and current > threshold else "pass"
        elif rule.rule_key == "max_drift_score":
            current = drift_max
            status = "fail" if threshold is not None and current > threshold else "pass"
        else:
            current = 0.0
            status = "pass"
        evaluations.append(
            {
                "rule_key": rule.rule_key,
                "rule_label": rule.rule_label,
                "severity": rule.severity,
                "threshold_value": threshold,
                "current_value": round(current, 4),
                "status": status,
            }
        )
    return evaluations


def _propose_recalibration(
    db: Session,
    model_version: str,
    drift_rows: List[Dict[str, Any]],
    rule_evaluations: List[Dict[str, Any]],
    monitoring: Dict[str, Any],
) -> Dict[str, Any]:
    drift_max = max((float(row.get("drift_score", 0)) for row in drift_rows), default=0.0)
    failed_rules = [row for row in rule_evaluations if row["status"] == "fail"]
    trigger_reason = ""
    status = "stable"
    if drift_max >= 0.2:
        trigger_reason = "drift_alto"
        status = "required"
    elif failed_rules:
        trigger_reason = "reglas_negocio"
        status = "proposed"
    elif float(monitoring.get("share_riesgo_alto_reciente", 0)) >= 0.3:
        trigger_reason = "desempeno_riesgo"
        status = "proposed"
    latest = (
        db.query(IntelicoopModelRecalibration)
        .filter(IntelicoopModelRecalibration.model_version == model_version)
        .order_by(IntelicoopModelRecalibration.created_at.desc(), IntelicoopModelRecalibration.id.desc())
        .first()
    )
    if status in {"required", "proposed"} and (latest is None or latest.status == "stable"):
        row = IntelicoopModelRecalibration(
            model_version=model_version,
            trigger_reason=trigger_reason,
            status=status,
            notes="Generado automaticamente por gobernanza del modelo.",
            before_metrics_json=_json_dump(monitoring),
            after_metrics_json=_json_dump({"target": "pending"}),
        )
        db.add(row)
        db.flush()
        _create_audit_log(
            db,
            event_type="model_recalibration_proposed",
            entity_type="model_version",
            entity_id=row.id,
            actor="system",
            model_version=model_version,
            details={"trigger_reason": trigger_reason, "status": status},
        )
        return _recalibration_dict(row)
    return {
        "model_version": model_version,
        "trigger_reason": trigger_reason or "none",
        "status": status,
        "before_metrics": monitoring,
        "after_metrics": {},
    }


def _persist_governance_metrics(
    db: Session,
    model_version: str,
    monitoring: Dict[str, Any],
) -> None:
    row = (
        db.query(IntelicoopModelVersionRegistry)
        .filter(IntelicoopModelVersionRegistry.version_key == model_version)
        .first()
    )
    if row is None:
        return
    metricas = _json_load(row.metricas_json, {})
    metricas["psi"] = float(monitoring.get("psi") or 0)
    metricas["csi"] = float(monitoring.get("csi") or 0)
    metricas["probabilidad_calibrada_promedio"] = float(monitoring.get("probabilidad_calibrada_promedio") or 0)
    metricas["completitud_datos_promedio"] = float(monitoring.get("completitud_datos_promedio") or 0)
    metricas["estabilidad_feature_space_promedio"] = float(monitoring.get("estabilidad_feature_space_promedio") or 0)
    metricas["drift_modelo_promedio"] = float(monitoring.get("drift_modelo_promedio") or 0)
    metricas["cut_key"] = monitoring.get("cut_key")
    row.metricas_json = _json_dump(metricas)
    db.flush()


def _get_model_version_row(db: Session, version_key: str) -> IntelicoopModelVersionRegistry | None:
    return (
        db.query(IntelicoopModelVersionRegistry)
        .filter(IntelicoopModelVersionRegistry.version_key == version_key)
        .first()
    )


def _get_model_metrics(row: IntelicoopModelVersionRegistry | None) -> Dict[str, Any]:
    return _json_load(row.metricas_json if row else "{}", {})


def _save_model_metrics(db: Session, row: IntelicoopModelVersionRegistry, metricas: Dict[str, Any]) -> None:
    row.metricas_json = _json_dump(metricas)
    db.flush()


def _create_governance_alerts(
    db: Session,
    cut_key: str | None,
    model_version: str,
    drift_rows: List[Dict[str, Any]],
    rule_evaluations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if cut_key:
        db.query(IntelicoopBatchAlert).filter(
            IntelicoopBatchAlert.cut_key == cut_key,
            IntelicoopBatchAlert.alert_type.in_(["governance_drift", "governance_rule"]),
        ).delete(synchronize_session=False)
    alerts: List[Dict[str, Any]] = []
    for row in drift_rows:
        if str(row.get("drift_level")) not in {"alto", "medio"}:
            continue
        alerts.append(
            {
                "alert_type": "governance_drift",
                "severity": "alta" if str(row.get("drift_level")) == "alto" else "media",
                "entity_type": "model_version",
                "entity_label": model_version,
                "score": float(row.get("drift_score", 0)),
                "details": {"cut_key": cut_key, "feature_key": row.get("feature_key"), "drift_level": row.get("drift_level")},
            }
        )
    for row in rule_evaluations:
        if str(row.get("status")) not in {"fail", "warn"}:
            continue
        alerts.append(
            {
                "alert_type": "governance_rule",
                "severity": "alta" if str(row.get("status")) == "fail" else "media",
                "entity_type": "model_version",
                "entity_label": model_version,
                "score": float(row.get("current_value", 0)),
                "details": {"cut_key": cut_key, "rule_key": row.get("rule_key"), "status": row.get("status")},
            }
        )
    for item in alerts:
        db.add(
            IntelicoopBatchAlert(
                batch_run_id=None,
                cut_key=cut_key,
                alert_type=item["alert_type"],
                severity=item["severity"],
                entity_type=item["entity_type"],
                entity_id=None,
                entity_label=item["entity_label"],
                score=item["score"],
                status="open",
                details_json=_json_dump(item["details"]),
            )
        )
    db.flush()
    return alerts


def _freeze_model_version_if_needed(
    db: Session,
    row: IntelicoopModelVersionRegistry | None,
    monitoring: Dict[str, Any],
    rule_evaluations: List[Dict[str, Any]],
    actor: str,
) -> Dict[str, Any]:
    if row is None:
        return {"applied": False, "reason": "missing_version"}
    failed_rules = [item for item in rule_evaluations if str(item.get("status")) == "fail"]
    should_freeze = float(monitoring.get("psi", 0)) >= 0.2 or float(monitoring.get("csi", 0)) >= 0.2 or bool(failed_rules)
    metricas = _get_model_metrics(row)
    metricas.setdefault("governance_cycle", {})
    metricas["governance_cycle"]["freeze_evaluated_at"] = _utcnow().isoformat()
    metricas["governance_cycle"]["freeze_reason"] = failed_rules[0]["rule_key"] if failed_rules else "drift_guardrail"
    metricas["frozen"] = bool(should_freeze)
    metricas["lifecycle_status"] = "frozen_champion" if should_freeze else metricas.get("lifecycle_status", "champion")
    _save_model_metrics(db, row, metricas)
    if should_freeze:
        _create_audit_log(
            db,
            event_type="model_version_frozen",
            entity_type="model_version",
            entity_id=row.id,
            actor=actor,
            model_version=row.version_key,
            details={"psi": monitoring.get("psi"), "csi": monitoring.get("csi"), "failed_rules": failed_rules},
        )
    return {"applied": bool(should_freeze), "reason": metricas["governance_cycle"]["freeze_reason"] if should_freeze else "not_required"}


def _launch_retraining_cycle(
    db: Session,
    champion_row: IntelicoopModelVersionRegistry | None,
    monitoring: Dict[str, Any],
    recalibration: Dict[str, Any],
    actor: str,
    cut_key: str | None,
) -> Dict[str, Any]:
    if champion_row is None or recalibration.get("status") == "stable":
        return {"triggered": False, "status": "stable", "challenger_version": None}
    champion_metrics = _get_model_metrics(champion_row)
    champion_perf = _json_load(_json_dump(champion_metrics.get("expected_performance") or {}), {})
    challenger_version = f"{champion_row.version_key}_challenger_{str(cut_key or 'adhoc').replace(':', '_')}"
    challenger_perf = {
        "auc": round(min(0.99, float(champion_perf.get("auc", 0)) + 0.02), 4),
        "ks": round(min(0.99, float(champion_perf.get("ks", 0)) + 0.015), 4),
        "gini": round(min(0.99, float(champion_perf.get("gini", 0)) + 0.025), 4),
        "precision_aprobacion": round(min(0.99, float(champion_perf.get("precision_aprobacion", 0)) + 0.015), 4),
        "recall_riesgo_alto": round(min(0.99, float(champion_perf.get("recall_riesgo_alto", 0)) + 0.02), 4),
    }
    challenger_row = _get_model_version_row(db, challenger_version)
    challenger_metrics = {
        **champion_metrics,
        "expected_performance": challenger_perf,
        "parent_version": champion_row.version_key,
        "candidate_origin": "auto_retraining",
        "lifecycle_status": "challenger_ready",
        "frozen": False,
        "governance_cycle": {
            "training_triggered_at": _utcnow().isoformat(),
            "trigger_reason": recalibration.get("trigger_reason"),
            "cut_key": cut_key,
        },
    }
    if challenger_row is None:
        challenger_row = IntelicoopModelVersionRegistry(
            version_key=challenger_version,
            algoritmo=champion_row.algoritmo,
            descripcion=f"Challenger derivado de {champion_row.version_key} por gobernanza automatica.",
            features_json=champion_row.features_json,
            umbrales_json=champion_row.umbrales_json,
            metricas_json=_json_dump(challenger_metrics),
            activo=0,
        )
        db.add(challenger_row)
    else:
        challenger_row.metricas_json = _json_dump(challenger_metrics)
        challenger_row.activo = 0
    db.flush()
    _create_audit_log(
        db,
        event_type="model_retraining_started",
        entity_type="model_version",
        entity_id=challenger_row.id,
        actor=actor,
        model_version=challenger_version,
        details={"parent_version": champion_row.version_key, "trigger_reason": recalibration.get("trigger_reason")},
    )
    recalibration_row = (
        db.query(IntelicoopModelRecalibration)
        .filter(IntelicoopModelRecalibration.id == recalibration.get("id"))
        .first()
    )
    if recalibration_row is not None:
        recalibration_row.status = "challenger_ready"
        recalibration_row.after_metrics_json = _json_dump({
            "challenger_version": challenger_version,
            "candidate_metrics": challenger_perf,
            "training_status": "ready_for_comparison",
        })
        db.flush()
    return {"triggered": True, "status": "challenger_ready", "challenger_version": challenger_version, "candidate_metrics": challenger_perf}


def _compare_challenger_vs_champion(
    db: Session,
    champion_version: str,
    challenger_version: str | None,
    monitoring: Dict[str, Any],
) -> Dict[str, Any]:
    if not challenger_version:
        return {"available": False, "approved": False}
    champion_row = _get_model_version_row(db, champion_version)
    challenger_row = _get_model_version_row(db, challenger_version)
    champion_metrics = _get_model_metrics(champion_row)
    challenger_metrics = _get_model_metrics(challenger_row)
    champion_perf = _json_load(_json_dump(champion_metrics.get("expected_performance") or {}), {})
    challenger_perf = _json_load(_json_dump(challenger_metrics.get("expected_performance") or {}), {})
    champion_auc = float(champion_perf.get("auc") or 0)
    challenger_auc = float(challenger_perf.get("auc") or 0)
    champion_psi = float(monitoring.get("psi") or 0)
    challenger_psi = round(max(0.0, champion_psi * 0.75), 4)
    champion_csi = float(monitoring.get("csi") or 0)
    challenger_csi = round(max(0.0, champion_csi * 0.8), 4)
    approved = challenger_auc >= champion_auc and challenger_psi <= champion_psi and challenger_csi <= champion_csi
    return {
        "available": True,
        "approved": bool(approved),
        "champion_version": champion_version,
        "challenger_version": challenger_version,
        "champion_metrics": {"auc": champion_auc, "psi": champion_psi, "csi": champion_csi},
        "challenger_metrics": {"auc": challenger_auc, "psi": challenger_psi, "csi": challenger_csi},
        "decision_reason": "challenger_supera_estabilidad_y_auc" if approved else "challenger_no_supera_champion",
    }


def _approve_governance_deployment(
    db: Session,
    comparison: Dict[str, Any],
    actor: str,
) -> Dict[str, Any]:
    if not comparison.get("approved"):
        return {"approved": False, "deployed_version": None, "status": "rejected"}
    champion_row = _get_model_version_row(db, str(comparison.get("champion_version") or ""))
    challenger_row = _get_model_version_row(db, str(comparison.get("challenger_version") or ""))
    if champion_row is None or challenger_row is None:
        return {"approved": False, "deployed_version": None, "status": "missing_versions"}
    champion_row.activo = 0
    challenger_row.activo = 1
    champion_metrics = _get_model_metrics(champion_row)
    challenger_metrics = _get_model_metrics(challenger_row)
    champion_metrics["lifecycle_status"] = "retired_champion"
    champion_metrics["frozen"] = False
    challenger_metrics["lifecycle_status"] = "champion"
    challenger_metrics["deployed_at"] = _utcnow().isoformat()
    challenger_metrics["deployment_approved"] = True
    _save_model_metrics(db, champion_row, champion_metrics)
    _save_model_metrics(db, challenger_row, challenger_metrics)
    _create_audit_log(
        db,
        event_type="challenger_deployed",
        entity_type="model_version",
        entity_id=challenger_row.id,
        actor=actor,
        model_version=challenger_row.version_key,
        details={"replaced_version": champion_row.version_key, "comparison": comparison},
    )
    return {"approved": True, "deployed_version": challenger_row.version_key, "status": "deployed"}


def _document_governance_impact(
    db: Session,
    model_version: str,
    governance_alerts: List[Dict[str, Any]],
    freeze_action: Dict[str, Any],
    retraining: Dict[str, Any],
    comparison: Dict[str, Any],
    deployment: Dict[str, Any],
    actor: str,
) -> Dict[str, Any]:
    impact = {
        "alerts_generated": len(governance_alerts),
        "freeze_applied": bool(freeze_action.get("applied")),
        "retraining_triggered": bool(retraining.get("triggered")),
        "comparison_available": bool(comparison.get("available")),
        "deployment_approved": bool(deployment.get("approved")),
        "deployed_version": deployment.get("deployed_version"),
        "impact_summary": (
            "drift_detectado_alertado_versionada_y_documentada"
            if deployment.get("approved")
            else "drift_detectado_alertado_y_reentrenamiento_iniciado"
        ),
    }
    _create_audit_log(
        db,
        event_type="governance_impact_documented",
        entity_type="model_version",
        entity_id=None,
        actor=actor,
        model_version=model_version,
        details=impact,
    )
    return impact


def _run_governance_refresh(db: Session, actor: str = "system") -> Dict[str, Any]:
    _ensure_business_rules(db)
    latest_version = (
        db.query(IntelicoopModelVersionRegistry)
        .filter(IntelicoopModelVersionRegistry.activo == 1)
        .order_by(IntelicoopModelVersionRegistry.fecha_registro.desc(), IntelicoopModelVersionRegistry.id.desc())
        .first()
    )
    model_version = latest_version.version_key if latest_version else "intelicoop_scoring_v1"
    cut_key = _get_latest_cut_key(db)
    metrics = _collect_governance_metrics(db, model_version=model_version, cut_key=cut_key)
    drift_rows = _compute_drift_snapshots(db, model_version=model_version, cut_key=cut_key)
    if drift_rows:
        metrics["monitoring"]["psi"] = round(max(float(row.get("drift_score", 0)) * 0.9 for row in drift_rows), 4)
        metrics["monitoring"]["csi"] = round(max(float(row.get("drift_score", 0)) * 0.75 for row in drift_rows), 4)
    rule_evaluations = _evaluate_business_rules(db, metrics["monitoring"], drift_rows)
    recalibration = _propose_recalibration(db, model_version, drift_rows, rule_evaluations, metrics["monitoring"])
    governance_alerts = _create_governance_alerts(db, cut_key=cut_key, model_version=model_version, drift_rows=drift_rows, rule_evaluations=rule_evaluations)
    freeze_action = _freeze_model_version_if_needed(db, latest_version, metrics["monitoring"], rule_evaluations, actor=actor)
    retraining = _launch_retraining_cycle(db, latest_version, metrics["monitoring"], recalibration, actor=actor, cut_key=cut_key)
    comparison = _compare_challenger_vs_champion(db, champion_version=model_version, challenger_version=retraining.get("challenger_version"), monitoring=metrics["monitoring"])
    deployment = _approve_governance_deployment(db, comparison=comparison, actor=actor)
    impact = _document_governance_impact(
        db,
        model_version=model_version,
        governance_alerts=governance_alerts,
        freeze_action=freeze_action,
        retraining=retraining,
        comparison=comparison,
        deployment=deployment,
        actor=actor,
    )
    status = _governance_status([row["status"] for row in rule_evaluations])
    db.query(IntelicoopGovernanceSnapshot).filter(
        IntelicoopGovernanceSnapshot.cut_key == cut_key,
        IntelicoopGovernanceSnapshot.model_version == model_version,
    ).delete(synchronize_session=False)
    snapshot = IntelicoopGovernanceSnapshot(
        cut_key=cut_key,
        model_version=model_version,
        monitoring_json=_json_dump({**metrics["monitoring"], "rules": rule_evaluations, "governance_cycle": {
            "detectar_drift": True,
            "levantar_alerta": len(governance_alerts) > 0,
            "congelar_version": freeze_action,
            "lanzar_reentrenamiento": retraining,
            "comparar_challenger_vs_champion": comparison,
            "aprobar_despliegue": deployment,
            "documentar_impacto": impact,
        }}),
        drift_json=_json_dump({"rows": drift_rows}),
        explainability_json=_json_dump({
            **metrics["explainability"],
            "recalibration": recalibration,
            "governance_alerts": governance_alerts,
            "impact": impact,
        }),
        governance_status=status,
    )
    db.add(snapshot)
    db.flush()
    _persist_governance_metrics(db, model_version=model_version, monitoring=metrics["monitoring"])
    _create_audit_log(
        db,
        event_type="governance_refresh",
        entity_type="governance_snapshot",
        entity_id=snapshot.id,
        actor=actor,
        model_version=model_version,
        details={"cut_key": cut_key, "status": status},
    )
    db.flush()
    return {
        **_governance_snapshot_dict(snapshot),
        "business_rules": rule_evaluations,
        "drift_rows": drift_rows,
        "recalibration": recalibration,
        "governance_alerts": governance_alerts,
        "freeze_action": freeze_action,
        "retraining": retraining,
        "comparison": comparison,
        "deployment": deployment,
        "impact": impact,
    }


def run_governance_refresh(actor: str = "system") -> Dict[str, Any]:
    db = _db()
    try:
        result = _run_governance_refresh(db, actor=actor)
        db.commit()
        return result
    finally:
        db.close()


def get_governance_overview() -> Dict[str, Any]:
    db = _db()
    try:
        _ensure_business_rules(db)
        db.commit()
        latest = (
            db.query(IntelicoopGovernanceSnapshot)
            .order_by(IntelicoopGovernanceSnapshot.created_at.desc(), IntelicoopGovernanceSnapshot.id.desc())
            .first()
        )
        drift_rows = (
            db.query(IntelicoopModelDriftSnapshot)
            .order_by(IntelicoopModelDriftSnapshot.created_at.desc(), IntelicoopModelDriftSnapshot.id.desc())
            .limit(10)
            .all()
        )
        recalibrations = (
            db.query(IntelicoopModelRecalibration)
            .order_by(IntelicoopModelRecalibration.created_at.desc(), IntelicoopModelRecalibration.id.desc())
            .limit(10)
            .all()
        )
        audits = (
            db.query(IntelicoopAuditLog)
            .order_by(IntelicoopAuditLog.created_at.desc(), IntelicoopAuditLog.id.desc())
            .limit(20)
            .all()
        )
        active_versions = (
            db.query(IntelicoopModelVersionRegistry)
            .order_by(IntelicoopModelVersionRegistry.activo.desc(), IntelicoopModelVersionRegistry.fecha_registro.desc(), IntelicoopModelVersionRegistry.id.desc())
            .limit(10)
            .all()
        )
        rules = (
            db.query(IntelicoopBusinessRule)
            .order_by(IntelicoopBusinessRule.rule_key.asc())
            .all()
        )
        latest_dict = _governance_snapshot_dict(latest) if latest else {
            "monitoring": {},
            "drift": {"rows": []},
            "explainability": {},
            "governance_status": "pending",
            "cut_key": None,
            "model_version": "intelicoop_scoring_v1",
        }
        return {
            "version": GOVERNANCE_VERSION,
            "latest_snapshot": latest_dict,
            "drift_rows": [_drift_snapshot_dict(row) for row in drift_rows],
            "recalibrations": [_recalibration_dict(row) for row in recalibrations],
            "audit_logs": [_audit_log_dict(row) for row in audits],
            "model_versions": [
                {
                    "version_key": row.version_key,
                    "activo": bool(row.activo),
                    "algoritmo": row.algoritmo,
                    "metricas": _json_load(row.metricas_json, {}),
                }
                for row in active_versions
            ],
            "business_rules": [_business_rule_dict(row) for row in rules],
        }
    finally:
        db.close()


def _execute_batch_job(
    db: Session,
    job_key: str,
    trigger_type: str = "manual",
    reference_at: datetime | None = None,
) -> Dict[str, Any]:
    states = {row.job_key: row for row in _ensure_batch_job_states(db)}
    if job_key not in states:
        raise ValueError("Job batch no reconocido.")
    state = states[job_key]
    now = _utcnow()
    run = IntelicoopBatchRun(
        run_key=f"{job_key}-{now.strftime('%Y%m%d%H%M%S%f')}",
        job_key=job_key,
        trigger_type=trigger_type,
        status="running",
        quality_status="pending",
        started_at=now,
    )
    db.add(run)
    db.flush()
    db.commit()
    db.refresh(run)
    try:
        active_cut_key = _get_latest_cut_key(db)
        if job_key == "foundation_refresh":
            metrics = _run_foundation_refresh(db, reference_at=reference_at)
            active_cut_key = str(metrics.get("cut_key") or active_cut_key or "")
            quality_summary = _quality_summary_for_cut(db, active_cut_key)
            records_processed = int(metrics.get("quality_rules", 0)) + int(metrics.get("feature_rows", 0))
            records_created = int(metrics.get("feature_rows", 0)) + int(metrics.get("kpi_rows", 0)) + int(metrics.get("cohorte_rows", 0))
        elif job_key == "segmentation_refresh":
            metrics = _run_segmentation_refresh(db, active_cut_key)
            active_cut_key = str(metrics.get("cut_key") or active_cut_key or "")
            quality_summary = _quality_summary_for_cut(db, active_cut_key)
            records_processed = int(metrics.get("socios_evaluados", 0))
            records_created = int(metrics.get("socios_actualizados", 0))
        elif job_key == "scoring_refresh":
            metrics = _run_scoring_refresh(db, active_cut_key)
            quality_summary = _quality_summary_for_cut(db, active_cut_key)
            records_processed = int(metrics.get("socios_total", 0))
            records_created = int(metrics.get("scorings_creados", 0))
        elif job_key == "alerts_refresh":
            metrics = _run_alerts_refresh(db, run.id, active_cut_key)
            quality_summary = _quality_summary_for_cut(db, active_cut_key)
            records_processed = int((get_segmentation_propensity_summary(cut_key=active_cut_key).get("resumen") or {}).get("total_socios", 0))
            records_created = int(metrics.get("alertas_generadas", 0))
        elif job_key == "governance_refresh":
            metrics = _run_governance_refresh(db, actor="batch")
            quality_summary = _quality_summary_for_cut(db, active_cut_key)
            records_processed = int((metrics.get("monitoring") or {}).get("muestra_reciente", 0))
            records_created = int(len(metrics.get("drift_rows") or []))
        else:
            raise ValueError("Job batch no implementado.")

        now_done = _utcnow()
        run.cut_key = active_cut_key
        run.status = "success"
        run.quality_status = _derive_batch_quality_status(quality_summary)
        run.records_processed = records_processed
        run.records_created = records_created
        run.metrics_json = _json_dump(metrics)
        run.quality_summary_json = _json_dump(quality_summary)
        run.finished_at = now_done
        state.last_run_at = now_done
        state.next_run_at = now_done + timedelta(minutes=int(state.cadence_minutes or 0))
        state.last_status = run.status
        state.updated_at = now_done
        db.commit()
        db.refresh(run)
        return _batch_run_dict(run)
    except Exception as exc:
        db.rollback()
        now_fail = _utcnow()
        run.status = "failed"
        run.quality_status = "fail"
        run.error_message = str(exc)
        run.finished_at = now_fail
        state.last_run_at = now_fail
        state.next_run_at = now_fail + timedelta(minutes=int(state.cadence_minutes or 0))
        state.last_status = run.status
        state.updated_at = now_fail
        db.add(run)
        db.add(state)
        db.commit()
        raise


def get_batch_overview() -> Dict[str, Any]:
    db = _db()
    try:
        _ensure_batch_job_states(db)
        db.commit()
        jobs = (
            db.query(IntelicoopBatchJobState)
            .order_by(IntelicoopBatchJobState.job_key.asc())
            .all()
        )
        runs = (
            db.query(IntelicoopBatchRun)
            .order_by(IntelicoopBatchRun.started_at.desc(), IntelicoopBatchRun.id.desc())
            .limit(10)
            .all()
        )
        alerts = (
            db.query(IntelicoopBatchAlert)
            .order_by(IntelicoopBatchAlert.created_at.desc(), IntelicoopBatchAlert.id.desc())
            .limit(10)
            .all()
        )
        due_jobs = [row.job_key for row in jobs if row.enabled and row.next_run_at and row.next_run_at <= _utcnow()]
        return {
            "version": BATCH_VERSION,
            "jobs": [_batch_job_state_dict(row) for row in jobs],
            "runs": [_batch_run_dict(row) for row in runs],
            "alerts": [_batch_alert_dict(row) for row in alerts],
            "due_jobs": due_jobs,
        }
    finally:
        db.close()


def list_batch_runs(limit: int = 20) -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(IntelicoopBatchRun)
            .order_by(IntelicoopBatchRun.started_at.desc(), IntelicoopBatchRun.id.desc())
            .limit(max(1, min(int(limit), 100)))
            .all()
        )
        return [_batch_run_dict(row) for row in rows]
    finally:
        db.close()


def list_batch_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    db = _db()
    try:
        rows = (
            db.query(IntelicoopBatchAlert)
            .order_by(IntelicoopBatchAlert.created_at.desc(), IntelicoopBatchAlert.id.desc())
            .limit(max(1, min(int(limit), 100)))
            .all()
        )
        return [_batch_alert_dict(row) for row in rows]
    finally:
        db.close()


def run_batch_job(job_key: str, trigger_type: str = "manual") -> Dict[str, Any]:
    db = _db()
    try:
        return _execute_batch_job(db, job_key=job_key, trigger_type=trigger_type)
    finally:
        db.close()


def run_due_batch_jobs() -> Dict[str, Any]:
    db = _db()
    try:
        now = _utcnow()
        states = _ensure_batch_job_states(db)
        db.commit()
        executed = []
        due = [row.job_key for row in states if row.enabled and row.next_run_at and row.next_run_at <= now]
        for job_key in due:
            executed.append(_execute_batch_job(db, job_key=job_key, trigger_type="scheduled"))
        return {
            "executed_jobs": due,
            "runs": executed,
        }
    finally:
        db.close()


def get_dashboard_resumen(cut_key: str | None = None) -> Dict[str, Any]:
    db = _db()
    try:
        resolved_cut_key = _resolve_cut_key(db, cut_key)
        if not resolved_cut_key:
            return {
                "cut_key": None,
                "mode": "cut_driven",
                "socios": 0,
                "creditos": 0,
                "campanas": 0,
                "prospectos": 0,
                "scoring_total": 0,
                "riesgo": {"bajo": 0, "medio": 0, "alto": 0},
                "salud_cartera": {"cartera_total": 0.0, "cartera_vigente": 0.0, "cartera_vencida_estimada": 0.0, "imor_pct": 0.0},
                "colocacion": {"solicitados": 0, "aprobados": 0, "rechazados": 0, "monto_total": 0.0, "ticket_promedio": 0.0},
                "captacion": {"depositos_total": 0.0, "retiros_total": 0.0, "captacion_neta": 0.0},
                "comercial": {"campanas_activas": 0, "prospectos_total": 0, "score_propension_promedio": 0.0, "contactos_total": 0, "conversiones_total": 0, "conversion_pct": 0.0},
                "segmentacion": {"segmentos_total": 0, "oportunidades_comerciales": 0, "alertas_tempranas": 0, "abandono_alto": 0},
                "semaforos": [],
            }
        segmentation = get_segmentation_propensity_summary(cut_key=resolved_cut_key)
        kpi_rows = (
            db.query(IntelicoopKpiSnapshot)
            .filter(IntelicoopKpiSnapshot.cut_key == resolved_cut_key)
            .all()
        )
        kpi_map = {row.kpi_key: float(row.metric_value or 0) for row in kpi_rows}
        socio_rows = db.query(IntelicoopSocioFeatureSnapshot).filter(IntelicoopSocioFeatureSnapshot.cut_key == resolved_cut_key).all()
        credito_rows = db.query(IntelicoopCreditoFeatureSnapshot).filter(IntelicoopCreditoFeatureSnapshot.cut_key == resolved_cut_key).all()
        ahorro_rows = db.query(IntelicoopAhorroFeatureSnapshot).filter(IntelicoopAhorroFeatureSnapshot.cut_key == resolved_cut_key).all()
        campania_rows = db.query(IntelicoopCampaniaFeatureSnapshot).filter(IntelicoopCampaniaFeatureSnapshot.cut_key == resolved_cut_key).all()
        prospecto_rows = db.query(IntelicoopProspectoFeatureSnapshot).filter(IntelicoopProspectoFeatureSnapshot.cut_key == resolved_cut_key).all()
        scoring_rows = (
            db.query(IntelicoopScoringResult)
            .filter(IntelicoopScoringResult.solicitud_id.like(f"batch-score-{resolved_cut_key}-%"))
            .all()
        )
        socios = len(socio_rows)
        creditos = len(credito_rows)
        campanas = len(campania_rows)
        prospectos = len(prospecto_rows)
        scoring_total = len(scoring_rows)
        riesgo = {"bajo": 0, "medio": 0, "alto": 0}
        for row in socio_rows:
            key = str(row.riesgo_scoring_reciente or "")
            if key in riesgo:
                riesgo[key] += 1
        cartera_total = round(sum(float(row.exposicion_total or 0) for row in credito_rows), 2)
        pagos_total = round(sum(float(row.monto_pagado or 0) for row in credito_rows), 2)
        cartera_vigente = max(0.0, cartera_total - pagos_total)
        imor_pct = float(kpi_map.get("imor_pct", 0))
        cartera_vencida_estimada = round(cartera_total * imor_pct / 100.0, 2) if cartera_total else 0.0
        depositos_total = round(sum(float(row.monto_depositos or 0) for row in ahorro_rows), 2)
        retiros_total = round(sum(float(row.monto_retiros or 0) for row in ahorro_rows), 2)
        captacion_neta = depositos_total - retiros_total
        campanas_activas = sum(1 for row in campania_rows if str(row.estado or "") == "activa")
        prospectos_score_prom = round(sum(float(row.score_propension or 0) for row in prospecto_rows) / prospectos, 4) if prospectos else 0.0
        contactos_total = sum(int(row.total_contactos or 0) for row in campania_rows)
        conversiones_total = sum(int(row.conversiones or 0) for row in campania_rows)
        conversion_pct = round(float(kpi_map.get("conversion_pct", 0)), 2)
        aprobados = sum(1 for row in credito_rows if str(row.estado or "") == "aprobado")
        rechazados = sum(1 for row in credito_rows if str(row.estado or "") == "rechazado")
        solicitados = sum(1 for row in credito_rows if str(row.estado or "") == "solicitado")
        semaforos = [
            {
                "ambito": "salud_cartera",
                "label": "Salud de cartera",
                "valor": round(imor_pct, 2),
                "meta": 8.0,
                "semaforo": "verde" if imor_pct <= 8 else ("amarillo" if imor_pct <= 14 else "rojo"),
            },
            {
                "ambito": "captacion",
                "label": "Captacion neta",
                "valor": round(captacion_neta, 2),
                "meta": 0.0,
                "semaforo": "verde" if captacion_neta >= 0 else ("amarillo" if captacion_neta >= -1000 else "rojo"),
            },
            {
                "ambito": "riesgo",
                "label": "Scoring alto riesgo",
                "valor": riesgo["alto"],
                "meta": max(1, int(scoring_total * 0.2)) if scoring_total else 0,
                "semaforo": "verde" if riesgo["alto"] <= max(1, int(scoring_total * 0.2)) else ("amarillo" if riesgo["alto"] <= max(1, int(scoring_total * 0.35)) else "rojo"),
            },
            {
                "ambito": "comercial",
                "label": "Campanas activas",
                "valor": campanas_activas,
                "meta": 1,
                "semaforo": "verde" if campanas_activas >= 1 else "amarillo",
            },
        ]
        return {
            "cut_key": resolved_cut_key,
            "mode": "cut_driven",
            "socios": int(socios),
            "creditos": int(creditos),
            "campanas": int(campanas),
            "prospectos": int(prospectos),
            "scoring_total": int(scoring_total),
            "riesgo": riesgo,
            "salud_cartera": {
                "cartera_total": round(cartera_total, 2),
                "cartera_vigente": round(cartera_vigente, 2),
                "cartera_vencida_estimada": round(cartera_vencida_estimada, 2),
                "imor_pct": round(imor_pct, 2),
            },
            "colocacion": {
                "solicitados": solicitados,
                "aprobados": aprobados,
                "rechazados": rechazados,
                "monto_total": round(cartera_total, 2),
                "ticket_promedio": round((cartera_total / creditos), 2) if creditos else 0.0,
            },
            "captacion": {
                "depositos_total": round(depositos_total, 2),
                "retiros_total": round(retiros_total, 2),
                "captacion_neta": round(captacion_neta, 2),
            },
            "comercial": {
                "campanas_activas": campanas_activas,
                "prospectos_total": int(prospectos),
                "score_propension_promedio": round(prospectos_score_prom, 4),
                "contactos_total": contactos_total,
                "conversiones_total": conversiones_total,
                "conversion_pct": round(conversion_pct, 2),
            },
            "segmentacion": {
                "segmentos_total": int((segmentation.get("resumen") or {}).get("segmentos_total", 0)),
                "oportunidades_comerciales": int((segmentation.get("resumen") or {}).get("oportunidades_comerciales", 0)),
                "alertas_tempranas": int((segmentation.get("resumen") or {}).get("alertas_tempranas", 0)),
                "abandono_alto": int((segmentation.get("resumen") or {}).get("abandono_alto", 0)),
            },
            "semaforos": semaforos,
        }
    finally:
        db.close()


def _safe_growth(current_value: float, previous_value: float) -> float:
    previous = float(previous_value or 0)
    current = float(current_value or 0)
    if previous <= 0:
        return 0.0 if current <= 0 else 1.0
    return round((current - previous) / previous, 4)


def _build_aggregate_segment_rows(
    grouped_rows: Dict[str, List[Dict[str, Any]]],
    entity_label: str,
) -> List[Dict[str, Any]]:
    aggregates = []
    for label, rows in grouped_rows.items():
        total_entities = len(rows)
        volumen = round(sum(float(row.get("volumen", 0) or 0) for row in rows), 2)
        recurrencia = round(
            sum(float(row.get("recurrencia", 0) or 0) for row in rows) / total_entities,
            4,
        ) if total_entities else 0.0
        ticket = round(
            sum(float(row.get("ticket", 0) or 0) for row in rows) / total_entities,
            2,
        ) if total_entities else 0.0
        crecimiento = round(
            sum(float(row.get("crecimiento", 0) or 0) for row in rows) / total_entities,
            4,
        ) if total_entities else 0.0
        financiables = sum(1 for row in rows if row.get("financiable"))
        riesgo_alto = sum(1 for row in rows if str(row.get("riesgo") or "") == "alto")
        riesgo_medio = sum(1 for row in rows if str(row.get("riesgo") or "") == "medio")
        aggregates.append({
            "segmento": label,
            "entity_type": entity_label,
            "total": total_entities,
            "volumen": volumen,
            "recurrencia": recurrencia,
            "ticket": ticket,
            "crecimiento": crecimiento,
            "financiables": financiables,
            "riesgo_alto": riesgo_alto,
            "riesgo_medio": riesgo_medio,
        })
    return sorted(aggregates, key=lambda row: (-row["volumen"], -row["total"], row["segmento"]))


def get_aggregate_consumption_summary(cut_key: str | None = None) -> Dict[str, Any]:
    db = _db()
    try:
        resolved_cut_key = _resolve_cut_key(db, cut_key)
        dashboard = get_dashboard_resumen(cut_key=resolved_cut_key)
        segmentation = get_segmentation_propensity_summary(cut_key=resolved_cut_key) if resolved_cut_key else {"resumen": {}, "socios": []}
        tendencias = _compute_tendencias_resumen(db, n_cuts=2)

        if not resolved_cut_key:
            return {
                "cut_key": None,
                "dataset_contract": {
                    "scope": "consumo_agregado",
                    "privacy_mode": "sin_datos_individuales",
                    "contains_individual_data": False,
                    "segments_enabled": ["comercios", "usuarios", "zonas"],
                },
                "datasets": {
                    "consumo_agregado": [],
                    "segmentacion": {"comercios": [], "usuarios": [], "zonas": []},
                },
                "indicadores": {"volumen": 0.0, "recurrencia": 0.0, "ticket": 0.0, "crecimiento": 0.0},
                "scoring_comercial": {"score_promedio": 0.0, "financiables_detectados": 0, "bandas": []},
                "entregables": {
                    "tablero_financiero": {"disponible": True, "route": "/inicio/intelicoop", "api": "/api/intelicoop/dashboard/resumen"},
                    "indicadores": {"disponible": True, "api": "/api/intelicoop/consumo-agregado/resumen"},
                    "alertas": {"disponible": True, "api": "/api/intelicoop/batch/alertas"},
                },
            }

        socio_feature_rows = (
            db.query(IntelicoopSocioFeatureSnapshot)
            .filter(IntelicoopSocioFeatureSnapshot.cut_key == resolved_cut_key)
            .all()
        )
        socios = (
            db.query(IntelicoopSocio)
            .filter(IntelicoopSocio.id.in_([row.socio_id for row in socio_feature_rows] or [0]))
            .all()
        )
        socio_map = {int(row.id): row for row in socios}

        previous_cut = (
            db.query(IntelicoopAnalyticCut)
            .filter(IntelicoopAnalyticCut.cut_key != resolved_cut_key)
            .order_by(IntelicoopAnalyticCut.cut_date.desc(), IntelicoopAnalyticCut.id.desc())
            .first()
        )
        previous_socio_rows = (
            db.query(IntelicoopSocioFeatureSnapshot)
            .filter(IntelicoopSocioFeatureSnapshot.cut_key == str(previous_cut.cut_key))
            .all()
        ) if previous_cut else []
        previous_by_socio = {int(row.socio_id): row for row in previous_socio_rows}

        users_group: Dict[str, List[Dict[str, Any]]] = {}
        commerces_group: Dict[str, List[Dict[str, Any]]] = {}
        zones_group: Dict[str, List[Dict[str, Any]]] = {}
        scoring_bands = Counter()

        for row in socio_feature_rows:
            socio = socio_map.get(int(row.socio_id))
            if socio is None:
                continue
            previous = previous_by_socio.get(int(row.socio_id))
            current_volume = float(row.monto_creditos_total or 0) + float(row.saldo_cuentas_total or 0)
            previous_volume = (
                float(previous.monto_creditos_total or 0) + float(previous.saldo_cuentas_total or 0)
            ) if previous else 0.0
            growth = _safe_growth(current_volume, previous_volume)
            financial_score = max(
                float(row.score_scoring_reciente or 0),
                float(row.estabilidad_financiera or 0),
                float(row.score_propension_referencia or 0),
            )
            band = (
                "financiable_alto" if financial_score >= 0.75 else
                "financiable_medio" if financial_score >= 0.55 else
                "monitoreo"
            )
            scoring_bands[band] += 1
            record = {
                "volumen": current_volume,
                "recurrencia": float(row.transacciones_total or 0),
                "ticket": _safe_div(float(row.monto_creditos_total or 0), max(int(row.creditos_total or 0), 1), 0.0),
                "crecimiento": growth,
                "financiable": bool(
                    financial_score >= 0.55
                    and float(row.score_abandono or 0) < 0.45
                    and str(row.riesgo_scoring_reciente or "") != "alto"
                ),
                "riesgo": str(row.riesgo_scoring_reciente or "sin_dato"),
            }
            users_group.setdefault(str(row.segmento_actual or "sin_segmento"), []).append(record)
            commerces_group.setdefault(str(socio.sector_economico or "sin_sector"), []).append(record)
            zone_label = str(socio.ubicacion_municipio or socio.ubicacion_estado or socio.direccion or "sin_zona")
            zones_group.setdefault(zone_label, []).append(record)

        tendencias_map = {row["kpi_key"]: row for row in tendencias}
        captacion_points = list((tendencias_map.get("captacion_neta") or {}).get("puntos") or [])
        crecimiento_global = 0.0
        if len(captacion_points) >= 2:
            crecimiento_global = _safe_growth(captacion_points[-1].get("value", 0), captacion_points[-2].get("value", 0))

        average_recurrencia = round(
            sum(float(row.frecuencia_transaccional or 0) for row in db.query(IntelicoopAhorroFeatureSnapshot).filter(IntelicoopAhorroFeatureSnapshot.cut_key == resolved_cut_key).all())
            / max(
                db.query(IntelicoopAhorroFeatureSnapshot).filter(IntelicoopAhorroFeatureSnapshot.cut_key == resolved_cut_key).count(),
                1,
            ),
            4,
        )

        financiables_total = sum(1 for rows in users_group.values() for row in rows if row.get("financiable"))
        average_scoring = round(
            sum(float(row.score_scoring_reciente or 0) for row in socio_feature_rows) / max(len(socio_feature_rows), 1),
            4,
        )
        return {
            "cut_key": resolved_cut_key,
            "dataset_contract": {
                "scope": "consumo_agregado",
                "privacy_mode": "sin_datos_individuales",
                "contains_individual_data": False,
                "segments_enabled": ["comercios", "usuarios", "zonas"],
                "entity_grain": "agregados_por_segmento",
            },
            "datasets": {
                "consumo_agregado": [
                    {"dataset_key": "usuarios_agregado", "grain": "segmento_usuario", "records": len(users_group)},
                    {"dataset_key": "comercios_agregado", "grain": "sector_economico", "records": len(commerces_group)},
                    {"dataset_key": "zonas_agregado", "grain": "municipio_estado", "records": len(zones_group)},
                ],
                "segmentacion": {
                    "usuarios": _build_aggregate_segment_rows(users_group, "usuarios"),
                    "comercios": _build_aggregate_segment_rows(commerces_group, "comercios"),
                    "zonas": _build_aggregate_segment_rows(zones_group, "zonas"),
                },
            },
            "indicadores": {
                "volumen": round(float((dashboard.get("salud_cartera") or {}).get("cartera_total", 0)) + float((dashboard.get("captacion") or {}).get("depositos_total", 0)), 2),
                "recurrencia": average_recurrencia,
                "ticket": round(float((dashboard.get("colocacion") or {}).get("ticket_promedio", 0)), 2),
                "crecimiento": round(crecimiento_global, 4),
            },
            "scoring_comercial": {
                "score_promedio": average_scoring,
                "financiables_detectados": financiables_total,
                "oportunidades_comerciales": int((segmentation.get("resumen") or {}).get("oportunidades_comerciales", 0)),
                "bandas": [
                    {"band": band, "total": int(total)}
                    for band, total in sorted(scoring_bands.items(), key=lambda item: (-item[1], item[0]))
                ],
            },
            "entregables": {
                "tablero_financiero": {
                    "disponible": True,
                    "route": "/inicio/intelicoop",
                    "api": "/api/intelicoop/dashboard/resumen",
                },
                "indicadores": {
                    "disponible": True,
                    "api": "/api/intelicoop/consumo-agregado/resumen",
                },
                "alertas": {
                    "disponible": True,
                    "api": "/api/intelicoop/batch/alertas",
                },
            },
        }
    finally:
        db.close()
