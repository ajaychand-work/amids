from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

from ..config import settings
from ..db import get_connection


logger = logging.getLogger(__name__)


def _fetch_context(start_date: date, end_date: date):
    with get_connection() as conn:
        cur = conn.cursor()
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        cur.execute(
            """
            select run_date, channel, region, cac, ltv, channel_roi, revenue_growth
            from kpi_summary_daily
            where run_date between ? and ?
            order by run_date, channel, region
            """,
            (start_str, end_str),
        )
        kpis = cur.fetchall()

        cur.execute(
            """
            select run_date, metric, dimension, anomaly_type, current_value, z_score
            from anomaly_log
            where run_date between ? and ?
            order by detected_at desc
            """,
            (start_str, end_str),
        )
        anomalies = cur.fetchall()

        cur.execute(
            """
            select metric, scenario, forecast
            from forecast_summary
            order by created_at desc
            limit 10
            """
        )
        forecasts = cur.fetchall()

        cur.execute(
            """
            select anomaly_id, factor_type, factor_value, impact_score, rank
            from root_cause_summary
            order by anomaly_id, rank
            """
        )
        root_causes = cur.fetchall()

    return kpis, anomalies, forecasts, root_causes


def _summarise(kpis, anomalies, forecasts, root_causes) -> str:
    lines: list[str] = []

    lines.append("AMIDS Executive Weekly Summary")
    lines.append("=" * 32)
    lines.append("")

    if kpis:
        lines.append("Key performance trends:")
        for row in kpis[:20]:
            day, channel, region, cac, ltv, roi, growth = row
            cac_str = f"{cac:.2f}" if cac is not None else "0.00"
            ltv_str = f"{ltv:.2f}" if ltv is not None else "0.00"
            roi_str = f"{roi:.2f}" if roi is not None else "0.00"
            growth_str = f"{growth:.2%}" if growth is not None else "0.00%"
            lines.append(
                f"- {day} {channel}/{region}: CAC={cac_str}, "
                f"LTV={ltv_str}, ROI={roi_str}, "
                f"Rev growth={growth_str}"
            )

    lines.append("")

    if anomalies:
        lines.append("Detected anomalies:")
        for row in anomalies[:10]:
            day, metric, dimension, anomaly_type, value, z = row
            lines.append(
                f"- {day} | {metric} | {dimension} | {anomaly_type} | value={value} z={z}"
            )
    else:
        lines.append("No anomalies detected in the period.")

    lines.append("")

    if forecasts:
        lines.append("Forecast highlights (next 4 weeks):")
        for metric, scenario, forecast in forecasts:
            try:
                data = json.loads(forecast)
                last_point = data.get("points", [])[-1] if data.get("points") else None
                if last_point:
                    lines.append(
                        f"- {metric} ({scenario}) expected around {last_point['value']:.2f} by {last_point['date']}"
                    )
            except Exception:
                continue

    lines.append("")
    if root_causes:
        lines.append("Top impact drivers:")
        for anomaly_id, factor_type, factor_value, impact_score, rank in root_causes[:10]:
            lines.append(
                f"- Anomaly {anomaly_id} | {factor_type}={factor_value} | impact_score={impact_score:.2f} (rank {rank})"
            )

    lines.append("")
    lines.append("Budget reallocation suggestions (heuristic):")
    lines.append(
        "- Shift incremental budget into channels with positive revenue growth and ROI above 1.5x; "
        "de-prioritise segments with persistent CAC spikes."
    )

    return "\n".join(lines)


def run(as_of: date | None = None) -> Path:
    """Generate an executive summary text report."""
    as_of = as_of or date.today()
    start_date = as_of - timedelta(days=7)

    logger.info("AI Insight Agent: generating summary for %s - %s", start_date, as_of)

    kpis, anomalies, forecasts, root_causes = _fetch_context(start_date, as_of)
    report_text = _summarise(kpis, anomalies, forecasts, root_causes)

    out_path = settings.reports_dir / f"executive_summary_{as_of.isoformat()}.txt"
    out_path.write_text(report_text, encoding="utf-8")

    logger.info("AI Insight Agent: wrote %s", out_path)
    return out_path

