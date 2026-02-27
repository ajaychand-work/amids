from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
import sqlite3

from .config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Return a SQLite connection to the local AMIDS DB file."""
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_sql_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        sql = f.read()
    with get_connection() as conn:
        conn.executescript(sql)

