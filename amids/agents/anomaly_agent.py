from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from ..db import get_connection


logger = logging.getLogger(__name__)


def _mad_score(series: pd.Series) -> pd.Series:
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0 or pd.isna(mad):
        return pd.Series([pd.NA] * len(series), index=series.index)
    return 0.6745 * (series - median) / mad


def run(run_date: date | None = None, z_threshold: float = 2.0, mad_threshold: float = 3.0) -> None:
    """Detect KPI anomalies using rolling z-scores and robust MAD checks."""
    run_date = run_date or date.today()
    run_str = run_date.isoformat()
    logger.info("Anomaly Agent: detecting anomalies for %s", run_str)

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
    anomalies: list[tuple] = []

    for (channel, region), group in df.groupby(["channel", "region"]):
        group = group.sort_values("run_date").reset_index(drop=True)
        if group.empty:
            continue

        # Rolling z-score catches short-term spikes compared to recent behavior.
        roll = group.rolling(window=15, on="run_date", min_periods=5)
        mean_cac = roll["cac"].mean()
        std_cac = roll["cac"].std()
        mean_rev = roll["revenue_growth"].mean()
        std_rev = roll["revenue_growth"].std()

        z_cac = (group["cac"] - mean_cac) / std_cac.replace(0, pd.NA)
        z_rev = (group["revenue_growth"] - mean_rev) / std_rev.replace(0, pd.NA)

        # MAD is more robust when heavy tails distort standard deviation.
        mad_cac = _mad_score(group["cac"].fillna(0.0))
        mad_rev = _mad_score(group["revenue_growth"].fillna(0.0))

        for idx, row in group.iterrows():
            day = row["run_date"].date().isoformat()
            if day != run_str:
                continue

            cac = row["cac"]
            rev_growth = row["revenue_growth"]
            zc = z_cac.loc[idx]
            zr = z_rev.loc[idx]
            mc = mad_cac.loc[idx]
            mr = mad_rev.loc[idx]

            if pd.notna(zc) and zc > z_threshold:
                anomalies.append(
                    (
                        day,
                        "cac",
                        f"{channel}:{region}",
                        "cac_spike_zscore",
                        float(cac) if cac is not None else None,
                        float(mean_cac.loc[idx]) if pd.notna(mean_cac.loc[idx]) else None,
                        float(zc),
                        "Detected by rolling z-score",
                    )
                )
            if pd.notna(mc) and mc > mad_threshold:
                anomalies.append(
                    (
                        day,
                        "cac",
                        f"{channel}:{region}",
                        "cac_spike_mad",
                        float(cac) if cac is not None else None,
                        None,
                        float(mc),
                        "Detected by MAD robust score",
                    )
                )

            if pd.notna(zr) and zr < -z_threshold:
                anomalies.append(
                    (
                        day,
                        "revenue_growth",
                        f"{channel}:{region}",
                        "revenue_drop_zscore",
                        float(rev_growth) if rev_growth is not None else None,
                        float(mean_rev.loc[idx]) if pd.notna(mean_rev.loc[idx]) else None,
                        float(zr),
                        "Detected by rolling z-score",
                    )
                )
            if pd.notna(mr) and mr < -mad_threshold:
                anomalies.append(
                    (
                        day,
                        "revenue_growth",
                        f"{channel}:{region}",
                        "revenue_drop_mad",
                        float(rev_growth) if rev_growth is not None else None,
                        None,
                        float(mr),
                        "Detected by MAD robust score",
                    )
                )

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("delete from anomaly_log where run_date = ?", (run_str,))
        if anomalies:
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

    if not anomalies:
        logger.info("Anomaly Agent: no anomalies found for %s", run_str)
        return

    logger.info("Anomaly Agent: inserted %d anomalies", len(anomalies))
