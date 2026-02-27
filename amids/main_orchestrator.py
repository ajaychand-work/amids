from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from .config import settings, BASE_DIR
from .db import execute_sql_file
from .agents import (
    data_agent,
    validation_agent,
    kpi_agent,
    anomaly_agent,
    rootcause_agent,
    forecast_agent,
    ai_insight_agent,
    dashboard_agent,
)


def _setup_logging() -> None:
    log_file = settings.log_dir / "amids.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _ensure_schema() -> None:
    schema_path = BASE_DIR / "database" / "schema.sql"
    execute_sql_file(schema_path)


def run_daily(run_date: date | None = None) -> None:
    """Run the full AMIDS daily pipeline."""
    run_date = run_date or date.today()
    logger = logging.getLogger("amids.orchestrator")
    logger.info("Starting AMIDS daily run for %s", run_date)

    _ensure_schema()

    data_agent.run(run_date)
    validation_agent.run(run_date)
    kpi_agent.run(run_date)
    anomaly_agent.run(run_date)
    rootcause_agent.run()
    forecast_agent.run(run_date)
    ai_insight_agent.run(run_date)
    dashboard_agent.run()

    logger.info("Completed AMIDS daily run for %s", run_date)


if __name__ == "__main__":
    _setup_logging()
    run_daily()

