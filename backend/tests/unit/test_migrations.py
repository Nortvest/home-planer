"""Тесты миграций."""
from src.infrastructure.db.connection import get_connection
from src.infrastructure.db.migrations import init_if_needed


class TestMigrations:

    def test_init_creates_tables(self, db_path: str) -> None:
        conn = get_connection(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'",
        ).fetchall()
        names = {t["name"] for t in tables}
        assert "user" in names
        assert "task_template" in names
        assert "task_instance" in names
        assert "schema_version" in names
        conn.close()

    def test_schema_version_set(self, db_path: str) -> None:
        conn = get_connection(db_path)
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        assert row is not None
        assert row["version"] >= 1
        conn.close()

    def test_reinit_is_idempotent(self, db_path: str) -> None:
        init_if_needed(db_path)
        conn = get_connection(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'",
        ).fetchall()
        names = {t["name"] for t in tables}
        assert "user" in names
        assert "task_template" in names
        conn.close()

    def test_adds_missing_column(self, db_path: str) -> None:
        conn = get_connection(db_path)
        conn.execute("DROP TABLE IF EXISTS task_template")
        conn.execute(
            "CREATE TABLE task_template ("
            "id INTEGER PRIMARY KEY, "
            "title TEXT NOT NULL, "
            "sp_cost INTEGER NOT NULL DEFAULT 0, "
            "recurrence_type TEXT NOT NULL DEFAULT 'none', "
            "recurrence_params TEXT NOT NULL DEFAULT '{}', "
            "default_assignee_id INTEGER, "
            "active INTEGER NOT NULL DEFAULT 1, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")",
        )
        conn.close()
        init_if_needed(db_path)
        conn = get_connection(db_path)
        conn.execute("PRAGMA table_info(task_template)")
        conn.close()

    def test_adds_missing_index(self, db_path: str) -> None:
        conn = get_connection(db_path)
        conn.execute("DROP INDEX IF EXISTS idx_user_name_active")
        conn.close()
        init_if_needed(db_path)
        conn = get_connection(db_path)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND tbl_name='user'",
        ).fetchall()
        index_names = {i["name"] for i in indexes}
        assert "idx_user_name_active" in index_names
        conn.close()
