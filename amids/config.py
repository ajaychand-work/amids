import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Settings:
    """Central configuration for AMIDS."""

    # Use a local SQLite database file by default so no external DB
    # is required. You can override this path with AMIDS_DB_PATH.
    db_path: Path = Path(os.getenv("AMIDS_DB_PATH", BASE_DIR / "amids.db"))
    log_dir: Path = BASE_DIR / "logs"
    reports_dir: Path = BASE_DIR / "reports"
    dashboard_dir: Path = BASE_DIR / "dashboard"


settings = Settings()

settings.log_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
settings.dashboard_dir.mkdir(parents=True, exist_ok=True)

