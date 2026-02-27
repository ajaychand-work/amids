# CittaAI Phase 1 Beta MVP

Minimal FastAPI + static web app to demo an account risk predictor and feedback loop for early beta customers.

## Features

- **Risk prediction API**: `/api/predict` returns a risk score, confidence, and recommended actions.
- **Feedback capture**: `/api/feedback` (GET/POST) stores feedback in `data/feedback_log.json`.
- **Roadmap + metrics**: `/api/roadmap` and `/api/metrics` power the dashboard panels.
- **Single-page UI**: `web/index.html` with `app.js` and `styles.css`, served by FastAPI.

## Getting started

1. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS / Linux
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server**:

   ```bash
   uvicorn backend.app.main:app --reload
   ```

4. Open your browser at `http://127.0.0.1:8000/`.

On first run, the app will **auto-create** `data/roadmap.json` with a default 45‑day plan so the UI is populated without any manual seeding.

## Project layout

- `backend/app/main.py` – FastAPI app and routes.
- `backend/app/schemas.py` – Pydantic request/response models.
- `backend/app/services.py` – Risk scoring logic.
- `backend/app/store.py` – JSON persistence, metrics, and auto-populated roadmap.
- `web/` – Static frontend (`index.html`, `app.js`, `styles.css`).
- `data/` – Generated at runtime for roadmap and feedback logs.

# CittaAI Phase 1 Beta MVP

This is a runnable beta project generated from your roadmap prompt.

## What you now have
- Working backend API: health, roadmap, predict, feedback, metrics.
- Working frontend UI connected to API.
- Auto-populated seed roadmap and feedback data.
- Basic API tests.

## Run locally
1. Open terminal in `cittaai_phase1_beta`.
2. Create venv:
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Start server:
   - `uvicorn backend.app.main:app --reload --port 8000`
5. Open:
   - `http://127.0.0.1:8000`

## API endpoints
- `GET /api/health`
- `GET /api/roadmap`
- `POST /api/predict`
- `GET /api/feedback`
- `POST /api/feedback`
- `GET /api/metrics`

## Test
- `pytest -q`

## Main files
- `backend/app/main.py`
- `backend/app/services.py`
- `backend/app/store.py`
- `backend/app/schemas.py`
- `web/index.html`
- `web/app.js`
- `web/styles.css`
- `data/roadmap.json`
- `data/feedback_log.json`
