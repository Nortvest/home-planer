import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from src.infrastructure.settings import get_settings


def get_connection(path: str | None = None, timeout: float | None = None) -> sqlite3.Connection:
    """Создаёт новое соединение с SQLite."""
    settings = get_settings()
    db_path = path or settings.db_path_resolved
    parent = Path(db_path).parent
    parent.mkdir(parents=True, exist_ok=True)

    conn_timeout = timeout if timeout is not None else settings.DB_TIMEOUT

    conn = sqlite3.connect(db_path, timeout=conn_timeout)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    busy = settings.DB_BUSY_TIMEOUT
    conn.execute(f"PRAGMA busy_timeout={busy}")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_transaction(path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Контекстный менеджер для транзакции."""
    conn = get_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
