# AMIDS (Autonomous Marketing Intelligence & Decision System)

AMIDS is a portfolio-grade analytics project that simulates a production marketing intelligence workflow.
It combines:

- A FastAPI backend for risk scoring, KPI analytics, and dashboard data APIs
- A multi-agent AMIDS pipeline for ingestion, validation, KPI modeling, anomaly detection, forecasting, and reporting
- SQL-first analytics artifacts (aggregations, joins, window functions)
- A lightweight dashboard (web + Streamlit) for analysis and monitoring

## Problem Statement

Marketing and growth teams often struggle to combine campaign data, quality monitoring, and actionable risk signals in one place.
AMIDS solves this by:

- Consolidating campaign performance and KPI signals
- Detecting anomalies with statistical methods
- Scoring account risk with explainable factors
- Producing dashboard-ready trend and performance metrics

## Project Highlights

- Explainable risk scoring formula (`risk-v2-logistic`) with factor contributions
- Statistical anomaly detection using both z-score and MAD
- Data quality checks persisted to `data_quality_log`
- Dataset summary statistics (`mean`, `median`, `variance`) surfaced via API
- SQL portfolio queries for trend, engagement, and risk-distribution analysis
- Batch analytics scripts for cleaning, feature engineering, and report generation

## Data Pipeline

1. `data_agent` ingests/simulates campaign data into SQLite.
2. `validation_agent` runs quality checks (nulls, duplicates, funnel consistency, ROI sanity) and logs outcomes.
3. `summary_stats_agent` stores daily summary metrics for monitoring.
4. `kpi_agent` computes CAC/LTV/ROI and related KPI models.
5. `anomaly_agent` flags CAC spikes/revenue drops with z-score + MAD.
6. `rootcause_agent` attributes likely impact drivers.
7. `forecast_agent` stores baseline 4-week forecasts.
8. `ai_insight_agent` writes executive summary reports.
9. `dashboard_agent` records dashboard refresh markers.

## Analytics Methodology

### Risk Scoring

Risk score is computed from normalized signals:

- `behavioral_load`
- `engagement_drop`
- `platform_stability`
- `support_intensity`

Then calibrated with a logistic transformation:

`risk = 100 / (1 + exp(-8 * (weighted_signal - 0.5)))`

Output includes:

- `risk_score`
- `priority_band` (`low` / `medium` / `high`)
- `confidence`
- `risk_factors` with per-factor contribution
- recommended actions

### Statistical Analysis

- Summary statistics: mean, median, variance, min, max
- Anomaly detection:
  - z-score for distribution-based outliers
  - MAD for robust outlier detection
- KPI monitoring vs threshold ranges for operational status

## API Endpoints

### Core

- `GET /api/health`
- `GET /api/roadmap`
- `POST /api/predict`
- `GET /api/feedback`
- `POST /api/feedback`
- `GET /api/metrics`

### Dashboard Analytics

- `GET /api/dashboard/kpis`
- `GET /api/dashboard/trends`
- `GET /api/dashboard/performance`

## Example Outputs

### Predict response (sample)

```json
{
  "account_id": "acct_portfolio",
  "risk_score": 78,
  "priority_band": "high",
  "confidence": 0.87,
  "formula_version": "risk-v2-logistic",
  "risk_factors": [
    {"name": "engagement_drop", "weight": 0.35, "normalized_value": 0.76, "contribution": 26.6}
  ],
  "recommended_actions": [
    "Prioritize reliability fixes and set endpoint-level alert thresholds."
  ]
}
```

### Trend analysis payload (sample fields)

- daily revenue trend
- 7-day moving average
- anomaly list with method (`zscore` / `mad`)

## SQL Portfolio Assets

- `amids/sql/kpi_models.sql`
- `amids/sql/transformations.sql`
- `amids/sql/analytics_queries.sql`

These include:

- aggregations (`sum`, `avg`)
- joins between KPI and campaign facts
- window functions (`lag`, `avg over`, `rank`)
- risk-band distribution logic

## Scripts

`scripts/` includes:

- `data_cleaning.py` - cleans campaign data and enforces funnel consistency
- `feature_engineering.py` - builds CTR/CPC/CPL/ROI/risk features
- `batch_analysis.py` - runs batch summary stats, anomaly checks, KPI monitoring

## Project Structure

```text
cittaai_phase1_beta/
  backend/
    app/
      analytics/
      api/
      schemas/
      services/
      main.py
  amids/
    agents/
    dashboard/
    database/
    sql/
  scripts/
  data/
  tests/
  web/
```

## Run Locally

1. Create/activate venv
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
2. Install dependencies
   - `pip install -r requirements.txt`
3. Run FastAPI
   - `uvicorn backend.app.main:app --reload --port 8000`
4. Open web UI
   - `http://127.0.0.1:8000`

## Run AMIDS Pipeline

- Single run:
  - `python -m amids.main_orchestrator`
- Streamlit dashboard:
  - `streamlit run amids/dashboard/app.py`

## Run Scripts

- `python scripts/data_cleaning.py`
- `python scripts/feature_engineering.py`
- `python scripts/batch_analysis.py`

## Tests

- `pytest -q`

---

This project is intentionally structured to be explainable in interviews:
it demonstrates data engineering basics, analytical reasoning, statistical quality checks, API design, and dashboard enablement in one coherent workflow.
