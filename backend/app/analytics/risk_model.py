from __future__ import annotations

import math

from ..schemas import PredictRequest, PredictResponse, RiskFactor


FORMULA_VERSION = "risk-v2-logistic"
WEIGHTS = {
    "behavioral_load": 0.20,
    "engagement_drop": 0.35,
    "platform_stability": 0.30,
    "support_intensity": 0.15,
}


def _priority(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _normalize_signals(req: PredictRequest) -> dict[str, float]:
    # Scale each raw signal to 0-1 to combine heterogeneous business metrics.
    return {
        "behavioral_load": min(req.events_last_7d / 30.0, 1.0),
        "engagement_drop": max(0.0, 1.0 - min(req.active_minutes_last_7d / 420.0, 1.0)),
        "platform_stability": min(req.error_rate / 0.20, 1.0),
        "support_intensity": min(req.feedback_count_last_30d / 12.0, 1.0),
    }


def _recommended_actions(score: int, normalized: dict[str, float]) -> list[str]:
    actions: list[str] = []
    if normalized["platform_stability"] >= 0.55:
        actions.append("Prioritize reliability fixes and set endpoint-level alert thresholds.")
    if normalized["engagement_drop"] >= 0.50:
        actions.append("Trigger activation campaign with guided onboarding for at-risk accounts.")
    if normalized["support_intensity"] >= 0.45:
        actions.append("Create a customer success queue for high-severity unresolved feedback.")
    if normalized["behavioral_load"] >= 0.60:
        actions.append("Investigate heavy usage cohorts for friction points and feature regressions.")
    if score >= 70:
        actions.append("Escalate to account management within 24 hours with a retention playbook.")
    if not actions:
        actions.append("Maintain weekly monitoring and continue product usage experiments.")
    return actions


def score_prediction(req: PredictRequest) -> PredictResponse:
    normalized = _normalize_signals(req)
    weighted_risk = sum(normalized[name] * WEIGHTS[name] for name in WEIGHTS)

    # Logistic calibration keeps risk in 0-100 while increasing sensitivity near tipping points.
    risk_score = int(round(100.0 / (1.0 + math.exp(-8.0 * (weighted_risk - 0.50)))))
    risk_score = max(0, min(100, risk_score))

    signal_volume = min((req.events_last_7d + req.feedback_count_last_30d) / 40.0, 1.0)
    confidence = 0.58 + (0.25 * signal_volume) + (0.14 * (1.0 - abs(weighted_risk - 0.50)))
    confidence = round(min(confidence, 0.97), 2)

    risk_factors = [
        RiskFactor(
            name=name,
            weight=weight,
            normalized_value=round(normalized[name], 4),
            contribution=round(normalized[name] * weight * 100.0, 2),
        )
        for name, weight in WEIGHTS.items()
    ]

    return PredictResponse(
        account_id=req.account_id,
        risk_score=risk_score,
        priority_band=_priority(risk_score),
        confidence=confidence,
        formula_version=FORMULA_VERSION,
        risk_factors=risk_factors,
        recommended_actions=_recommended_actions(risk_score, normalized),
    )
