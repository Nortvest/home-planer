"""Python-схемы таблиц.

Мигратор считывает эти описания и подстраивает БД:
добавляет отсутствующие таблицы, колонки, индексы, FK-ограничения.
"""
from dataclasses import dataclass

from src.domain.value_objects import RecurrenceType

SCHEMA_VERSION: int = 1


@dataclass(frozen=True)
class Column:
    name: str
    sql_type: str
    not_null: bool = False
    default: str | None = None
    is_pk: bool = False
    autoincrement: bool = False


@dataclass(frozen=True)
class ForeignKey:
    column: str
    ref_table: str
    ref_column: str = "id"


@dataclass(frozen=True)
class Index:
    name: str
    table: str
    columns: list[str]
    unique: bool = False
    where: str | None = None


def _columns(columns: list[Column]) -> dict[str, Column]:
    return {c.name: c for c in columns}


# -- user --
user_columns = _columns([
    Column("id", "INTEGER", is_pk=True, autoincrement=True),
    Column("name", "TEXT", not_null=True),
    Column("color", "TEXT", not_null=True),
    Column("active", "INTEGER", not_null=True, default="1"),
    Column("created_at", "TEXT", not_null=True, default="(datetime('now'))"),
])

user_indexes: list[Index] = [
    Index("idx_user_name_active", "user", ["name"], unique=True, where="active = 1"),
]

user_foreign_keys: list[ForeignKey] = []

# -- task_template --
template_columns = _columns([
    Column("id", "INTEGER", is_pk=True, autoincrement=True),
    Column("title", "TEXT", not_null=True),
    Column("description", "TEXT"),
    Column("sp_cost", "INTEGER", not_null=True, default="0"),
    Column("recurrence_type", "TEXT", not_null=True, default=f"'{RecurrenceType.NONE.value}'"),
    Column("recurrence_params", "TEXT", not_null=True, default="'{}'"),
    Column("default_assignee_id", "INTEGER"),
    Column("active", "INTEGER", not_null=True, default="1"),
    Column("created_at", "TEXT", not_null=True, default="(datetime('now'))"),
])

template_indexes: list[Index] = [
    Index("idx_template_active", "task_template", ["active"]),
]

template_foreign_keys: list[ForeignKey] = [
    ForeignKey("default_assignee_id", "user"),
]

# -- task_instance --
instance_columns = _columns([
    Column("id", "INTEGER", is_pk=True, autoincrement=True),
    Column("template_id", "INTEGER"),
    Column("title", "TEXT", not_null=True),
    Column("scheduled_date", "TEXT", not_null=True),
    Column("assignee_id", "INTEGER"),
    Column("completed_at", "TEXT"),
    Column("completed_by_id", "INTEGER"),
    Column("sp_cost_at_completion", "INTEGER"),
    Column("created_at", "TEXT", not_null=True, default="(datetime('now'))"),
])

instance_indexes: list[Index] = [
    Index("idx_instance_scheduled_date", "task_instance", ["scheduled_date"]),
    Index("idx_instance_assignee", "task_instance", ["assignee_id"]),
    Index("idx_instance_template_date", "task_instance", ["template_id", "scheduled_date"]),
    Index("idx_instance_completed", "task_instance", ["completed_at", "completed_by_id"]),
]

instance_foreign_keys: list[ForeignKey] = [
    ForeignKey("template_id", "task_template"),
    ForeignKey("assignee_id", "user"),
    ForeignKey("completed_by_id", "user"),
]

# -- task_transfer --
transfer_columns = _columns([
    Column("id", "INTEGER", is_pk=True, autoincrement=True),
    Column("instance_id", "INTEGER", not_null=True),
    Column("from_user_id", "INTEGER"),
    Column("to_user_id", "INTEGER", not_null=True),
    Column("transferred_at", "TEXT", not_null=True, default="(datetime('now'))"),
])

transfer_indexes: list[Index] = [
    Index("idx_transfer_instance", "task_transfer", ["instance_id"]),
]

transfer_foreign_keys: list[ForeignKey] = [
    ForeignKey("instance_id", "task_instance"),
    ForeignKey("from_user_id", "user"),
    ForeignKey("to_user_id", "user"),
]

# -- schema_version --
version_columns = _columns([
    Column("version", "INTEGER", is_pk=True),
])

version_indexes: list[Index] = []
version_foreign_keys: list[ForeignKey] = []


_ALL_TABLES_RAW: dict[str, dict[str, object]] = {
    "schema_version": {
        "columns": version_columns,
        "indexes": version_indexes,
        "foreign_keys": version_foreign_keys,
    },
    "user": {
        "columns": user_columns,
        "indexes": user_indexes,
        "foreign_keys": user_foreign_keys,
    },
    "task_template": {
        "columns": template_columns,
        "indexes": template_indexes,
        "foreign_keys": template_foreign_keys,
    },
    "task_instance": {
        "columns": instance_columns,
        "indexes": instance_indexes,
        "foreign_keys": instance_foreign_keys,
    },
    "task_transfer": {
        "columns": transfer_columns,
        "indexes": transfer_indexes,
        "foreign_keys": transfer_foreign_keys,
    },
}

# Typed version for the migrator
ALL_TABLES: dict[str, dict[str, object]] = _ALL_TABLES_RAW
