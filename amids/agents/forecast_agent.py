from __future__ import annotations

import json
import logging
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ..db import get_connection


logger = logging.getLogger(__name__)


def _fit_trend(df: pd.DataFrame, value_col: str, horizon_days: int = 28) -> dict:
    if df.empty:
        return {}

    df = df.sort_values("run_date")
    df["run_date"] = pd.to_datetime(df["run_date"])
    df["t"] = (df["run_date"] - df["run_date"].min()).dt.days

    X = df[["t"]].values
    y = df[value_col].values
    model = LinearRegression()
    model.fit(X, y)

    last_t = df["t"].max()
    forecast_points = []
    for i in range(1, horizon_days + 1):
        t_future = last_t + i
        y_pred = float(model.predict(np.array([[t_future]]))[0])
        day = df["run_date"].max() + pd.Timedelta(days=i)
        forecast_points.append({"date": day.date().isoformat(), "value": y_pred})

    return {"history_start": df["run_date"].min().date().isoformat(), "points": forecast_points}


def run(run_date: date | None = None) -> None:
    """Produce revenue and lead forecasts and store in forecast_summary."""
    run_date = run_date or date.today()
    logger.info("Forecast Agent: building forecasts as of %s", run_date)

    with get_connection() as conn:
        revenue_df = pd.read_sql(
            """
            select run_date, sum(revenue) as revenue
            from campaign_performance_daily
            group by run_date
            order by run_date
            """,
            conn,
        )

        leads_df = pd.read_sql(
            """
            select run_date, sum(leads) as leads
            from campaign_performance_daily
            group by run_date
            order by run_date
            """,
            conn,
        )

        revenue_forecast = _fit_trend(revenue_df, "revenue")
        leads_forecast = _fit_trend(leads_df, "leads")

        cur = conn.cursor()
        if revenue_forecast:
            cur.execute(
                """
                insert into forecast_summary (horizon_weeks, metric, scenario, forecast)
                values (?,?,?,?)
                """,
                (4, "revenue", "baseline", json.dumps(revenue_forecast)),
            )

        if leads_forecast:
            cur.execute(
                """
                insert into forecast_summary (horizon_weeks, metric, scenario, forecast)
                values (?,?,?,?)
                """,
                (4, "leads", "baseline", json.dumps(leads_forecast)),
            )

    logger.info("Forecast Agent: forecasts stored")

