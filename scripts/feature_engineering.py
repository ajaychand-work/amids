from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "cleaned_campaign_data.csv"
OUT_PATH = ROOT / "data" / "engineered_campaign_features.csv"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Core funnel and efficiency features for downstream KPI and risk analysis.
    out["ctr"] = np.where(out["impressions"] > 0, out["clicks"] / out["impressions"], 0.0)
    out["cpc"] = np.where(out["clicks"] > 0, out["spend"] / out["clicks"], 0.0)
    out["cpl"] = np.where(out["leads"] > 0, out["spend"] / out["leads"], 0.0)
    out["signup_rate"] = np.where(out["opportunities"] > 0, out["signups"] / out["opportunities"], 0.0)
    out["lead_to_signup_rate"] = np.where(out["leads"] > 0, out["signups"] / out["leads"], 0.0)
    out["roi"] = np.where(out["spend"] > 0, out["revenue"] / out["spend"], 0.0)

    # Heuristic risk signal that combines low conversion, high cost, and low ROI.
    out["risk_signal"] = (
        (1.0 - out["lead_to_signup_rate"].clip(0, 1)) * 40
        + (out["cpl"].clip(0, 500) / 500) * 35
        + (1.0 - (out["roi"].clip(0, 3) / 3.0)) * 25
    ).clip(0, 100)

    return out


def main() -> None:
    if not IN_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found at {IN_PATH}. Run scripts/data_cleaning.py first."
        )

    df = pd.read_csv(IN_PATH)
    features = build_features(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUT_PATH, index=False)
    print(f"Saved engineered features to {OUT_PATH} ({len(features)} rows)")


if __name__ == "__main__":
    main()
