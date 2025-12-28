from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=1)
    request_id: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    model_version: str
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str
