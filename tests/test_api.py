from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


def test_predict():
    payload = {
        "account_id": "acct_1",
        "events_last_7d": 7,
        "active_minutes_last_7d": 84,
        "error_rate": 0.12,
        "feedback_count_last_30d": 3,
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["account_id"] == "acct_1"
    assert 0 <= body["risk_score"] <= 100


def test_feedback_roundtrip():
    payload = {
        "user_id": "u_test",
        "feature": "insight_dashboard",
        "sentiment": "positive",
        "severity": "low",
        "message": "Test feedback",
    }
    post_res = client.post("/api/feedback", json=payload)
    assert post_res.status_code == 200

    get_res = client.get("/api/feedback")
    assert get_res.status_code == 200
    rows = get_res.json()
    assert any(r["user_id"] == "u_test" for r in rows)
