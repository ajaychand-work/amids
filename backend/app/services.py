from __future__ import annotations

from .schemas import PredictRequest, PredictResponse


def _priority(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _actions(score: int, error_rate: float, active_minutes: int) -> list[str]:
    actions = []
    if error_rate >= 0.15:
        actions.append("Run reliability review and add endpoint-level alerting")
    if active_minutes < 90:
        actions.append("Trigger onboarding nudge and guided product tour")
    if score >= 70:
        actions.append("Escalate account to beta success manager within 24h")
    if not actions:
        actions.append("Maintain current cadence and monitor weekly trend")
    return actions


def score_prediction(req: PredictRequest) -> PredictResponse:
    score = 0
    score += min(req.events_last_7d * 3, 30)
    score += max(0, 25 - min(req.active_minutes_last_7d // 8, 25))
    score += int(req.error_rate * 100 * 0.35)
    score += min(req.feedback_count_last_30d * 5, 20)
    score = max(0, min(score, 100))
    band = _priority(score)
    confidence = round(0.62 + min(req.events_last_7d, 8) * 0.03, 2)
    confidence = min(confidence, 0.93)

    return PredictResponse(
        account_id=req.account_id,
        risk_score=score,
        priority_band=band,
        confidence=confidence,
        recommended_actions=_actions(score, req.error_rate, req.active_minutes_last_7d),
    )
