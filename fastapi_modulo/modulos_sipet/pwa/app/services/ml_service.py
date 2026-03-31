import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def save_model(model: Any, name: str) -> Path:
    path = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    logger.info("Model saved: %s", path)
    return path


def load_model(name: str) -> Any:
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Model '{name}' not found at {path}")
    return joblib.load(path)


def list_models() -> list[str]:
    return sorted([p.stem for p in MODELS_DIR.glob("*.joblib")])


def delete_model(name: str) -> None:
    path = MODELS_DIR / f"{name}.joblib"
    if path.exists():
        path.unlink()
        logger.info("Model deleted: %s", name)


def dataframe_from_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        raise ValueError("records cannot be empty")
    return pd.DataFrame(records)


def prepare_features(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str | None = None,
) -> tuple[pd.DataFrame, pd.Series | None]:
    missing = [col for col in feature_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {', '.join(missing)}")
    if target_col and target_col not in df.columns:
        raise ValueError(f"Missing target column: {target_col}")

    X = df[feature_cols].copy()
    y = df[target_col] if target_col else None
    return X, y


def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    categorical_cols = [col for col in X.columns if col not in numeric_cols]

    transformers = []
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            )
        )
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            )
        )

    return ColumnTransformer(transformers=transformers)


def train_classifier(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    test_size: float = 0.2,
    n_estimators: int = 100,
    random_state: int = 42,
) -> dict:
    if y.nunique() < 2:
        raise ValueError("Classifier target must contain at least 2 classes")

    class_counts = y.value_counts(dropna=False)
    stratify = y if class_counts.min() > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    pipeline = Pipeline(
        [
            ("preprocessor", _build_preprocessor(X)),
            ("clf", RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
        "model_name": model_name,
        "n_samples": len(X),
        "n_features": X.shape[1],
    }

    save_model(pipeline, model_name)
    logger.info("Classifier trained — accuracy: %.4f", metrics["accuracy"])
    return metrics


def train_regressor(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    test_size: float = 0.2,
    n_estimators: int = 100,
    random_state: int = 42,
) -> dict:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    pipeline = Pipeline(
        [
            ("preprocessor", _build_preprocessor(X)),
            ("reg", RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = {
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "model_name": model_name,
        "n_samples": len(X),
        "n_features": X.shape[1],
    }

    save_model(pipeline, model_name)
    logger.info("Regressor trained — R2: %.4f | RMSE: %.4f", metrics["r2"], metrics["rmse"])
    return metrics


def predict(model_name: str, records: list[dict]) -> list[Any]:
    model = load_model(model_name)
    df = pd.DataFrame(records)
    return model.predict(df).tolist()


def predict_proba(model_name: str, records: list[dict]) -> list[list[float]]:
    model = load_model(model_name)
    if not hasattr(model, "predict_proba"):
        raise ValueError(f"Model '{model_name}' does not support probability estimates")
    df = pd.DataFrame(records)
    return model.predict_proba(df).tolist()
