from __future__ import annotations

import logging
from datetime import date

from ..db import get_connection


logger = logging.getLogger(__name__)


def run(run_date: date | None = None) -> None:
    """Run basic data quality checks and log results."""
    run_date = run_date or date.today()
    logger.info("Validation Agent: running checks for %s", run_date)

    with get_connection() as conn:
        cur = conn.cursor()
        run_str = run_date.isoformat()

        # Null checks and counts (SQLite syntax)
        cur.execute(
            """
            select
                sum(case when spend is null then 1 else 0 end) as spend_nulls,
                sum(case when revenue is null then 1 else 0 end) as revenue_nulls
            from campaign_performance_daily
            where run_date = ?
            """,
            (run_str,),
        )
        row = cur.fetchone()
        spend_nulls, revenue_nulls = row if row is not None else (0, 0)

        # Duplicate check on campaign/day
        cur.execute(
            """
            select count(*)
            from (
                select run_date, campaign_id, count(*) as c
                from campaign_performance_daily
                where run_date = ?
                group by run_date, campaign_id
                having count(*) > 1
            ) dup
            """,
            (run_str,),
        )
        duplicate_rows_row = cur.fetchone()
        duplicate_rows = duplicate_rows_row[0] if duplicate_rows_row else 0

        # Spend vs revenue reconciliation (basic sanity ratio)
        cur.execute(
            """
            select
                coalesce(sum(spend), 0) as total_spend,
                coalesce(sum(revenue), 0) as total_revenue
            from campaign_performance_daily
            where run_date = ?
            """,
            (run_str,),
        )
        ts_row = cur.fetchone()
        total_spend, total_revenue = ts_row if ts_row is not None else (0.0, 0.0)

    logger.info(
        "Validation Agent: spend_nulls=%s revenue_nulls=%s duplicate_rows=%s total_spend=%.2f total_revenue=%.2f",
        spend_nulls,
        revenue_nulls,
        duplicate_rows,
        float(total_spend),
        float(total_revenue),
    )

