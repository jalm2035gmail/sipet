from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
try:
    import joblib
except Exception:
    joblib = None
try:
    from sklearn.cluster import KMeans
except Exception:
    KMeans = None


MODEL_PATH = Path(__file__).resolve().with_name("dashboard_model.pkl")


class SimpleClusterModel:
    def __init__(self, centers: np.ndarray):
        self.cluster_centers_ = centers
        self.n_clusters = int(len(centers))

    def predict(self, matrix: np.ndarray) -> np.ndarray:
        if matrix.size == 0 or self.n_clusters == 0:
            return np.asarray([], dtype=int)
        distances = np.linalg.norm(matrix[:, None, :] - self.cluster_centers_[None, :, :], axis=2)
        return np.argmin(distances, axis=1)


def _build_usage_matrix(modules: list[dict]) -> tuple[np.ndarray, list[dict]]:
    rows = []
    normalized_modules = []
    for item in modules:
        route = str(item.get("route") or "").strip()
        key = str(item.get("key") or route).strip()
        if not route or not key:
            continue
        rows.append(
            [
                float(item.get("usage_count") or 1.0),
                float(1 if str(item.get("description") or "").strip() else 0),
                float(1 if bool(item.get("is_favorite")) else 0),
                float(1 if bool(item.get("is_pinned")) else 0),
            ]
        )
        normalized_modules.append(item)
    if not rows:
        return np.empty((0, 4)), []
    return np.asarray(rows, dtype=float), normalized_modules


def train_recommendation_model(modules: list[dict], n_clusters: int = 5, model_path: Path | None = None) -> dict:
    matrix, normalized_modules = _build_usage_matrix(modules)
    if len(normalized_modules) < 2:
        return {"status": "insufficient_data", "model_path": str(model_path or MODEL_PATH), "clusters": []}
    cluster_count = max(1, min(int(n_clusters), len(normalized_modules)))
    if KMeans is not None:
        model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        clusters = model.fit_predict(matrix)
    else:
        sorted_idx = np.argsort(-matrix[:, 0])
        centers = matrix[sorted_idx[:cluster_count]]
        model = SimpleClusterModel(centers)
        clusters = model.predict(matrix)
    resolved_model_path = model_path or MODEL_PATH
    if joblib is not None:
        joblib.dump(model, resolved_model_path)
    else:
        with resolved_model_path.open("wb") as buffer:
            pickle.dump(model, buffer)
    return {
        "status": "trained",
        "model_path": str(resolved_model_path),
        "clusters": clusters.tolist(),
    }


def load_recommendation_model(model_path: Path | None = None):
    resolved_model_path = model_path or MODEL_PATH
    if not resolved_model_path.exists():
        return None
    if joblib is not None:
        return joblib.load(resolved_model_path)
    with resolved_model_path.open("rb") as buffer:
        return pickle.load(buffer)


def recommend_modules(modules: list[dict], limit: int = 4) -> list[dict]:
    if not modules:
        return []
    matrix, normalized_modules = _build_usage_matrix(modules)
    model = load_recommendation_model()
    cluster_scores: dict[int, float] = {}
    if model is not None and len(normalized_modules) >= getattr(model, "n_clusters", 0):
        predicted_clusters = model.predict(matrix)
        for cluster_id, row in zip(predicted_clusters, matrix):
            cluster_scores[int(cluster_id)] = cluster_scores.get(int(cluster_id), 0.0) + float(np.sum(row))
    else:
        predicted_clusters = np.zeros(len(normalized_modules), dtype=int)
    scored = []
    for item, cluster_id in zip(normalized_modules, predicted_clusters):
        description_score = 1.0 if str(item.get("description") or "").strip() else 0.25
        favorite_score = 1.5 if bool(item.get("is_favorite")) else 1.0
        pinned_score = 1.25 if bool(item.get("is_pinned")) else 1.0
        cluster_score = cluster_scores.get(int(cluster_id), 1.0) or 1.0
        score = np.round(description_score * favorite_score * pinned_score * cluster_score, 2)
        scored.append((float(score), item))
    ranked = sorted(scored, key=lambda item: (-item[0], str(item[1].get("label") or "").lower()))
    return [item for _, item in ranked[:limit]]
