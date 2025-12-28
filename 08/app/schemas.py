from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=1)
    request_id: str | None = None


class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    model_version: str
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str
