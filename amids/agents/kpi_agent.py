from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from ..config import BASE_DIR
from ..db import get_connection


logger = logging.getLogger(__name__)


def run(run_date: date | None = None) -> None:
    """Compute marketing KPIs and store in kpi_summary_daily."""
    run_date = run_date or date.today()
    logger.info("KPI Agent: computing KPIs up to %s", run_date)

    sql_path = BASE_DIR / "sql" / "kpi_models.sql"

    with sql_path.open("r", encoding="utf-8") as f:
        sql = f.read()

    with get_connection() as conn:
        cur = conn.cursor()
        # For simplicity we recompute KPIs using all available history.
        cur.execute("delete from kpi_summary_daily where run_date <= ?", (run_date.isoformat(),))
        cur.executescript(sql)

    logger.info("KPI Agent: KPI snapshot refreshed")

