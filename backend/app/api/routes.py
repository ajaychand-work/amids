from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..analytics import score_prediction
from ..schemas import FeedbackRequest, PredictRequest
from ..services import (
    append_feedback,
    append_prediction,
    compute_metrics,
    get_kpi_dashboard,
    get_performance_metrics,
    get_trend_analysis,
    load_feedback,
    load_roadmap,
)

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "cittaai-phase1-beta",
        "utc": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }


@router.get("/api/roadmap")
def roadmap() -> dict:
    return load_roadmap()


@router.post("/api/predict")
def predict(payload: PredictRequest) -> dict:
    scored = score_prediction(payload)
    append_prediction(scored.model_dump())
    return scored.model_dump()


@router.get("/api/feedback")
def feedback() -> list[dict]:
    return load_feedback()


@router.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> dict:
    return append_feedback(payload.model_dump())


@router.get("/api/metrics")
def metrics() -> dict:
    return compute_metrics()


@router.get("/api/dashboard/kpis")
def dashboard_kpis(days: int = Query(default=30, ge=7, le=365)) -> dict:
    return get_kpi_dashboard(days=days)


@router.get("/api/dashboard/trends")
def dashboard_trends(days: int = Query(default=30, ge=7, le=365)) -> dict:
    return get_trend_analysis(days=days)


@router.get("/api/dashboard/performance")
def dashboard_performance(days: int = Query(default=30, ge=7, le=365)) -> dict:
    return get_performance_metrics(days=days)
