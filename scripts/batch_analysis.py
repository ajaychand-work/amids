from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.analytics.metrics import (  # noqa: E402
    calculate_summary_statistics,
    detect_anomalies_mad,
    detect_anomalies_zscore,
    monitor_kpis,
)

DB_PATH = ROOT / "amids" / "amids.db"
FEATURE_PATH = ROOT / "data" / "engineered_campaign_features.csv"
OUT_PATH = ROOT / "data" / "batch_analysis_report.json"


def load_feature_data() -> pd.DataFrame:
    if FEATURE_PATH.exists():
        return pd.read_csv(FEATURE_PATH)

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("select * from campaign_performance_daily", conn)


def run_batch_analysis(df: pd.DataFrame) -> dict:
    roi_values = df.get("roi", pd.Series(dtype=float)).dropna().tolist()
    revenue_values = df.get("revenue", pd.Series(dtype=float)).dropna().tolist()
    spend_values = df.get("spend", pd.Series(dtype=float)).dropna().tolist()

    zscore_anomalies = detect_anomalies_zscore(revenue_values, threshold=2.2)
    mad_anomalies = detect_anomalies_mad(revenue_values, threshold=3.2)

    summary = {
        "revenue": calculate_summary_statistics(revenue_values),
        "spend": calculate_summary_statistics(spend_values),
        "roi": calculate_summary_statistics(roi_values),
    }
    kpi_monitor = monitor_kpis(
        metrics={
            "avg_revenue": summary["revenue"]["mean"] or 0.0,
            "avg_spend": summary["spend"]["mean"] or 0.0,
            "avg_roi": summary["roi"]["mean"] or 0.0,
        },
        thresholds={
            "avg_revenue": (10_000.0, None),
            "avg_spend": (None, 45_000.0),
            "avg_roi": (1.2, None),
        },
    )

    by_channel = (
        df.groupby("channel", dropna=False)
        .agg(
            revenue=("revenue", "sum"),
            spend=("spend", "sum"),
            leads=("leads", "sum"),
            clicks=("clicks", "sum"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    by_channel["roi"] = by_channel["revenue"] / by_channel["spend"].replace(0, pd.NA)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary_statistics": summary,
        "anomalies": {
            "zscore": zscore_anomalies[:20],
            "mad": mad_anomalies[:20],
        },
        "kpi_monitoring": kpi_monitor,
        "channel_rollup": by_channel.fillna(0).to_dict(orient="records"),
    }


def main() -> None:
    if not DB_PATH.exists() and not FEATURE_PATH.exists():
        raise FileNotFoundError(
            f"No analysis input found. Expected {DB_PATH} or {FEATURE_PATH}."
        )

    df = load_feature_data()
    report = run_batch_analysis(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved batch analysis report to {OUT_PATH}")


if __name__ == "__main__":
    main()
