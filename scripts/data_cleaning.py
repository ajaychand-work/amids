from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "amids" / "amids.db"
OUT_PATH = ROOT / "data" / "cleaned_campaign_data.csv"


def load_campaign_data() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("select * from campaign_performance_daily", conn)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    # Enforce non-negative numeric values for key performance fields.
    numeric_cols = [
        "impressions",
        "clicks",
        "spend",
        "leads",
        "opportunities",
        "signups",
        "revenue",
    ]
    for col in numeric_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").fillna(0)
        cleaned[col] = cleaned[col].clip(lower=0)

    # Remove exact duplicate rows from ingestion reruns.
    cleaned = cleaned.drop_duplicates()

    # Keep only rows with basic funnel consistency.
    cleaned = cleaned[cleaned["clicks"] <= cleaned["impressions"]]
    cleaned = cleaned[cleaned["leads"] <= cleaned["clicks"]]
    cleaned = cleaned[cleaned["signups"] <= cleaned["opportunities"]]

    cleaned["run_date"] = pd.to_datetime(cleaned["run_date"]).dt.date
    return cleaned.sort_values(["run_date", "channel", "region"]).reset_index(drop=True)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"AMIDS database not found at {DB_PATH}")

    df = load_campaign_data()
    cleaned = clean_data(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUT_PATH, index=False)
    print(f"Saved cleaned data to {OUT_PATH} ({len(cleaned)} rows)")


if __name__ == "__main__":
    main()
