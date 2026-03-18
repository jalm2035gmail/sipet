from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# Imports opcionales — no rompen el módulo si no están instalados
try:
    import joblib
except ImportError:  # pragma: no cover
    joblib = None  # type: ignore[assignment]

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:
    from sklearn.pipeline import Pipeline as SKPipeline
except ImportError:  # pragma: no cover
    SKPipeline = None  # type: ignore[assignment]


_CATEGORY_DIRS = ("models", "pipelines", "artifacts")


class ModuleMLService:
    def __init__(self, module_root: str | Path) -> None:
        self.module_root = Path(module_root).resolve()
        self.ml_root = self.module_root / "ml"
        self.models_dir = self.ml_root / "models"
        self.pipelines_dir = self.ml_root / "pipelines"
        self.artifacts_dir = self.ml_root / "artifacts"

    # ── Estructura ────────────────────────────────────────────────────────────

    def ensure_structure(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def artifact_path(self, category: str, filename: str) -> Path:
        directories: dict[str, Path] = {
            "models": self.models_dir,
            "pipelines": self.pipelines_dir,
            "artifacts": self.artifacts_dir,
        }
        base_dir = directories.get(str(category or "").strip(), self.artifacts_dir)
        return (base_dir / str(filename or "").strip()).resolve()

    # ── Persistencia con joblib ───────────────────────────────────────────────

    def _require_joblib(self) -> Any:
        if joblib is None:
            raise RuntimeError("joblib no esta disponible. Instala: pip install joblib")
        return joblib

    def load_joblib_model(self, filename: str) -> Any:
        jb = self._require_joblib()
        path = self.artifact_path("models", filename)
        if not path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {path}")
        return jb.load(path)

    def save_model(self, model: Any, filename: str, *, compress: int = 3) -> Path:
        """Persiste un modelo sklearn/joblib en ml/models/."""
        jb = self._require_joblib()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifact_path("models", filename)
        jb.dump(model, path, compress=compress)
        return path

    def load_pipeline(self, filename: str) -> Any:
        """Carga un pipeline serializado desde ml/pipelines/."""
        jb = self._require_joblib()
        path = self.artifact_path("pipelines", filename)
        if not path.exists():
            raise FileNotFoundError(f"Pipeline no encontrado: {path}")
        return jb.load(path)

    def save_pipeline(self, pipeline: Any, filename: str, *, compress: int = 3) -> Path:
        """Persiste un pipeline en ml/pipelines/."""
        jb = self._require_joblib()
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifact_path("pipelines", filename)
        jb.dump(pipeline, path, compress=compress)
        return path

    def load_artifact(self, filename: str) -> Any:
        """Carga cualquier artefacto genérico desde ml/artifacts/."""
        jb = self._require_joblib()
        path = self.artifact_path("artifacts", filename)
        if not path.exists():
            raise FileNotFoundError(f"Artefacto no encontrado: {path}")
        return jb.load(path)

    # ── Preprocesamiento ──────────────────────────────────────────────────────

    def preprocess_with_numpy_or_pandas(
        self,
        payload: Any,
        *,
        processor: Callable[[Any], Any] | None = None,
    ) -> Any:
        if processor is not None:
            return processor(payload)
        return payload

    def to_dataframe(self, data: Any, *, columns: list[str] | None = None) -> "pd.DataFrame":
        """Convierte dicts, listas o arrays a DataFrame de pandas."""
        if pd is None:
            raise RuntimeError("pandas no esta disponible. Instala: pip install pandas")
        if isinstance(data, pd.DataFrame):
            return data
        df = pd.DataFrame(data)
        if columns:
            df = df[columns]
        return df

    def to_numpy(self, data: Any) -> "np.ndarray":
        """Convierte DataFrames, listas o dicts a ndarray de numpy."""
        if np is None:
            raise RuntimeError("numpy no esta disponible. Instala: pip install numpy")
        if pd is not None and isinstance(data, pd.DataFrame):
            return data.to_numpy()
        return np.array(data)

    # ── Inferencia ────────────────────────────────────────────────────────────

    def run_inference(
        self,
        model: Any,
        payload: Any,
        *,
        preprocessor: Callable[[Any], Any] | None = None,
        predictor_name: str = "predict",
    ) -> Any:
        processed = self.preprocess_with_numpy_or_pandas(payload, processor=preprocessor)
        predictor = getattr(model, predictor_name, None)
        if predictor is None or not callable(predictor):
            raise AttributeError(f"El modelo no expone un metodo callable '{predictor_name}'.")
        return predictor(processed)

    def predict_dataframe(
        self,
        model_filename: str,
        data: Any,
        *,
        columns: list[str] | None = None,
        output_column: str = "prediccion",
    ) -> "pd.DataFrame":
        """
        Carga un modelo, convierte `data` a DataFrame, corre predict()
        y devuelve el DataFrame original con una columna de predicciones.
        """
        if pd is None:
            raise RuntimeError("pandas no esta disponible. Instala: pip install pandas")
        model = self.load_joblib_model(model_filename)
        df = self.to_dataframe(data, columns=columns)
        df[output_column] = model.predict(df)
        return df

    def predict_proba_dataframe(
        self,
        model_filename: str,
        data: Any,
        *,
        columns: list[str] | None = None,
        class_labels: list[str] | None = None,
    ) -> "pd.DataFrame":
        """
        Igual que predict_dataframe pero usando predict_proba().
        Devuelve el DataFrame original con una columna por clase.
        """
        if pd is None:
            raise RuntimeError("pandas no esta disponible. Instala: pip install pandas")
        model = self.load_joblib_model(model_filename)
        df = self.to_dataframe(data, columns=columns)
        proba = model.predict_proba(df)
        labels = class_labels or [f"clase_{i}" for i in range(proba.shape[1])]
        for i, label in enumerate(labels):
            df[label] = proba[:, i]
        return df

    def fit_and_save(
        self,
        model: Any,
        data: Any,
        target: Any,
        filename: str,
        *,
        compress: int = 3,
    ) -> Path:
        """
        Entrena el modelo con (data, target) y lo persiste en ml/models/.
        Útil para tareas Celery de reentrenamiento.
        """
        X = self.to_numpy(data)
        y = self.to_numpy(target)
        model.fit(X, y)
        return self.save_model(model, filename, compress=compress)

    # ── Evaluación básica ─────────────────────────────────────────────────────

    def evaluate(
        self,
        model_filename: str,
        data: Any,
        target: Any,
        *,
        metrics: list[str] | None = None,
    ) -> dict[str, float]:
        """
        Evalúa un modelo persistido contra (data, target).
        Métricas soportadas: accuracy, f1, precision, recall, r2, mse, mae.
        """
        try:
            from sklearn import metrics as skmetrics
        except ImportError as exc:
            raise RuntimeError("scikit-learn no esta disponible. Instala: pip install scikit-learn") from exc

        model = self.load_joblib_model(model_filename)
        X = self.to_numpy(data)
        y_true = self.to_numpy(target)
        y_pred = model.predict(X)

        _metric_map: dict[str, Callable[..., float]] = {
            "accuracy": skmetrics.accuracy_score,
            "f1": lambda yt, yp: skmetrics.f1_score(yt, yp, average="weighted", zero_division=0),
            "precision": lambda yt, yp: skmetrics.precision_score(yt, yp, average="weighted", zero_division=0),
            "recall": lambda yt, yp: skmetrics.recall_score(yt, yp, average="weighted", zero_division=0),
            "r2": skmetrics.r2_score,
            "mse": skmetrics.mean_squared_error,
            "mae": skmetrics.mean_absolute_error,
        }

        requested = metrics or ["accuracy"]
        results: dict[str, float] = {}
        for name in requested:
            fn = _metric_map.get(name)
            if fn is None:
                raise ValueError(f"Metrica no soportada: '{name}'. Opciones: {list(_metric_map)}")
            results[name] = float(fn(y_true, y_pred))
        return results

    # ── Utilidades ────────────────────────────────────────────────────────────

    def list_artifacts(self, category: str = "models") -> list[str]:
        """Lista los archivos persistidos en una categoría."""
        directories: dict[str, Path] = {
            "models": self.models_dir,
            "pipelines": self.pipelines_dir,
            "artifacts": self.artifacts_dir,
        }
        target = directories.get(category, self.artifacts_dir)
        if not target.exists():
            return []
        return sorted(p.name for p in target.iterdir() if p.is_file())

    def delete_artifact(self, category: str, filename: str) -> bool:
        """Elimina un artefacto persistido. Devuelve True si existía."""
        path = self.artifact_path(category, filename)
        if path.exists():
            path.unlink()
            return True
        return False


__all__ = ["ModuleMLService"]
