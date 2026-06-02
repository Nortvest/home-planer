"""SQLite-реализация TaskTemplateRepository."""
import json
import sqlite3
from datetime import datetime, timezone

from src.application.ports.template_repo import TemplateRepository
from src.domain.entities import TaskTemplate
from src.domain.value_objects import RecurrenceType
from src.infrastructure.db.connection import get_connection, get_transaction


class SqliteTemplateRepository(TemplateRepository):
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def get(self, template_id: int) -> TaskTemplate | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM task_template WHERE id = ?", (template_id,),
            ).fetchone()
            if row is None:
                return None
            return self._to_template(row)

    def list_all(self) -> list[TaskTemplate]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_template ORDER BY id",
            ).fetchall()
            return [self._to_template(r) for r in rows]

    def list_active(self) -> list[TaskTemplate]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_template WHERE active = 1 ORDER BY id",
            ).fetchall()
            return [self._to_template(r) for r in rows]

    def create(  # noqa: PLR0913, PLR0917
        self,
        title: str,
        description: str | None,
        sp_cost: int,
        recurrence_type: str,
        recurrence_params: dict[str, int],
        default_assignee_id: int | None,
    ) -> TaskTemplate:
        with get_transaction(self._db_path) as conn:
            now = datetime.now(timezone.utc).isoformat()
            params_json = json.dumps(recurrence_params)
            cur = conn.execute(
                "INSERT INTO task_template "
                "(title, description, sp_cost, recurrence_type, recurrence_params, "
                "default_assignee_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, description, sp_cost, recurrence_type, params_json,
                 default_assignee_id, now),
            )
            tmpl_id = cur.lastrowid
            row = conn.execute(
                "SELECT * FROM task_template WHERE id = ?", (tmpl_id,),
            ).fetchone()
            return self._to_template(row)

    def update(  # noqa: PLR0913
        self,
        template_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        sp_cost: int | None = None,
        recurrence_type: str | None = None,
        recurrence_params: dict[str, int] | None = None,
        default_assignee_id: int | None = None,
        active: bool | None = None,
    ) -> TaskTemplate:
        with get_transaction(self._db_path) as conn:
            _update_templ_fields(
                conn,
                template_id,
                title,
                description,
                sp_cost,
                recurrence_type,
                recurrence_params,
                default_assignee_id,
                active=active,
            )
            row = conn.execute(
                "SELECT * FROM task_template WHERE id = ?", (template_id,),
            ).fetchone()
            return self._to_template(row)

    def deactivate(self, template_id: int) -> TaskTemplate:
        with get_transaction(self._db_path) as db_conn:
            db_conn.execute(
                "UPDATE task_template SET active = 0 WHERE id = ?",
                (template_id,),
            )
            row = db_conn.execute(
                "SELECT * FROM task_template WHERE id = ?", (template_id,),
            ).fetchone()
            return self._to_template(row)

    def delete(self, template_id: int) -> None:
        with get_transaction(self._db_path) as db_conn:
            db_conn.execute(
                "DELETE FROM task_instance WHERE template_id = ?", (template_id,),
            )
            db_conn.execute(
                "DELETE FROM task_template WHERE id = ?", (template_id,),
            )

    @staticmethod
    def _to_template(row: sqlite3.Row) -> TaskTemplate:
        params_raw = row["recurrence_params"]
        params = json.loads(params_raw) if params_raw else {}

        return TaskTemplate(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            sp_cost=row["sp_cost"],
            recurrence_type=RecurrenceType(row["recurrence_type"]),
            recurrence_params=params,
            default_assignee_id=row["default_assignee_id"],
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )


def _update_templ_fields(  # noqa: PLR0912, PLR0913, PLR0917
    conn: sqlite3.Connection,
    template_id: int,
    title: str | None,
    description: str | None,
    sp_cost: int | None,
    recurrence_type: str | None,
    recurrence_params: dict[str, int] | None,
    default_assignee_id: int | None,
    *,
    active: bool | None,
) -> None:
    for field, value in (
        ("title", title), ("description", description), ("sp_cost", sp_cost),
    ):
        if value is not None:
            conn.execute(
                f"UPDATE task_template SET {field} = ? WHERE id = ?",  # noqa: S608
                (value, template_id),
            )

    if recurrence_type is not None:
        conn.execute(
            "UPDATE task_template SET recurrence_type = ? WHERE id = ?",
            (recurrence_type, template_id),
        )
    if recurrence_params is not None:
        conn.execute(
            "UPDATE task_template SET recurrence_params = ? WHERE id = ?",
            (json.dumps(recurrence_params), template_id),
        )
    if default_assignee_id is not None:
        conn.execute(
            "UPDATE task_template SET default_assignee_id = ? WHERE id = ?",
            (default_assignee_id, template_id),
        )
    if active is not None:
        conn.execute(
            "UPDATE task_template SET active = ? WHERE id = ?",
            (1 if active else 0, template_id),
        )
