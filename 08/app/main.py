from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from app.config import configure_logging, get_settings
from app.schemas import HealthResponse, PredictRequest, PredictResponse
from app.services.model import IrisRuleModel, load_model

app = FastAPI(title="ML Model Serving API", version="1.0.0")


@app.on_event("startup")
def load_model_on_startup() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    model = load_model(settings.model_path)
    app.state.model = model
    logging.getLogger(__name__).info(
        "model loaded",
        extra={"model_version": model.version, "model_path": str(settings.model_path)},
    )


def _get_model() -> IrisRuleModel:
    model = getattr(app.state, "model", None)
    if model is None:
        raise RuntimeError("Model is not loaded")
    return model


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    model = _get_model()
    try:
        label, confidence = model.predict(payload.features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PredictResponse(
        prediction=label,
        confidence=confidence,
        model_version=model.version,
        request_id=payload.request_id,
    )
