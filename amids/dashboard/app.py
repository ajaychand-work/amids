import sqlite3
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

# Ensure project root is on sys.path so `amids` package can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from amids.config import settings


DB_PATH = Path(settings.db_path)


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=300)
def load_kpis():
    with get_conn() as conn:
        return pd.read_sql(
            """
            select run_date, channel, region, cac, ltv, revenue_growth, channel_roi
            from kpi_summary_daily
            order by run_date, channel, region
            """,
            conn,
        )


@st.cache_data(ttl=300)
def load_anomalies():
    with get_conn() as conn:
        return pd.read_sql(
            """
            select detected_at, run_date, metric, dimension, anomaly_type, current_value, z_score
            from anomaly_log
            order by detected_at desc
            """,
            conn,
        )


@st.cache_data(ttl=300)
def load_forecasts():
    with get_conn() as conn:
        return pd.read_sql(
            """
            select created_at, metric, scenario, forecast
            from forecast_summary
            order by created_at desc
            """,
            conn,
        )


def main():
    st.set_page_config(page_title="AMIDS Marketing Intelligence", layout="wide")
    st.title("AMIDS – Marketing Intelligence Dashboard")

    if not DB_PATH.exists():
        st.warning("No AMIDS database found yet. Run the orchestrator first.")
        return

    tab_kpi, tab_anom, tab_forecast = st.tabs(
        ["KPI Overview", "Anomalies & Root Cause", "Forecasts"]
    )

    with tab_kpi:
        st.subheader("Daily KPIs by Channel / Region")
        kpis = load_kpis()
        if kpis.empty:
            st.info("No KPI data available yet.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                channel_filter = st.multiselect(
                    "Channels", sorted(kpis["channel"].dropna().unique().tolist())
                )
            with col2:
                region_filter = st.multiselect(
                    "Regions", sorted(kpis["region"].dropna().unique().tolist())
                )

            df = kpis.copy()
            if channel_filter:
                df = df[df["channel"].isin(channel_filter)]
            if region_filter:
                df = df[df["region"].isin(region_filter)]

            st.dataframe(df.tail(50), use_container_width=True)

            st.markdown("##### Revenue Growth Over Time")
            if not df.empty:
                pivot = (
                    df.pivot_table(
                        index="run_date",
                        columns="channel",
                        values="revenue_growth",
                        aggfunc="mean",
                    )
                    .sort_index()
                    .fillna(0.0)
                )
                st.line_chart(pivot)

    with tab_anom:
        st.subheader("Anomalies")
        anomalies = load_anomalies()
        if anomalies.empty:
            st.info("No anomalies detected yet.")
        else:
            st.dataframe(anomalies.head(100), use_container_width=True)

    with tab_forecast:
        st.subheader("Forecast Snapshots")
        forecasts = load_forecasts()
        if forecasts.empty:
            st.info("No forecasts stored yet.")
        else:
            st.dataframe(forecasts[["created_at", "metric", "scenario"]].head(20))


if __name__ == "__main__":
    main()

