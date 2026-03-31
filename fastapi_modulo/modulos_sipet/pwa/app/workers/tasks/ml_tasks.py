import logging
from app.workers.celery_app import celery_app
from app.services import ml_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.train_model", max_retries=2)
def train_model_task(
    self,
    records: list[dict],
    feature_cols: list[str],
    target_col: str,
    model_name: str,
    model_type: str = "classifier",
    n_estimators: int = 100,
):
    try:
        df = ml_service.dataframe_from_records(records)
        X, y = ml_service.prepare_features(df, feature_cols, target_col)

        if model_type == "classifier":
            metrics = ml_service.train_classifier(X, y, model_name=model_name, n_estimators=n_estimators)
        else:
            metrics = ml_service.train_regressor(X, y, model_name=model_name, n_estimators=n_estimators)

        logger.info("ML train task complete: %s | metrics: %s", model_name, metrics)
        return {"status": "ok", "model_name": model_name, "metrics": metrics}
    except Exception as exc:
        logger.error("ML train task failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.batch_predict")
def batch_predict_task(model_name: str, records: list[dict]) -> dict:
    try:
        predictions = ml_service.predict(model_name, records)
        return {"status": "ok", "model_name": model_name, "predictions": predictions}
    except Exception as exc:
        logger.error("Batch predict failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
