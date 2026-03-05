from __future__ import annotations

from pathlib import Path
import sqlite3

from ..analytics.metrics import (
    calculate_summary_statistics,
    detect_anomalies_mad,
    detect_anomalies_zscore,
    monitor_kpis,
)
from ..analytics.sql_queries import (
    ENGAGEMENT_PERFORMANCE_QUERY,
    REVENUE_TREND_QUERY,
    RISK_DISTRIBUTION_QUERY,
    SUMMARY_STATS_QUERY,
)

ROOT = Path(__file__).resolve().parents[3]
AMIDS_DB_PATH = ROOT / "amids" / "amids.db"


def _query(sql: str, params: tuple = ()) -> list[dict]:
    if not AMIDS_DB_PATH.exists():
        return []

    with sqlite3.connect(AMIDS_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_kpi_dashboard(days: int = 30) -> dict:
    period = f"-{days} day"
    rows = _query(ENGAGEMENT_PERFORMANCE_QUERY, (period,))

    roi_values = [
        float(row["channel_roi"])
        for row in rows
        if row.get("channel_roi") is not None
    ]
    cac_values = [
        float(row["cac"])
        for row in rows
        if row.get("cac") is not None
    ]
    cvr_values = [
        (float(row["leads"]) / float(row["clicks"]))
        for row in rows
        if row.get("clicks") and float(row["clicks"]) > 0
    ]
    summary = {
        "roi": calculate_summary_statistics(roi_values),
        "cac": calculate_summary_statistics(cac_values),
        "lead_conversion_rate": calculate_summary_statistics(cvr_values),
    }

    latest = rows[:25]
    return {
        "window_days": days,
        "summary_stats": summary,
        "latest_segments": latest,
    }


def get_trend_analysis(days: int = 30) -> dict:
    period = f"-{days} day"
    rows = _query(REVENUE_TREND_QUERY, (period,))
    revenue_values = [float(row["revenue"]) for row in rows if row.get("revenue") is not None]

    anomalies = []
    zscore_hits = detect_anomalies_zscore(revenue_values, threshold=2.2)
    mad_hits = detect_anomalies_mad(revenue_values, threshold=3.2)

    index_to_date = {
        idx: row.get("run_date")
        for idx, row in enumerate(rows)
    }
    for hit in zscore_hits + mad_hits:
        anomalies.append(
            {
                "run_date": index_to_date.get(hit["index"]),
                "value": hit["value"],
                "method": hit["method"],
                "score": hit["score"],
                "threshold": hit["threshold"],
            }
        )

    return {
        "window_days": days,
        "summary_stats": calculate_summary_statistics(revenue_values),
        "trends": rows,
        "anomalies": anomalies,
    }


def get_performance_metrics(days: int = 30) -> dict:
    period = f"-{days} day"
    risk_distribution = _query(RISK_DISTRIBUTION_QUERY, (period,))
    summary_rows = _query(SUMMARY_STATS_QUERY, (period,))
    summary = summary_rows[0] if summary_rows else {}

    monitored = monitor_kpis(
        metrics={
            "avg_revenue": float(summary.get("avg_revenue") or 0.0),
            "avg_spend": float(summary.get("avg_spend") or 0.0),
            "avg_clicks": float(summary.get("avg_clicks") or 0.0),
            "avg_leads": float(summary.get("avg_leads") or 0.0),
        },
        thresholds={
            "avg_revenue": (10_000.0, None),
            "avg_spend": (None, 45_000.0),
            "avg_clicks": (250.0, None),
            "avg_leads": (40.0, None),
        },
    )

    return {
        "window_days": days,
        "summary": summary,
        "risk_distribution": risk_distribution,
        "kpi_monitoring": monitored,
    }
