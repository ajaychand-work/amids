from __future__ import annotations

from statistics import fmean, median, pvariance
from typing import Sequence


def calculate_summary_statistics(values: Sequence[float]) -> dict:
    """Return core summary stats used across dashboards and reports."""
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "variance": None,
            "min": None,
            "max": None,
        }

    numeric = [float(v) for v in values]
    return {
        "count": len(numeric),
        "mean": round(fmean(numeric), 4),
        "median": round(median(numeric), 4),
        "variance": round(pvariance(numeric), 4) if len(numeric) > 1 else 0.0,
        "min": round(min(numeric), 4),
        "max": round(max(numeric), 4),
    }


def detect_anomalies_zscore(values: Sequence[float], threshold: float = 2.5) -> list[dict]:
    """Detect outliers using standard z-score for normally distributed metrics."""
    if len(values) < 3:
        return []

    stats = calculate_summary_statistics(values)
    mean = stats["mean"]
    variance = stats["variance"]
    if mean is None or variance in (None, 0):
        return []

    std = variance ** 0.5
    anomalies: list[dict] = []
    for idx, value in enumerate(values):
        z_score = (float(value) - mean) / std if std > 0 else 0.0
        if abs(z_score) >= threshold:
            anomalies.append(
                {
                    "index": idx,
                    "value": float(value),
                    "method": "zscore",
                    "score": round(z_score, 4),
                    "threshold": threshold,
                }
            )
    return anomalies


def detect_anomalies_mad(values: Sequence[float], threshold: float = 3.5) -> list[dict]:
    """Detect robust outliers using median absolute deviation (MAD)."""
    if len(values) < 3:
        return []

    med = median(values)
    abs_dev = [abs(float(v) - med) for v in values]
    mad = median(abs_dev)
    if mad == 0:
        return []

    anomalies: list[dict] = []
    for idx, value in enumerate(values):
        modified_z = 0.6745 * (float(value) - med) / mad
        if abs(modified_z) >= threshold:
            anomalies.append(
                {
                    "index": idx,
                    "value": float(value),
                    "method": "mad",
                    "score": round(modified_z, 4),
                    "threshold": threshold,
                }
            )
    return anomalies


def monitor_kpis(
    metrics: dict[str, float],
    thresholds: dict[str, tuple[float | None, float | None]],
) -> list[dict]:
    """
    Classify KPI status against explicit monitoring thresholds.

    Threshold tuple format: (min_allowed, max_allowed).
    """
    statuses: list[dict] = []
    for name, value in metrics.items():
        low, high = thresholds.get(name, (None, None))
        status = "healthy"
        if low is not None and value < low:
            status = "critical"
        if high is not None and value > high:
            status = "critical"
        statuses.append(
            {
                "metric": name,
                "value": round(float(value), 4),
                "min_threshold": low,
                "max_threshold": high,
                "status": status,
            }
        )
    return statuses
