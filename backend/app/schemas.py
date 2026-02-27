from pydantic import BaseModel, Field
from typing import Literal


class PredictRequest(BaseModel):
    account_id: str = Field(min_length=2)
    events_last_7d: int = Field(ge=0)
    active_minutes_last_7d: int = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    feedback_count_last_30d: int = Field(ge=0)


class PredictResponse(BaseModel):
    account_id: str
    risk_score: int
    priority_band: Literal["low", "medium", "high"]
    confidence: float
    recommended_actions: list[str]


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2)
    feature: str = Field(min_length=2)
    sentiment: Literal["positive", "neutral", "negative"]
    severity: Literal["low", "medium", "high"]
    message: str = Field(min_length=3)


class FeedbackRecord(FeedbackRequest):
    id: str
    created_at: str
