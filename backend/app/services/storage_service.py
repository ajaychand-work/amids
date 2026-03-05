from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from ..analytics import calculate_summary_statistics

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
ROADMAP_PATH = DATA_DIR / "roadmap.json"
FEEDBACK_PATH = DATA_DIR / "feedback_log.json"
PREDICTION_PATH = DATA_DIR / "prediction_log.json"


DEFAULT_ROADMAP = {
    "project": "CittaAI Phase 1 Beta",
    "betaFocus": "Deliver a stable and measurable AI analytics beta within 45 days.",
    "assignee": "Owner: Analytics Lead",
    "date": datetime.now(timezone.utc).date().isoformat(),
    "successMetrics": [
        "Weekly active beta users >= 35",
        "Core API P95 latency <= 900ms",
        "Insight success rate >= 97%",
        "Feedback response SLA <= 48h",
    ],
    "milestones": [
        {
            "window": "Days 1-10",
            "title": "Instrumentation and baseline data quality",
            "deliverables": [
                "Ingest campaign and CRM signals into warehouse",
                "Set quality checks for nulls, duplicates, and reconciliation",
                "Release initial KPI and risk scoring endpoints",
            ],
        },
        {
            "window": "Days 11-25",
            "title": "Analytics enrichment",
            "deliverables": [
                "Feature engineering for channel-level risk signals",
                "Statistical anomaly detection on core KPIs",
                "Dashboard endpoint expansion for trend analysis",
            ],
        },
        {
            "window": "Days 26-45",
            "title": "Operationalization and launch readiness",
            "deliverables": [
                "Weekly executive summaries with forecast snapshots",
                "KPI monitoring and threshold alerts",
                "Portfolio-grade documentation and demo artifacts",
            ],
        },
    ],
}


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return fallback


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def load_roadmap() -> dict:
    if not ROADMAP_PATH.exists():
        _write_json(ROADMAP_PATH, DEFAULT_ROADMAP)
        return DEFAULT_ROADMAP
    return _read_json(ROADMAP_PATH, DEFAULT_ROADMAP)


def load_feedback() -> list[dict]:
    return _read_json(FEEDBACK_PATH, [])


def load_predictions() -> list[dict]:
    return _read_json(PREDICTION_PATH, [])


def append_feedback(payload: dict) -> dict:
    row = {
        "id": str(uuid.uuid4())[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    rows = load_feedback()
    rows.insert(0, row)
    _write_json(FEEDBACK_PATH, rows[:500])
    return row


def append_prediction(payload: dict) -> dict:
    row = {
        "id": str(uuid.uuid4())[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    rows = load_predictions()
    rows.insert(0, row)
    _write_json(PREDICTION_PATH, rows[:1_000])
    return row


def compute_metrics(prediction_count: int | None = None) -> dict:
    feedback = load_feedback()
    predictions = load_predictions()
    prediction_total = len(predictions)
    if prediction_count is not None:
        prediction_total = max(prediction_total, int(prediction_count))

    negative = sum(1 for row in feedback if row.get("sentiment") == "negative")
    high_severity = sum(1 for row in feedback if row.get("severity") == "high")
    risk_scores = [float(row.get("risk_score", 0)) for row in predictions if "risk_score" in row]
    risk_stats = calculate_summary_statistics(risk_scores)

    return {
        "prediction_count": prediction_total,
        "feedback_total": len(feedback),
        "feedback_negative": negative,
        "feedback_high_severity": high_severity,
        "feedback_response_sla_hours": 48,
        "risk_score_mean": risk_stats["mean"],
        "risk_score_median": risk_stats["median"],
        "risk_score_variance": risk_stats["variance"],
    }
