from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
import sys

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from amids.config import BASE_DIR, settings
    from amids.db import execute_sql_file
    from amids.agents import (
        ai_insight_agent,
        anomaly_agent,
        dashboard_agent,
        data_agent,
        forecast_agent,
        kpi_agent,
        rootcause_agent,
        summary_stats_agent,
        validation_agent,
    )
else:
    from .config import BASE_DIR, settings
    from .db import execute_sql_file
    from .agents import (
        ai_insight_agent,
        anomaly_agent,
        dashboard_agent,
        data_agent,
        forecast_agent,
        kpi_agent,
        rootcause_agent,
        summary_stats_agent,
        validation_agent,
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


def _insert_execution_start() -> int:
    with sqlite3.connect(settings.db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "insert into execution_log (status, details) values (?, ?)",
            ("running", "AMIDS orchestrator started"),
        )
        return int(cur.lastrowid)


def _close_execution(run_id: int, status: str, details: str) -> None:
    with sqlite3.connect(settings.db_path) as conn:
        conn.execute(
            """
            update execution_log
            set finished_at = ?, status = ?, details = ?
            where id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), status, details, run_id),
        )


def run_daily(run_date: date | None = None) -> None:
    """Run the full AMIDS daily analytics workflow."""
    run_date = run_date or date.today()
    logger = logging.getLogger("amids.orchestrator")
    logger.info("Starting AMIDS daily run for %s", run_date)

    _ensure_schema()
    run_id = _insert_execution_start()

    try:
        data_agent.run(run_date)
        validation_agent.run(run_date)
        summary_stats_agent.run(run_date)
        kpi_agent.run(run_date)
        anomaly_agent.run(run_date)
        rootcause_agent.run()
        forecast_agent.run(run_date)
        ai_insight_agent.run(run_date)
        dashboard_agent.run()
    except Exception as exc:
        _close_execution(run_id, "failed", str(exc))
        logger.exception("AMIDS daily run failed for %s", run_date)
        raise

    _close_execution(run_id, "completed", "AMIDS orchestrator completed successfully")
    logger.info("Completed AMIDS daily run for %s", run_date)


if __name__ == "__main__":
    _setup_logging()
    run_daily()
