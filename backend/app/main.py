from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import FeedbackRequest, PredictRequest
from .services import score_prediction
from .store import append_feedback, compute_metrics, load_feedback, load_roadmap

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"

app = FastAPI(title="CittaAI Phase1 Beta API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

prediction_count = 0


@app.get("/")
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "cittaai-phase1-beta",
        "utc": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/roadmap")
def roadmap() -> dict:
    return load_roadmap()


@app.post("/api/predict")
def predict(payload: PredictRequest) -> dict:
    global prediction_count
    prediction_count += 1
    return score_prediction(payload).model_dump()


@app.get("/api/feedback")
def feedback() -> list[dict]:
    return load_feedback()


@app.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> dict:
    return append_feedback(payload.model_dump())


@app.get("/api/metrics")
def metrics() -> dict:
    return compute_metrics(prediction_count)
