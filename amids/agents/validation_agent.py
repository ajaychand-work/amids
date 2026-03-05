from __future__ import annotations

import logging
from datetime import date

from ..db import get_connection


logger = logging.getLogger(__name__)


def _record_check(
    checks: list[tuple],
    run_str: str,
    check_name: str,
    observed: float,
    threshold: float | None,
    status: str,
    details: str,
) -> None:
    checks.append((run_str, check_name, status, observed, threshold, details))


def run(run_date: date | None = None) -> None:
    """Run data quality checks and persist outcomes for monitoring."""
    run_date = run_date or date.today()
    run_str = run_date.isoformat()
    logger.info("Validation Agent: running checks for %s", run_str)

    checks: list[tuple] = []

    with get_connection() as conn:
        cur = conn.cursor()

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
        spend_nulls, revenue_nulls = cur.fetchone() or (0, 0)
        _record_check(
            checks,
            run_str,
            "null_check_spend",
            float(spend_nulls or 0),
            0.0,
            "pass" if (spend_nulls or 0) == 0 else "fail",
            "Spend should never be null in campaign data.",
        )
        _record_check(
            checks,
            run_str,
            "null_check_revenue",
            float(revenue_nulls or 0),
            0.0,
            "pass" if (revenue_nulls or 0) == 0 else "fail",
            "Revenue should never be null in campaign data.",
        )

        cur.execute(
            """
            select count(*)
            from (
                select run_date, campaign_id, count(*) as dup_count
                from campaign_performance_daily
                where run_date = ?
                group by run_date, campaign_id
                having count(*) > 1
            ) d
            """,
            (run_str,),
        )
        duplicate_rows = cur.fetchone()[0]
        _record_check(
            checks,
            run_str,
            "duplicate_campaign_day",
            float(duplicate_rows),
            0.0,
            "pass" if duplicate_rows == 0 else "fail",
            "Campaign/day records should be unique.",
        )

        cur.execute(
            """
            select
                coalesce(sum(case when clicks > impressions then 1 else 0 end), 0) as bad_ctr_rows,
                coalesce(sum(case when leads > clicks then 1 else 0 end), 0) as bad_lead_rows,
                coalesce(sum(case when signups > opportunities then 1 else 0 end), 0) as bad_signup_rows
            from campaign_performance_daily
            where run_date = ?
            """,
            (run_str,),
        )
        bad_ctr_rows, bad_lead_rows, bad_signup_rows = cur.fetchone() or (0, 0, 0)
        total_funnel_violations = (bad_ctr_rows or 0) + (bad_lead_rows or 0) + (bad_signup_rows or 0)
        _record_check(
            checks,
            run_str,
            "funnel_consistency",
            float(total_funnel_violations),
            0.0,
            "pass" if total_funnel_violations == 0 else "fail",
            "Click <= impression, lead <= click, signup <= opportunity.",
        )

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
        total_spend, total_revenue = cur.fetchone() or (0.0, 0.0)
        roi = (float(total_revenue) / float(total_spend)) if float(total_spend) > 0 else 0.0
        _record_check(
            checks,
            run_str,
            "roi_sanity",
            roi,
            0.1,
            "pass" if roi >= 0.1 else "warn",
            "Daily ROI is unusually low when below 0.1.",
        )

        cur.execute("delete from data_quality_log where run_date = ?", (run_str,))
        cur.executemany(
            """
            insert into data_quality_log (
                run_date,
                check_name,
                status,
                observed_value,
                threshold_value,
                details
            )
            values (?,?,?,?,?,?)
            """,
            checks,
        )

    failed = sum(1 for _, _, status, *_ in checks if status == "fail")
    warned = sum(1 for _, _, status, *_ in checks if status == "warn")
    logger.info(
        "Validation Agent: completed %d checks (%d fail, %d warn)",
        len(checks),
        failed,
        warned,
    )
