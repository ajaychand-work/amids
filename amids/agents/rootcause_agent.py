from __future__ import annotations

import logging

from ..db import get_connection


logger = logging.getLogger(__name__)


def run() -> None:
    """For each anomaly, attribute impact across channel/region/segment."""
    logger.info("Root Cause Agent: starting analysis")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            select id, run_date, metric, dimension
            from anomaly_log
            where id not in (
                select distinct anomaly_id from root_cause_summary
            )
            order by detected_at asc
            """
        )
        anomalies = cur.fetchall()

        for anomaly_id, run_date, metric, dimension in anomalies:
            # Simple heuristic: use channel/region in dimension to rank impact by ROI.
            if dimension and ":" in dimension:
                channel, region = dimension.split(":", 1)
            else:
                channel, region = None, None

            cur.execute(
                """
                select
                    channel,
                    region,
                    avg(channel_roi) as roi
                from kpi_summary_daily
                where run_date = ?
                group by channel, region
                order by roi desc
                limit 5
                """,
                (run_date,),
            )
            factors = cur.fetchall()

            rank = 1
            for ch, rg, roi in factors:
                cur.execute(
                    """
                    insert into root_cause_summary (
                        anomaly_id,
                        factor_type,
                        factor_value,
                        impact_score,
                        rank
                    )
                    values (?,?,?,?,?)
                    """,
                    (
                        anomaly_id,
                        "channel_region",
                        f"{ch}:{rg}",
                        roi or 0.0,
                        rank,
                    ),
                )
                rank += 1

    logger.info("Root Cause Agent: completed for %d anomalies", len(anomalies))

