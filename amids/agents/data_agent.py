from __future__ import annotations

import logging
from datetime import date
from random import randint, uniform, choice

from ..db import get_connection


logger = logging.getLogger(__name__)


CHANNELS = ["paid_search", "paid_social", "email", "organic"]
REGIONS = ["APAC", "EMEA", "NA"]


def _generate_campaign_rows(run_date: date, days_back: int = 30) -> list[tuple]:
    rows: list[tuple] = []
    for d in range(days_back):
        day = run_date.fromordinal(run_date.toordinal() - d)
        for channel in CHANNELS:
            for region in REGIONS:
                campaign_id = f"{channel}_{region}_{d % 5}"
                impressions = randint(5_000, 50_000)
                clicks = int(impressions * uniform(0.01, 0.08))
                spend = round(uniform(200.0, 5_000.0), 2)
                leads = int(clicks * uniform(0.05, 0.25))
                opportunities = int(leads * uniform(0.1, 0.4))
                signups = int(opportunities * uniform(0.3, 0.7))
                arpu = uniform(50.0, 300.0)
                revenue = round(signups * arpu, 2)

                rows.append(
                    (
                        day,
                        campaign_id,
                        channel,
                        region,
                        impressions,
                        clicks,
                        spend,
                        leads,
                        opportunities,
                        signups,
                        revenue,
                    )
                )
    return rows


def run(run_date: date | None = None) -> None:
    """Fetch (simulated) campaign/CRM/revenue data and append to the warehouse."""
    run_date = run_date or date.today()
    logger.info("Data Agent: starting ingestion for %s", run_date)

    campaign_rows = _generate_campaign_rows(run_date)

    with get_connection() as conn:
        cur = conn.cursor()
        # store dates as ISO strings in SQLite
        cutoff = run_date.fromordinal(run_date.toordinal() - 30).isoformat()
        cur.execute(
            "delete from campaign_performance_daily where run_date >= ?",
            (cutoff,),
        )
        cur.executemany(
            """
            insert into campaign_performance_daily (
                run_date,
                campaign_id,
                channel,
                region,
                impressions,
                clicks,
                spend,
                leads,
                opportunities,
                signups,
                revenue
            )
            values (?,?,?,?,?,?,?,?,?,?,?)
            """,
            [(d.isoformat(), *rest) for (d, *rest) in campaign_rows],
        )

    logger.info("Data Agent: ingested %d campaign rows", len(campaign_rows))

