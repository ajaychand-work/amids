from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PredictRequest(BaseModel):
    account_id: str = Field(min_length=2, max_length=64)
    events_last_7d: int = Field(ge=0, le=50_000)
    active_minutes_last_7d: int = Field(ge=0, le=10_080)
    error_rate: float = Field(ge=0, le=1)
    feedback_count_last_30d: int = Field(ge=0, le=500)

    @field_validator("account_id")
    @classmethod
    def clean_account_id(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_any_signal(self) -> "PredictRequest":
        if (
            self.events_last_7d == 0
            and self.active_minutes_last_7d == 0
            and self.feedback_count_last_30d == 0
        ):
            raise ValueError("At least one behavioral signal must be greater than zero.")
        return self


class RiskFactor(BaseModel):
    name: str
    weight: float
    normalized_value: float
    contribution: float


class PredictResponse(BaseModel):
    account_id: str
    risk_score: int
    priority_band: Literal["low", "medium", "high"]
    confidence: float
    formula_version: str
    risk_factors: list[RiskFactor]
    recommended_actions: list[str]


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=64)
    feature: str = Field(min_length=2, max_length=128)
    sentiment: Literal["positive", "neutral", "negative"]
    severity: Literal["low", "medium", "high"]
    message: str = Field(min_length=3, max_length=500)

    @field_validator("user_id", "feature")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip()

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return value.strip()


class FeedbackRecord(FeedbackRequest):
    id: str
    created_at: str
