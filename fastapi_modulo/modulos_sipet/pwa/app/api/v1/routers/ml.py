from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Any
import pandas as pd
import io

from app.api.deps import get_current_active_user, get_current_superuser
from app.services import ml_service

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TrainRequest(BaseModel):
    model_name: str
    feature_cols: list[str]
    target_col: str
    model_type: str = "classifier"   # "classifier" | "regressor"
    test_size: float = 0.2
    n_estimators: int = 100
    records: list[dict]


class PredictRequest(BaseModel):
    model_name: str
    records: list[dict]


class TrainResponse(BaseModel):
    model_name: str
    metrics: dict


class PredictResponse(BaseModel):
    model_name: str
    predictions: list[Any]


class ProbaResponse(BaseModel):
    model_name: str
    probabilities: list[list[float]]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/train", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def train(
    body: TrainRequest,
    current_user=Depends(get_current_superuser),   # solo superuser puede entrenar
):
    try:
        df = ml_service.dataframe_from_records(body.records)
        X, y = ml_service.prepare_features(df, body.feature_cols, body.target_col)

        if body.model_type == "classifier":
            metrics = ml_service.train_classifier(
                X, y,
                model_name=body.model_name,
                test_size=body.test_size,
                n_estimators=body.n_estimators,
            )
        elif body.model_type == "regressor":
            metrics = ml_service.train_regressor(
                X, y,
                model_name=body.model_name,
                test_size=body.test_size,
                n_estimators=body.n_estimators,
            )
        else:
            raise HTTPException(status_code=400, detail="model_type must be 'classifier' or 'regressor'")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return TrainResponse(model_name=body.model_name, metrics=metrics)


@router.post("/train/csv", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
async def train_from_csv(
    model_name: str,
    target_col: str,
    model_type: str = "classifier",
    file: UploadFile = File(...),
    current_user=Depends(get_current_superuser),
):
    """Entrena un modelo a partir de un CSV subido."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        feature_cols = [c for c in df.columns if c != target_col]
        X, y = ml_service.prepare_features(df, feature_cols, target_col)

        if model_type == "classifier":
            metrics = ml_service.train_classifier(X, y, model_name=model_name)
        else:
            metrics = ml_service.train_regressor(X, y, model_name=model_name)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return TrainResponse(model_name=model_name, metrics=metrics)


@router.post("/predict", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    current_user=Depends(get_current_active_user),
):
    try:
        predictions = ml_service.predict(body.model_name, body.records)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return PredictResponse(model_name=body.model_name, predictions=predictions)


@router.post("/predict/proba", response_model=ProbaResponse)
def predict_proba(
    body: PredictRequest,
    current_user=Depends(get_current_active_user),
):
    try:
        probabilities = ml_service.predict_proba(body.model_name, body.records)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ProbaResponse(model_name=body.model_name, probabilities=probabilities)


@router.get("/models", response_model=list[str])
def list_models(current_user=Depends(get_current_active_user)):
    return ml_service.list_models()


@router.delete("/models/{model_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_name: str,
    current_user=Depends(get_current_superuser),
):
    try:
        ml_service.delete_model(model_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
