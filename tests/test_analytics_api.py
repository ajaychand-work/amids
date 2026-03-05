from fastapi.testclient import TestClient

from backend.app.analytics.metrics import calculate_summary_statistics, detect_anomalies_zscore
from backend.app.main import app


client = TestClient(app)


def test_predict_response_contains_risk_factors():
    payload = {
        "account_id": "acct_portfolio",
        "events_last_7d": 18,
        "active_minutes_last_7d": 55,
        "error_rate": 0.21,
        "feedback_count_last_30d": 8,
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["formula_version"] == "risk-v2-logistic"
    assert len(body["risk_factors"]) == 4
    assert 0 <= body["risk_score"] <= 100


def test_dashboard_endpoints():
    for path in [
        "/api/dashboard/kpis",
        "/api/dashboard/trends",
        "/api/dashboard/performance",
    ]:
        res = client.get(path)
        assert res.status_code == 200
        assert "window_days" in res.json()


def test_summary_statistics_helpers():
    stats = calculate_summary_statistics([10, 20, 30, 40])
    assert stats["mean"] == 25.0
    assert stats["median"] == 25.0
    assert stats["variance"] == 125.0

    anomalies = detect_anomalies_zscore([10, 11, 12, 13, 200], threshold=1.7)
    assert anomalies
