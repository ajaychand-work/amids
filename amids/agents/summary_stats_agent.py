from __future__ import annotations

import logging
from datetime import date

from ..db import get_connection


logger = logging.getLogger(__name__)


def run(run_date: date | None = None) -> None:
    """Persist daily dataset summary metrics for monitoring and reporting."""
    run_date = run_date or date.today()
    run_str = run_date.isoformat()
    logger.info("Summary Stats Agent: computing dataset summaries for %s", run_str)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            select
                avg(spend) as avg_spend,
                avg(revenue) as avg_revenue,
                avg(clicks) as avg_clicks,
                avg(leads) as avg_leads,
                avg(signups) as avg_signups
            from campaign_performance_daily
            where run_date = ?
            """,
            (run_str,),
        )
        row = cur.fetchone()
        if not row:
            logger.info("Summary Stats Agent: no data found for %s", run_str)
            return

        metric_pairs = [
            ("avg_spend", row[0] or 0.0),
            ("avg_revenue", row[1] or 0.0),
            ("avg_clicks", row[2] or 0.0),
            ("avg_leads", row[3] or 0.0),
            ("avg_signups", row[4] or 0.0),
        ]

        cur.execute(
            "delete from dataset_summary_daily where run_date = ? and dataset_name = ?",
            (run_str, "campaign_performance_daily"),
        )
        cur.executemany(
            """
            insert into dataset_summary_daily (run_date, dataset_name, metric_name, value)
            values (?,?,?,?)
            """,
            [(run_str, "campaign_performance_daily", name, float(value)) for name, value in metric_pairs],
        )

    logger.info("Summary Stats Agent: stored %d summary metrics", len(metric_pairs))
