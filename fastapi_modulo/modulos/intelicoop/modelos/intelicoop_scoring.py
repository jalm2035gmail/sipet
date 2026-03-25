from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopContactoCampania,
    IntelicoopCredito,
    IntelicoopCuenta,
    IntelicoopHistorialPago,
    IntelicoopModelDriftSnapshot,
    IntelicoopScoringResult,
    IntelicoopSeguimientoCampania,
    IntelicoopSocio,
    IntelicoopTransaccion,
)


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "modelo_scoring.pkl"
)
MODEL_VERSION = "intelicoop_scoring_v1"
SCORING_TRAZA_VERSION = "intelicoop_traza_v1"
_SCORE_UMBRAL_APROBAR = 0.80
_SCORE_UMBRAL_EVALUAR = 0.55
EXPECTED_MODEL_FEATURES = ["ingreso_mensual", "deuda_actual", "antiguedad_meses"]
EXPECTED_MODEL_PERFORMANCE = {
    "auc": 0.74,
    "ks": 0.39,
    "gini": 0.48,
    "precision_aprobacion": 0.68,
    "recall_riesgo_alto": 0.63,
    "psi_max": 0.20,
    "csi_max": 0.20,
}
SEGMENT_THRESHOLDS = {
    "integral_fiel": {"aprobar": 0.82, "evaluar": 0.58},
    "crecimiento": {"aprobar": 0.80, "evaluar": 0.55},
    "ahorrador_activo": {"aprobar": 0.78, "evaluar": 0.54},
    "alerta_temprana": {"aprobar": 0.88, "evaluar": 0.66},
    "pasivo": {"aprobar": 0.84, "evaluar": 0.60},
    "default": {"aprobar": _SCORE_UMBRAL_APROBAR, "evaluar": _SCORE_UMBRAL_EVALUAR},
}
_MODEL: Any = None
_MODEL_LOADED = False
_MODEL_METADATA: Dict[str, Any] = {
    "version": MODEL_VERSION,
    "artifact_path": str(MODEL_PATH),
    "artifact_format": "joblib",
    "expected_features": EXPECTED_MODEL_FEATURES,
    "expected_performance": EXPECTED_MODEL_PERFORMANCE,
    "load_status": "pending",
    "load_error": "",
    "loaded_at": None,
    "artifact_checksum": "",
    "algoritmo": "reglas",
}


def _clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return float(numerator) / float(denominator) if denominator else default


def _normalize_positive(value: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return _clamp01(value / target)


def _normalize_negative(value: float, max_tolerated: float) -> float:
    if max_tolerated <= 0:
        return 1.0
    return _clamp01(1.0 - min(float(value), float(max_tolerated)) / float(max_tolerated))


def _stddev(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return math.sqrt(max(0.0, variance))


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_model() -> Any:
    global _MODEL, _MODEL_LOADED
    if _MODEL_LOADED:
        return _MODEL
    _MODEL_LOADED = True
    loaded_at = datetime.utcnow().isoformat()
    _MODEL_METADATA["loaded_at"] = loaded_at
    if not MODEL_PATH.exists():
        _MODEL = None
        _MODEL_METADATA.update({
            "load_status": "missing",
            "load_error": f"artifact_not_found:{MODEL_PATH}",
            "artifact_checksum": "",
            "algoritmo": "reglas",
        })
        return None
    try:
        import joblib

        _MODEL = joblib.load(MODEL_PATH)
        _MODEL_METADATA.update({
            "load_status": "loaded",
            "load_error": "",
            "artifact_checksum": _file_sha256(MODEL_PATH),
            "algoritmo": _MODEL.__class__.__name__ if _MODEL is not None else "reglas",
        })
    except Exception as exc:
        _MODEL = None
        _MODEL_METADATA.update({
            "load_status": "error",
            "load_error": f"{exc.__class__.__name__}: {exc}",
            "artifact_checksum": "",
            "algoritmo": "reglas",
        })
    return _MODEL


def get_model_artifact_metadata() -> Dict[str, Any]:
    _load_model()
    return dict(_MODEL_METADATA)


def _fallback_score(ingreso_mensual: float, deuda_actual: float, antiguedad_meses: int) -> float:
    if ingreso_mensual <= 0:
        return 0.15
    ratio = deuda_actual / ingreso_mensual if ingreso_mensual else 1.0
    ratio_score = max(0.0, min(1.0, 1.0 - ratio))
    antiguedad_score = max(0.0, min(1.0, antiguedad_meses / 36.0))
    return round((ratio_score * 0.75) + (antiguedad_score * 0.25), 4)


def _predict_model_score(model: Any, features: List[float]) -> Optional[float]:
    try:
        if hasattr(model, "predict_proba"):
            result = model.predict_proba([features])[0]
            return float(result[1]) if len(result) > 1 else float(result[0])
        if hasattr(model, "predict"):
            return float(model.predict([features])[0])
    except Exception:
        return None
    return None


def _calibrate_probability(raw_score: float, motor: str) -> float:
    score = max(0.0, min(1.0, float(raw_score)))
    if motor != "modelo_ml":
        return round(0.5 + (score - 0.5) * 0.75, 4)
    centered = (score - 0.5) * 2.4
    calibrated = 1.0 / (1.0 + math.exp(-centered))
    return round(calibrated, 4)


def _get_db_session():
    current_host = str(core_db.get_request_host() or "").strip()
    session_factory = core_db.get_session_factory_for_host(current_host)
    return session_factory()


def _model_stability_snapshot() -> Dict[str, Any]:
    db = None
    try:
        db = _get_db_session()
        rows = (
            db.query(IntelicoopModelDriftSnapshot)
            .filter(IntelicoopModelDriftSnapshot.model_version == MODEL_VERSION)
            .order_by(IntelicoopModelDriftSnapshot.created_at.desc(), IntelicoopModelDriftSnapshot.id.desc())
            .limit(8)
            .all()
        )
        if not rows:
            return {"drift_score": 0.0, "psi": 0.0, "csi": 0.0, "stability": 0.85}
        drift_score = sum(float(row.drift_score or 0) for row in rows) / len(rows)
        psi = min(1.0, drift_score * 0.9)
        csi = min(1.0, drift_score * 0.75)
        stability = max(0.0, 1.0 - max(psi, csi, drift_score))
        return {
            "drift_score": round(drift_score, 4),
            "psi": round(psi, 4),
            "csi": round(csi, 4),
            "stability": round(stability, 4),
        }
    except Exception:
        return {"drift_score": 0.0, "psi": 0.0, "csi": 0.0, "stability": 0.75}
    finally:
        if db is not None:
            db.close()


def _data_completeness(inputs: Dict[str, Any], socio_context: Dict[str, Any]) -> float:
    observed = [
        1.0 if float(inputs.get("ingreso_mensual", 0) or 0) > 0 else 0.0,
        1.0 if inputs.get("deuda_actual") is not None else 0.0,
        1.0 if int(inputs.get("antiguedad_meses", 0) or 0) > 0 else 0.0,
        1.0 if float(socio_context.get("tasa_cumplimiento_pagos", 0) or 0) > 0 else 0.0,
        1.0 if float(socio_context.get("saldo_promedio", 0) or 0) > 0 else 0.0,
        1.0 if float(socio_context.get("transacciones_por_mes", 0) or 0) > 0 else 0.0,
        1.0 if int(socio_context.get("numero_productos", 0) or 0) > 0 else 0.0,
        1.0 if int(socio_context.get("dias_como_socio", 0) or 0) > 0 else 0.0,
        1.0 if int(socio_context.get("participacion_campanas", 0) or 0) > 0 else 0.0,
    ]
    return round(sum(observed) / len(observed), 4)


def _segment_thresholds(segmento: str) -> Dict[str, float]:
    return SEGMENT_THRESHOLDS.get(segmento, SEGMENT_THRESHOLDS["default"])


def _compute_confianza(
    score: float,
    motor: str,
    inputs: Dict[str, Any],
    socio_context: Dict[str, Any],
) -> Tuple[float, Dict[str, Any]]:
    segmento = str(socio_context.get("segmento_actual") or "default")
    thresholds = _segment_thresholds(segmento)
    calibrated_probability = _calibrate_probability(score, motor)
    completeness = _data_completeness(inputs, socio_context)
    stability = _model_stability_snapshot()
    threshold_gap = min(
        abs(calibrated_probability - float(thresholds["evaluar"])),
        abs(calibrated_probability - float(thresholds["aprobar"])),
    )
    threshold_confidence = min(1.0, threshold_gap / 0.25)
    confidence = (
        calibrated_probability * 0.35
        + completeness * 0.20
        + float(stability["stability"]) * 0.25
        + threshold_confidence * 0.20
    )
    return round(max(0.0, min(1.0, confidence)), 4), {
        "probabilidad_calibrada": calibrated_probability,
        "completitud_datos": completeness,
        "drift_modelo": float(stability["drift_score"]),
        "psi": float(stability["psi"]),
        "csi": float(stability["csi"]),
        "estabilidad_feature_space": float(stability["stability"]),
        "threshold_segmento": thresholds,
        "segmento_threshold": segmento,
        "threshold_confidence": round(threshold_confidence, 4),
    }


def _collect_socio_context(socio_id: Optional[int], credito_id: Optional[int]) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "dias_como_socio": 0,
        "creditos_previos": 0,
        "creditos_total": 0,
        "creditos_en_mora": 0,
        "dias_en_mora": 0,
        "historial_pagos_total": 0,
        "porcentaje_pagado_credito_anterior": 0.0,
        "tasa_cumplimiento_pagos": 0.0,
        "depositos_total": 0.0,
        "retiros_total": 0.0,
        "frecuencia_depositos": 0.0,
        "saldo_promedio": 0.0,
        "saldo_variabilidad": 0.0,
        "transacciones_por_mes": 0.0,
        "frecuencia_retiros_vs_depositos": 0.0,
        "recurrencia_ahorro": 0.0,
        "participacion_campanas": 0,
        "respuesta_comercial_historica": 0.0,
        "numero_productos": 0,
        "cuentas_total": 0,
        "depositos_count": 0,
        "retiros_count": 0,
    }
    if not socio_id:
        return defaults

    db = None
    try:
        db = _get_db_session()
        now = datetime.utcnow()
        socio = db.query(IntelicoopSocio).filter(IntelicoopSocio.id == int(socio_id)).first()
        if socio and socio.fecha_registro:
            defaults["dias_como_socio"] = max(0, (now - socio.fecha_registro).days)

        creditos = (
            db.query(IntelicoopCredito)
            .filter(IntelicoopCredito.socio_id == int(socio_id))
            .order_by(IntelicoopCredito.id.desc())
            .all()
        )
        defaults["creditos_total"] = len(creditos)
        previous_creditos = [row for row in creditos if credito_id is None or int(row.id) != int(credito_id)]
        defaults["creditos_previos"] = len(previous_creditos)

        overdue_days: List[int] = []
        for row in creditos:
            estado = str(row.estado or "")
            if estado == "mora":
                if row.fecha_vencimiento:
                    overdue_days.append(max(0, (now - row.fecha_vencimiento).days))
                else:
                    overdue_days.append(30)
        defaults["creditos_en_mora"] = len(overdue_days)
        defaults["dias_en_mora"] = max(overdue_days) if overdue_days else 0

        total_pagado_creditos = 0.0
        total_monto_creditos = 0.0
        porcentaje_pagado_credito_anterior = 0.0
        historial_pagos_total = 0
        if previous_creditos:
            previous_ids = [int(row.id) for row in previous_creditos]
            pagos = (
                db.query(IntelicoopHistorialPago)
                .filter(IntelicoopHistorialPago.credito_id.in_(previous_ids))
                .all()
            )
            pagos_by_credito: Dict[int, float] = {}
            for pago in pagos:
                historial_pagos_total += 1
                pagos_by_credito[int(pago.credito_id)] = pagos_by_credito.get(int(pago.credito_id), 0.0) + float(pago.monto or 0)
            total_pagado_creditos = sum(pagos_by_credito.values())
            total_monto_creditos = sum(float(row.monto or 0) for row in previous_creditos)
            latest_previous = previous_creditos[0]
            latest_paid = pagos_by_credito.get(int(latest_previous.id), 0.0)
            porcentaje_pagado_credito_anterior = _clamp01(_safe_div(latest_paid, float(latest_previous.monto or 0), 0.0))
        defaults["historial_pagos_total"] = historial_pagos_total
        defaults["tasa_cumplimiento_pagos"] = _clamp01(_safe_div(total_pagado_creditos, total_monto_creditos, 0.0))
        defaults["porcentaje_pagado_credito_anterior"] = porcentaje_pagado_credito_anterior

        cuentas = db.query(IntelicoopCuenta).filter(IntelicoopCuenta.socio_id == int(socio_id)).all()
        account_ids = [int(row.id) for row in cuentas]
        saldos = [float(row.saldo or 0) for row in cuentas]
        defaults["cuentas_total"] = len(cuentas)
        defaults["saldo_promedio"] = round(sum(saldos) / len(saldos), 4) if saldos else 0.0
        defaults["saldo_variabilidad"] = round(_stddev(saldos), 4) if saldos else 0.0

        depositos_count = 0
        retiros_count = 0
        depositos_total = 0.0
        retiros_total = 0.0
        transacciones_total = 0
        months_with_deposit = set()
        earliest_tx = None
        if account_ids:
            txs = (
                db.query(IntelicoopTransaccion)
                .filter(IntelicoopTransaccion.cuenta_id.in_(account_ids))
                .all()
            )
            transacciones_total = len(txs)
            for tx in txs:
                tx_date = tx.fecha or now
                earliest_tx = tx_date if earliest_tx is None else min(earliest_tx, tx_date)
                monto = float(tx.monto or 0)
                if str(tx.tipo or "") == "deposito":
                    depositos_count += 1
                    depositos_total += monto
                    months_with_deposit.add(tx_date.strftime("%Y-%m"))
                elif str(tx.tipo or "") == "retiro":
                    retiros_count += 1
                    retiros_total += monto
        months_span = 1
        if earliest_tx is not None:
            months_span = max(
                1,
                (now.year - earliest_tx.year) * 12 + (now.month - earliest_tx.month) + 1,
            )
        defaults["depositos_count"] = depositos_count
        defaults["retiros_count"] = retiros_count
        defaults["depositos_total"] = round(depositos_total, 4)
        defaults["retiros_total"] = round(retiros_total, 4)
        defaults["frecuencia_depositos"] = round(depositos_count / months_span, 4)
        defaults["transacciones_por_mes"] = round(transacciones_total / months_span, 4)
        defaults["frecuencia_retiros_vs_depositos"] = round(_safe_div(retiros_count, depositos_count, 0.0), 4)
        defaults["recurrencia_ahorro"] = round(len(months_with_deposit) / months_span, 4) if months_span else 0.0

        participacion_campanas = int(
            db.query(func.count(IntelicoopContactoCampania.id))
            .filter(IntelicoopContactoCampania.socio_id == int(socio_id))
            .scalar()
            or 0
        )
        conversiones = int(
            db.query(func.count(IntelicoopSeguimientoCampania.id))
            .filter(
                IntelicoopSeguimientoCampania.socio_id == int(socio_id),
                IntelicoopSeguimientoCampania.conversion == 1,
            )
            .scalar()
            or 0
        )
        defaults["participacion_campanas"] = participacion_campanas
        defaults["respuesta_comercial_historica"] = round(_safe_div(conversiones, participacion_campanas, 0.0), 4)
        defaults["numero_productos"] = len(cuentas) + len([row for row in creditos if str(row.estado or "") in {"solicitado", "aprobado", "vigente", "mora", "reestructurado"}])
        defaults["segmento_actual"] = str(socio.segmento or "default") if socio else "default"
        return defaults
    except Exception:
        return defaults
    finally:
        if db is not None:
            db.close()


def _build_enhanced_feature_scores(
    ingreso_mensual: float,
    deuda_actual: float,
    antiguedad_meses: int,
    socio_context: Dict[str, Any],
) -> Dict[str, Any]:
    ratio_deuda_ingreso = round(_safe_div(deuda_actual, ingreso_mensual, 1.0), 4) if ingreso_mensual > 0 else 1.0
    capacidad_score = _clamp01((1.0 - min(ratio_deuda_ingreso, 1.0)) * 0.72 + min(1.0, antiguedad_meses / 48.0) * 0.28)
    creditos_previos = float(socio_context.get("creditos_previos", 0))
    historial_pagos = _clamp01(float(socio_context.get("tasa_cumplimiento_pagos", 0)))
    pct_pagado_credito_anterior = _clamp01(float(socio_context.get("porcentaje_pagado_credito_anterior", 0)))
    if creditos_previos <= 0:
        historial_pagos = 0.55
        pct_pagado_credito_anterior = 0.5
        creditos_previos_score = 0.5
    else:
        creditos_previos_score = _normalize_positive(creditos_previos, 3)
    component_scores = {
        "capacidad_pago": capacidad_score,
        "historial_pagos": historial_pagos,
        "creditos_previos": creditos_previos_score,
        "mora": _normalize_negative(float(socio_context.get("dias_en_mora", 0)), 90),
        "frecuencia_depositos": _normalize_positive(float(socio_context.get("frecuencia_depositos", 0)), 4),
        "saldo_promedio": _normalize_positive(float(socio_context.get("saldo_promedio", 0)), 4000),
        "transacciones_mes": _normalize_positive(float(socio_context.get("transacciones_por_mes", 0)), 8),
        "participacion_campanas": _normalize_positive(float(socio_context.get("participacion_campanas", 0)), 4),
        "antiguedad_socio": _normalize_positive(float(socio_context.get("dias_como_socio", 0)), 720),
        "productos": _normalize_positive(float(socio_context.get("numero_productos", 0)), 4),
        "variabilidad_saldo": _normalize_negative(float(socio_context.get("saldo_variabilidad", 0)), 2500),
        "pct_pagado_credito_anterior": pct_pagado_credito_anterior,
        "retiros_vs_depositos": _normalize_negative(float(socio_context.get("frecuencia_retiros_vs_depositos", 0)), 1.5),
        "recurrencia_ahorro": _clamp01(float(socio_context.get("recurrencia_ahorro", 0))),
        "respuesta_comercial": _clamp01(float(socio_context.get("respuesta_comercial_historica", 0))),
    }
    weights = {
        "capacidad_pago": 0.22,
        "historial_pagos": 0.14,
        "creditos_previos": 0.05,
        "mora": 0.11,
        "frecuencia_depositos": 0.05,
        "saldo_promedio": 0.04,
        "transacciones_mes": 0.05,
        "participacion_campanas": 0.03,
        "antiguedad_socio": 0.08,
        "productos": 0.05,
        "variabilidad_saldo": 0.04,
        "pct_pagado_credito_anterior": 0.05,
        "retiros_vs_depositos": 0.03,
        "recurrencia_ahorro": 0.04,
        "respuesta_comercial": 0.02,
    }
    enhanced_score = 0.0
    impacts: List[Dict[str, Any]] = []
    for key, weight in weights.items():
        component = _clamp01(component_scores.get(key, 0))
        enhanced_score += component * weight
        impacts.append(
            {
                "feature": key,
                "score": component,
                "weight": weight,
                "impact": round((component - 0.5) * weight, 4),
            }
        )
    return {
        "ratio_deuda_ingreso": ratio_deuda_ingreso,
        "component_scores": component_scores,
        "weights": weights,
        "impacts": sorted(impacts, key=lambda item: abs(item["impact"]), reverse=True),
        "enhanced_score": _clamp01(enhanced_score),
    }


def _build_explicacion(
    score: float,
    motor: str,
    enriched: Dict[str, Any],
    socio_context: Dict[str, Any],
) -> Dict[str, Any]:
    labels = {
        "capacidad_pago": "capacidad de pago",
        "historial_pagos": "historial de pagos",
        "creditos_previos": "experiencia crediticia previa",
        "mora": "dias en mora",
        "frecuencia_depositos": "frecuencia de depositos",
        "saldo_promedio": "saldo promedio",
        "transacciones_mes": "transacciones por mes",
        "participacion_campanas": "participacion en campanas",
        "antiguedad_socio": "antiguedad como socio",
        "productos": "numero de productos",
        "variabilidad_saldo": "variabilidad del saldo",
        "pct_pagado_credito_anterior": "porcentaje pagado del credito anterior",
        "retiros_vs_depositos": "frecuencia de retiros vs depositos",
        "recurrencia_ahorro": "recurrencia del ahorro",
        "respuesta_comercial": "respuesta comercial historica",
    }
    razones: List[str] = []
    reglas: List[Dict[str, Any]] = []
    top_factores: List[Dict[str, Any]] = []
    total_abs_impact = sum(abs(float(item.get("impact", 0) or 0)) for item in enriched["impacts"]) or 1.0
    shap_values: Dict[str, float] = {}
    importancia_variables: List[Dict[str, Any]] = []
    for item in enriched["impacts"]:
        feature_key = str(item["feature"])
        label = labels.get(feature_key, feature_key)
        impact = round(float(item.get("impact", 0) or 0), 4)
        importancia = round(abs(impact) / total_abs_impact, 4)
        shap_values[feature_key] = impact
        importancia_variables.append(
            {
                "feature": feature_key,
                "label": label,
                "importance": importancia,
                "impact": impact,
                "direccion": "positiva" if impact >= 0 else "negativa",
            }
        )
    importancia_variables = sorted(importancia_variables, key=lambda item: item["importance"], reverse=True)

    for item in enriched["impacts"][:5]:
        label = labels.get(item["feature"], item["feature"])
        if item["impact"] >= 0:
            razones.append(f"{label.capitalize()} favorable: fortalece el perfil.")
        else:
            razones.append(f"{label.capitalize()} debil: presiona el riesgo del perfil.")
        reglas.append(
            {
                "regla": item["feature"],
                "impacto": "positivo" if item["impact"] >= 0 else "negativo",
                "peso": item["weight"],
                "score_feature": item["score"],
            }
        )
        top_factores.append(
            {
                "feature": item["feature"],
                "label": label,
                "impact": round(float(item["impact"]), 4),
                "direccion": "positivo" if item["impact"] >= 0 else "negativo",
            }
        )

    if float(socio_context.get("dias_en_mora", 0)) > 0:
        razones.append(f"Se detectan {int(socio_context['dias_en_mora'])} dias estimados en mora.")
    if float(socio_context.get("historial_pagos_total", 0)) == 0:
        razones.append("Sin historial de pagos suficiente: la evaluacion depende mas de capacidad y comportamiento de ahorro.")

    if score >= _SCORE_UMBRAL_APROBAR:
        razones.append(f"Score {score:.4f} ≥ {_SCORE_UMBRAL_APROBAR}: perfil aprobable.")
    elif score >= _SCORE_UMBRAL_EVALUAR:
        razones.append(f"Score {score:.4f} entre {_SCORE_UMBRAL_EVALUAR} y {_SCORE_UMBRAL_APROBAR}: requiere revision.")
    else:
        razones.append(f"Score {score:.4f} < {_SCORE_UMBRAL_EVALUAR}: perfil de alto riesgo.")

    reglas.append({"regla": "motor_utilizado", "valor": motor, "impacto": "informativo", "peso": 0})
    return {
        "razones": razones[:7],
        "reglas_aplicadas": reglas,
        "importancia_variables": importancia_variables[:10],
        "shap_values": shap_values,
        "top_factores_por_score": top_factores[:5],
        "explicacion_local_socio": {
            "segmento": str(socio_context.get("segmento_actual") or "sin_segmento"),
            "score": round(float(score), 4),
            "motor": motor,
            "mensaje": razones[0] if razones else "Sin explicacion disponible.",
            "factores_clave": top_factores[:3],
        },
    }


def evaluate_scoring(
    ingreso_mensual: float,
    deuda_actual: float,
    antiguedad_meses: int,
) -> Tuple[float, str, str, str]:
    result = evaluate_scoring_v2(
        ingreso_mensual=ingreso_mensual,
        deuda_actual=deuda_actual,
        antiguedad_meses=antiguedad_meses,
    )
    return result["score"], result["recomendacion"], result["riesgo"], result["model_version"]


def evaluate_scoring_v2(
    ingreso_mensual: float,
    deuda_actual: float,
    antiguedad_meses: int,
    solicitud_id: str = "",
    socio_id: Optional[int] = None,
    credito_id: Optional[int] = None,
) -> Dict[str, Any]:
    t0 = time.monotonic()
    ingreso_f = float(ingreso_mensual)
    deuda_f = float(deuda_actual)
    antiguedad_i = int(antiguedad_meses)

    socio_context = _collect_socio_context(socio_id=socio_id, credito_id=credito_id)
    enriched = _build_enhanced_feature_scores(
        ingreso_mensual=ingreso_f,
        deuda_actual=deuda_f,
        antiguedad_meses=antiguedad_i,
        socio_context=socio_context,
    )

    model = _load_model()
    base_features = [ingreso_f, deuda_f, antiguedad_i]
    model_score = _predict_model_score(model, base_features) if model is not None else None
    enhanced_score = float(enriched["enhanced_score"])

    if model_score is None:
        model_score = _fallback_score(*base_features)
        score = enhanced_score
        motor = "reglas"
    else:
        model_score = _clamp01(model_score)
        score = _clamp01((model_score * 0.30) + (enhanced_score * 0.70))
        motor = "modelo_ml"

    if score >= _SCORE_UMBRAL_APROBAR:
        recomendacion, riesgo = "aprobar", "bajo"
    elif score >= _SCORE_UMBRAL_EVALUAR:
        recomendacion, riesgo = "evaluar", "medio"
    else:
        recomendacion, riesgo = "rechazar", "alto"

    tiempo_ms = max(1, int((time.monotonic() - t0) * 1000))
    inputs = {
        "ingreso_mensual": ingreso_f,
        "deuda_actual": deuda_f,
        "antiguedad_meses": antiguedad_i,
    }
    confianza, confianza_componentes = _compute_confianza(
        score=score,
        motor=motor,
        inputs=inputs,
        socio_context=socio_context,
    )
    explicacion = _build_explicacion(score=score, motor=motor, enriched=enriched, socio_context=socio_context)

    return {
        "score": score,
        "recomendacion": recomendacion,
        "riesgo": riesgo,
        "model_version": MODEL_VERSION,
        "confianza": confianza,
        "motor": motor,
        "tiempo_ms": tiempo_ms,
        "inputs": inputs,
        "features_calculados": {
            "ratio_deuda_ingreso": enriched["ratio_deuda_ingreso"],
            "antiguedad_normalizada": round(min(1.0, antiguedad_i / 48.0), 4),
            "ingreso_positivo": ingreso_f > 0,
            "score_modelo_base": _clamp01(model_score),
            "score_reglas_enriquecidas": enhanced_score,
            **confianza_componentes,
            **enriched["component_scores"],
            **socio_context,
        },
        "razones": explicacion["razones"],
        "reglas_aplicadas": explicacion["reglas_aplicadas"],
        "explainability": {
            "importancia_variables": explicacion["importancia_variables"],
            "shap_values": explicacion["shap_values"],
            "top_factores_por_score": explicacion["top_factores_por_score"],
            "explicacion_local_socio": explicacion["explicacion_local_socio"],
        },
        "solicitud_id": solicitud_id,
        "socio_id": socio_id,
        "credito_id": credito_id,
        "traza_version": SCORING_TRAZA_VERSION,
    }


def summarize_scoring(rows: list[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    por_riesgo = {"bajo": 0, "medio": 0, "alto": 0}
    por_recomendacion = {"aprobar": 0, "evaluar": 0, "rechazar": 0}
    score_sum = 0.0
    recientes = []
    for row in rows:
        score = float(row.get("score", 0) or 0)
        score_sum += score
        riesgo = str(row.get("riesgo", "")).lower()
        recomendacion = str(row.get("recomendacion", "")).lower()
        if riesgo in por_riesgo:
            por_riesgo[riesgo] += 1
        if recomendacion in por_recomendacion:
            por_recomendacion[recomendacion] += 1
        recientes.append(
            {
                "id": row.get("id"),
                "solicitud_id": row.get("solicitud_id"),
                "socio_id": row.get("socio_id"),
                "credito_id": row.get("credito_id"),
                "score": score,
                "recomendacion": recomendacion,
                "riesgo": riesgo,
                "model_version": row.get("model_version", MODEL_VERSION),
                "fecha_creacion": row.get("fecha_creacion"),
            }
        )
    recientes = list(reversed(recientes[-5:]))
    return {
        "total_inferencias": total,
        "score_promedio": round(score_sum / total, 4) if total else 0.0,
        "por_riesgo": por_riesgo,
        "por_recomendacion": por_recomendacion,
        "recientes": recientes,
    }
