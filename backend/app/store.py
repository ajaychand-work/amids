from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
ROADMAP_PATH = DATA_DIR / "roadmap.json"
FEEDBACK_PATH = DATA_DIR / "feedback_log.json"


DEFAULT_ROADMAP = {
    "project": "CittaAI Phase 1 Beta MVP",
    "betaFocus": "Validate risk scoring and feedback loop with 10–20 design partners.",
    "assignee": "Owner: Beta Lead",
    "date": datetime.now(timezone.utc).date().isoformat(),
    "milestones": [
        {
            "window": "Week 1–2",
            "title": "Instrument core flows",
            "deliverables": [
                "Add event tracking to key product journeys",
                "Ship initial risk scoring model behind feature flag",
            ],
        },
        {
            "window": "Week 3–4",
            "title": "Close feedback loop",
            "deliverables": [
                "Onboard first 5–10 beta accounts",
                "Review negative feedback within 48 hours",
                "Tune thresholds for high‑risk accounts",
            ],
        },
        {
            "window": "Week 5–6",
            "title": "Stabilize and prepare GA",
            "deliverables": [
                "Harden alerts and dashboards for on‑call",
                "Document runbooks for top 3 incident types",
                "Define success metrics for GA rollout",
            ],
        },
    ],
}


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_roadmap() -> dict:
    """
    Load the roadmap configuration, creating a sensible default on first run.

    This lets a fresh checkout of the project render a complete UI without
    requiring any manual data seeding.
    """
    if not ROADMAP_PATH.exists():
        _write_json(ROADMAP_PATH, DEFAULT_ROADMAP)
        return DEFAULT_ROADMAP
    return _read_json(ROADMAP_PATH, {})


def load_feedback() -> list[dict]:
    return _read_json(FEEDBACK_PATH, [])


def append_feedback(payload: dict) -> dict:
    row = {
        "id": str(uuid.uuid4())[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    rows = load_feedback()
    rows.insert(0, row)
    rows = rows[:200]
    _write_json(FEEDBACK_PATH, rows)
    return row


def compute_metrics(prediction_count: int) -> dict:
    feedback = load_feedback()
    negative = sum(1 for r in feedback if r["sentiment"] == "negative")
    high = sum(1 for r in feedback if r["severity"] == "high")
    return {
        "prediction_count": prediction_count,
        "feedback_total": len(feedback),
        "feedback_negative": negative,
        "feedback_high_severity": high,
        "feedback_response_sla_hours": 48,
    }
