from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from ..db import get_connection


logger = logging.getLogger(__name__)


def run(run_date: date | None = None, z_threshold: float = 2.0) -> None:
    """Detect anomalies on revenue and CAC using rolling z-scores (SQLite-safe)."""
    run_date = run_date or date.today()
    logger.info("Anomaly Agent: detecting anomalies for %s", run_date)

    with get_connection() as conn:
        df = pd.read_sql(
            """
            select
                run_date,
                channel,
                region,
                cac,
                revenue_growth
            from kpi_summary_daily
            order by run_date
            """,
            conn,
        )

    if df.empty:
        logger.info("Anomaly Agent: no KPI data available")
        return

    df["run_date"] = pd.to_datetime(df["run_date"])

    anomalies = []

    for (channel, region), group in df.groupby(["channel", "region"]):
        group = group.sort_values("run_date")
        # 15-day rolling window
        roll = group.rolling(window=15, on="run_date", min_periods=5)

        mean_cac = roll["cac"].mean()
        std_cac = roll["cac"].std()
        mean_rev = roll["revenue_growth"].mean()
        std_rev = roll["revenue_growth"].std()

        z_cac = (group["cac"] - mean_cac) / std_cac.replace(0, pd.NA)
        z_rev = (group["revenue_growth"] - mean_rev) / std_rev.replace(0, pd.NA)

        for idx, row in group.iterrows():
            day = row["run_date"].date()
            cac = row["cac"]
            rev_growth = row["revenue_growth"]
            zc = z_cac.loc[idx]
            zr = z_rev.loc[idx]

            if pd.notna(zc) and zc > z_threshold:
                anomalies.append(
                    (
                        day.isoformat(),
                        "cac",
                        f"{channel}:{region}",
                        "cac_spike",
                        float(cac) if cac is not None else None,
                        None,
                        float(zc),
                        None,
                    )
                )

            if pd.notna(zr) and zr < -z_threshold:
                anomalies.append(
                    (
                        day.isoformat(),
                        "revenue_growth",
                        f"{channel}:{region}",
                        "revenue_drop",
                        float(rev_growth) if rev_growth is not None else None,
                        None,
                        float(zr),
                        None,
                    )
                )

    if not anomalies:
        logger.info("Anomaly Agent: no anomalies found")
        return

    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(
            """
            insert into anomaly_log (
                run_date,
                metric,
                dimension,
                anomaly_type,
                current_value,
                expected_value,
                z_score,
                details
            )
            values (?,?,?,?,?,?,?,?)
            """,
            anomalies,
        )

    logger.info("Anomaly Agent: inserted %d anomalies", len(anomalies))


