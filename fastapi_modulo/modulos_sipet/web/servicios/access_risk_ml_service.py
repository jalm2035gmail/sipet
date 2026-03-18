from __future__ import annotations

import ipaddress
import os
from datetime import datetime, timedelta
from typing import Any

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except Exception:  # pragma: no cover
    ColumnTransformer = None
    OneHotEncoder = None
    Pipeline = None
    RandomForestClassifier = None
    StandardScaler = None
    cross_val_score = None

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.modelos.db_models import WebLoginAttempt, WebSecurityEvent

MODEL_PATH = (
    os.environ.get("WEB_ACCESS_RISK_MODEL_PATH")
    or os.path.join(os.path.dirname(__file__), "..", "runtime", "access_risk_model.joblib")
).strip()
MODEL_VERSION = 1

# ── Caché del modelo en memoria ───────────────────────────────────────────────
# El modelo se carga desde disco una sola vez por proceso.
# Se invalida automáticamente cuando el mtime del archivo cambia,
# es decir, después de cada reentrenamiento via Celery.
_MODEL_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_MTIME: dict[str, float] = {}


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


def _metadata_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    raw = str(value or "").strip()
    if not raw:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.utcnow()


def _ip_octet_bucket(ip_value: str) -> int:
    raw = str(ip_value or "").strip()
    if not raw:
        return 0
    try:
        ip_obj = ipaddress.ip_address(raw)
        packed = int(ip_obj)
        return int(packed % 256)
    except ValueError:
        return sum(ord(ch) for ch in raw) % 256


def _user_agent_family(user_agent: str) -> str:
    raw = str(user_agent or "").lower()
    if "mobile" in raw or "android" in raw or "iphone" in raw:
        return "mobile"
    if "chrome" in raw:
        return "chrome"
    if "firefox" in raw:
        return "firefox"
    if "safari" in raw:
        return "safari"
    return "other"


def _risk_label(score: float) -> str:
    if score >= 0.78:
        return "sospechoso"
    if score >= 0.42:
        return "inusual"
    return "normal"


def _fallback_score(feature_row: dict[str, Any]) -> float:
    score = 0.0
    score += min(float(feature_row.get("recent_failed_attempts", 0)) / 10.0, 0.45)
    score += min(float(feature_row.get("recent_distinct_ips", 0)) / 8.0, 0.2)
    score += 0.18 if int(feature_row.get("hour", 0)) in {0, 1, 2, 3, 4, 5} else 0.0
    score += 0.15 if int(feature_row.get("success", 1)) == 0 else 0.0
    if str(feature_row.get("role") or "") in {"autoridades", "superadministrador"}:
        score += 0.05
    if str(feature_row.get("user_agent_family") or "") == "other":
        score += 0.05
    return min(1.0, round(score, 4))


def _recent_login_stats(
    username: str, ip: str, created_at: datetime, lookback_minutes: int = 60
) -> dict[str, int]:
    db = SessionLocal()
    try:
        since = created_at - timedelta(minutes=max(1, int(lookback_minutes)))
        rows = (
            db.query(WebLoginAttempt)
            .filter(
                WebLoginAttempt.created_at >= since,
                WebLoginAttempt.created_at <= created_at,
                WebLoginAttempt.username == username,
            )
            .all()
        )
        recent_failed = sum(1 for row in rows if not bool(row.success))
        recent_attempts = len(rows)
        distinct_ips = len({str(row.ip or "").strip() for row in rows if str(row.ip or "").strip()})
        current_ip_attempts = sum(1 for row in rows if str(row.ip or "").strip() == ip)
        return {
            "recent_failed_attempts": recent_failed,
            "recent_attempts": recent_attempts,
            "recent_distinct_ips": distinct_ips,
            "recent_ip_attempts": current_ip_attempts,
        }
    finally:
        db.close()


def build_feature_row(event: dict[str, Any]) -> dict[str, Any]:
    created_at = _parse_datetime(event.get("created_at"))
    metadata = _metadata_dict(event.get("metadata_json") or event.get("metadata"))
    username = str(event.get("username") or "").strip()
    ip = str(event.get("ip") or "").strip()
    role = str(metadata.get("role") or event.get("role") or "usuario").strip().lower()
    stats = _recent_login_stats(username, ip, created_at)
    return {
        "hour": created_at.hour,
        "weekday": created_at.weekday(),
        "ip_octet_bucket": _ip_octet_bucket(ip),
        "user_agent_family": _user_agent_family(str(event.get("user_agent") or "")),
        "role": role or "usuario",
        "success": 1 if bool(event.get("success", True)) else 0,
        "recent_failed_attempts": int(stats["recent_failed_attempts"]),
        "recent_attempts": int(stats["recent_attempts"]),
        "recent_distinct_ips": int(stats["recent_distinct_ips"]),
        "recent_ip_attempts": int(stats["recent_ip_attempts"]),
    }


def _heuristic_training_label(feature_row: dict[str, Any]) -> str:
    return _risk_label(_fallback_score(feature_row))


def load_training_events(hours: int = 24 * 30) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=max(1, int(hours)))
        login_rows = (
            db.query(WebLoginAttempt)
            .filter(WebLoginAttempt.created_at >= since)
            .order_by(WebLoginAttempt.created_at.asc())
            .all()
        )
        role_lookup: dict[str, str] = {}
        security_rows = (
            db.query(WebSecurityEvent)
            .filter(WebSecurityEvent.created_at >= since)
            .order_by(WebSecurityEvent.created_at.asc())
            .all()
        )
        for row in security_rows:
            metadata = _metadata_dict(row.metadata_json)
            role_value = str(metadata.get("role") or "").strip().lower()
            if row.username and role_value:
                role_lookup[str(row.username).strip()] = role_value
        events: list[dict[str, Any]] = []
        for row in login_rows:
            events.append({
                "created_at": row.created_at,
                "username": row.username,
                "ip": row.ip,
                "user_agent": row.user_agent,
                "success": bool(row.success),
                "metadata": {"role": role_lookup.get(str(row.username or "").strip(), "usuario")},
            })
        return events
    finally:
        db.close()


def build_training_dataset(hours: int = 24 * 30) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in load_training_events(hours):
        features = build_feature_row(event)
        features["label"] = _heuristic_training_label(features)
        rows.append(features)
    return rows


def sklearn_available() -> bool:
    return all(
        item is not None
        for item in (joblib, pd, ColumnTransformer, OneHotEncoder, Pipeline, RandomForestClassifier)
    )


def train_access_risk_model(hours: int = 24 * 30, output_path: str = MODEL_PATH) -> dict[str, Any]:
    dataset = build_training_dataset(hours)
    if not dataset:
        return {"status": "empty", "model_path": "", "samples": 0, "cv_accuracy": []}
    if not sklearn_available():
        return {"status": "fallback", "model_path": "", "samples": len(dataset), "cv_accuracy": []}

    frame = pd.DataFrame(dataset)
    feature_columns = [
        "hour",
        "weekday",
        "ip_octet_bucket",
        "user_agent_family",
        "role",
        "success",
        "recent_failed_attempts",
        "recent_attempts",
        "recent_distinct_ips",
        "recent_ip_attempts",
    ]
    categorical_columns = ["user_agent_family", "role"]
    numeric_columns = [col for col in feature_columns if col not in categorical_columns]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
            # StandardScaler normaliza las features numéricas para mejorar
            # la precisión del RandomForest en rangos muy distintos
            # (ej. recent_failed_attempts 0-50 vs hour 0-23)
            ("num", StandardScaler(), numeric_columns),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=80,
                random_state=42,
                class_weight="balanced",
            )),
        ]
    )

    # Validación cruzada antes del fit final para reportar accuracy real
    cv_scores: list[float] = []
    if cross_val_score is not None and len(frame) >= 10:
        try:
            scores = cross_val_score(
                model, frame[feature_columns], frame["label"], cv=3, scoring="accuracy"
            )
            cv_scores = [round(float(s), 4) for s in scores]
        except Exception:
            pass

    model.fit(frame[feature_columns], frame["label"])
    _ensure_parent_dir(output_path)

    payload = {
        "version": MODEL_VERSION,
        "feature_columns": feature_columns,
        "categorical_columns": categorical_columns,
        "pipeline": model,
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(dataset),
        "cv_accuracy": cv_scores,
    }
    joblib.dump(payload, output_path)

    # Invalidar caché para que la próxima predicción use el modelo recién entrenado
    _MODEL_CACHE.pop(output_path, None)
    _MODEL_MTIME.pop(output_path, None)

    return {
        "status": "trained",
        "model_path": output_path,
        "samples": len(dataset),
        "cv_accuracy": cv_scores,
    }


def load_model(output_path: str = MODEL_PATH) -> dict[str, Any] | None:
    """
    Carga el modelo con caché en memoria por proceso.
    Se recarga automáticamente cuando el archivo en disco es más reciente
    que la versión cacheada (tras un reentrenamiento por Celery).
    """
    if joblib is None or not os.path.exists(output_path):
        return None

    try:
        current_mtime = os.path.getmtime(output_path)
    except OSError:
        return None

    cached = _MODEL_CACHE.get(output_path)
    if cached is not None and _MODEL_MTIME.get(output_path) == current_mtime:
        return cached

    try:
        payload = joblib.load(output_path)
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    _MODEL_CACHE[output_path] = payload
    _MODEL_MTIME[output_path] = current_mtime
    return payload


def predict_access_risk(event: dict[str, Any], model_path: str = MODEL_PATH) -> dict[str, Any]:
    features = build_feature_row(event)
    model_payload = load_model(model_path)

    if model_payload and pd is not None:
        pipeline = model_payload.get("pipeline")
        feature_columns = model_payload.get("feature_columns") or list(features.keys())
        frame = pd.DataFrame([{col: features.get(col) for col in feature_columns}])
        try:
            predicted_label = str(pipeline.predict(frame)[0])
            probabilities: dict[str, float] = {}
            if hasattr(pipeline, "predict_proba"):
                classes = list(getattr(pipeline, "classes_", []))
                raw_probs = list(pipeline.predict_proba(frame)[0])
                probabilities = {str(name): float(val) for name, val in zip(classes, raw_probs)}
            risk_score = probabilities.get("sospechoso")
            if risk_score is None:
                risk_score = (
                    1.0 if predicted_label == "sospechoso"
                    else 0.55 if predicted_label == "inusual"
                    else 0.1
                )
            return {
                "label": predicted_label,
                "risk_score": round(float(risk_score), 4),
                "features": features,
                "model_status": "trained",
                "probabilities": probabilities,
            }
        except Exception:
            pass

    score = _fallback_score(features)
    return {
        "label": _risk_label(score),
        "risk_score": score,
        "features": features,
        "model_status": "fallback",
        "probabilities": {},
    }


def batch_predict_recent_logins(hours: int = 24, limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=max(1, int(hours)))
        rows = (
            db.query(WebLoginAttempt)
            .filter(WebLoginAttempt.created_at >= since)
            .order_by(WebLoginAttempt.created_at.desc())
            .limit(max(1, int(limit)))
            .all()
        )
        predictions: list[dict[str, Any]] = []
        for row in rows:
            event = {
                "created_at": row.created_at,
                "username": row.username,
                "ip": row.ip,
                "user_agent": row.user_agent,
                "success": bool(row.success),
                "metadata": {},
            }
            prediction = predict_access_risk(event)
            predictions.append({
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "username": row.username,
                "ip": row.ip,
                "success": bool(row.success),
                "label": prediction["label"],
                "risk_score": prediction["risk_score"],
                "model_status": prediction["model_status"],
            })
        return predictions
    finally:
        db.close()
        