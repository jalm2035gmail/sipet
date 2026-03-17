from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class ModuleMLService:
    def __init__(self, module_root: str | Path) -> None:
        self.module_root = Path(module_root).resolve()
        self.ml_root = self.module_root / "ml"
        self.models_dir = self.ml_root / "models"
        self.pipelines_dir = self.ml_root / "pipelines"
        self.artifacts_dir = self.ml_root / "artifacts"

    def ensure_structure(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def artifact_path(self, category: str, filename: str) -> Path:
        directories = {
            "models": self.models_dir,
            "pipelines": self.pipelines_dir,
            "artifacts": self.artifacts_dir,
        }
        base_dir = directories.get(str(category or "").strip(), self.artifacts_dir)
        return (base_dir / str(filename or "").strip()).resolve()

    def load_joblib_model(self, filename: str) -> Any:
        path = self.artifact_path("models", filename)
        try:
            import joblib
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("joblib no esta disponible.") from exc
        return joblib.load(path)

    def preprocess_with_numpy_or_pandas(
        self,
        payload: Any,
        *,
        processor: Callable[[Any], Any] | None = None,
    ) -> Any:
        if processor is not None:
            return processor(payload)
        return payload

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


__all__ = ["ModuleMLService"]
