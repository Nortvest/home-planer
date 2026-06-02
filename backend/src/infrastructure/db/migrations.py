"""Мигратор схемы БД.

Читает Python-схемы из schema.ALL_TABLES и подстраивает БД:
- создаёт отсутствующие таблицы
- добавляет отсутствующие колонки
- создаёт отсутствующие индексы
- не удаляет ничего (безопасная миграция)
"""
import sqlite3

from src.infrastructure.db.connection import get_transaction
from src.infrastructure.db.schema import ALL_TABLES, SCHEMA_VERSION, Column, ForeignKey, Index


def _get_existing_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'",
    ).fetchall()
    return {r["name"] for r in rows}


def _get_existing_columns(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r["name"]: r["type"] for r in rows}


def _get_existing_indexes(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'",
    ).fetchall()
    return {r["name"] for r in rows}


_RESERVED_WORDS = {"user"}


def _quote(name: str) -> str:
    if name.lower() in _RESERVED_WORDS:
        return f'"{name}"'
    return name


def _column_def(col: Column) -> str:
    parts = [col.name, col.sql_type]
    if col.is_pk:
        if col.autoincrement:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        else:
            parts.append("PRIMARY KEY")
    if col.not_null and not col.is_pk:
        parts.append("NOT NULL")
    if col.default is not None and not col.is_pk:
        parts.append(f"DEFAULT {col.default}")
    return " ".join(parts)


def _fk_def(fk: ForeignKey) -> str:
    return f"FOREIGN KEY ({fk.column}) REFERENCES {_quote(fk.ref_table)}({fk.ref_column})"


def _sql_for_index(idx: Index) -> str:
    cols = ", ".join(idx.columns)
    unique = "UNIQUE " if idx.unique else ""
    sql = f"CREATE {unique}INDEX IF NOT EXISTS {idx.name} ON {_quote(idx.table)} ({cols})"
    if idx.where:
        sql += f" WHERE {idx.where}"
    return sql


def _migrate(conn: sqlite3.Connection) -> None:
    existing_tables = _get_existing_tables(conn)

    for table_name, spec in ALL_TABLES.items():
        _ensure_table(conn, table_name, spec, existing_tables)
        _ensure_indexes(conn, spec)

    _set_version(conn)


def _ensure_table(
    conn: sqlite3.Connection,
    table_name: str,
    spec: dict[str, object],
    existing_tables: set[str],
) -> None:
    columns: dict[str, Column] = spec["columns"]  # type: ignore[assignment]
    foreign_keys: list[ForeignKey] = spec["foreign_keys"]  # type: ignore[assignment]

    if table_name not in existing_tables:
        _create_table(conn, table_name, columns, foreign_keys)
        existing_tables.add(table_name)
    else:
        _add_missing_columns(conn, table_name, columns)


def _create_table(
    conn: sqlite3.Connection,
    table_name: str,
    columns: dict[str, Column],
    foreign_keys: list[ForeignKey],
) -> None:
    parts_col = [f"    {_column_def(col)}" for col in columns.values()]
    parts_col.extend(f"    {_fk_def(fk)}" for fk in foreign_keys)
    ddl_parts = [f"CREATE TABLE IF NOT EXISTS {_quote(table_name)} ("]
    ddl_parts.extend((",\n".join(parts_col), ")"))
    sql = "\n".join(ddl_parts)
    conn.execute(sql)


def _add_missing_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: dict[str, Column],
) -> None:
    existing_cols = _get_existing_columns(conn, table_name)
    for col in columns.values():
        if col.name not in existing_cols:
            alter = f"ALTER TABLE {_quote(table_name)} ADD COLUMN {_column_def(col)}"
            conn.execute(alter)


def _ensure_indexes(conn: sqlite3.Connection, spec: dict[str, object]) -> None:
    indexes: list[Index] = spec["indexes"]  # type: ignore[assignment]
    for idx in indexes:
        sql = _sql_for_index(idx)
        conn.execute(sql)


def _get_version(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'",
    ).fetchall()
    if not rows:
        return 0

    row = conn.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1",
    ).fetchone()
    return row["version"] if row else 0


def _set_version(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1",
    ).fetchone()
    current = row["version"] if row else 0

    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,),
        )


def init_if_needed(db_path: str | None = None) -> None:
    """Подстраивает БД под текущие Python-схемы."""
    with get_transaction(db_path) as conn:
        _migrate(conn)
