from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException

from app.config import configure_logging, get_settings
from app.schemas import (
    HealthResponse,
    LoginRequest,
    PredictRequest,
    PredictResponse,
    TokenResponse,
)
from app.services.auth import authenticate_user, create_access_token, require_roles
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


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    settings = get_settings()
    user = authenticate_user(payload.username, payload.password, settings)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user, settings)
    return TokenResponse(access_token=token)


@app.post("/predict", response_model=PredictResponse)
def predict(
    payload: PredictRequest,
    _user=Depends(require_roles("user", "admin")),
) -> PredictResponse:
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


@app.post("/admin/reload")
def reload_model(
    _user=Depends(require_roles("admin")),
) -> dict[str, str]:
    settings = get_settings()
    model = load_model(settings.model_path)
    app.state.model = model
    return {"status": "reloaded", "model_version": model.version}
