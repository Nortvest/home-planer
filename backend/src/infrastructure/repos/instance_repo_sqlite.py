"""SQLite-реализация TaskInstanceRepository."""
import sqlite3
from datetime import date, datetime, timezone

from src.application.ports.instance_repo import InstanceRepository
from src.domain.entities import TaskInstance
from src.infrastructure.db.connection import get_connection, get_transaction

_MONTHS_IN_YEAR = 12


class SqliteInstanceRepository(InstanceRepository):
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def get(self, instance_id: int) -> TaskInstance | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM task_instance WHERE id = ?", (instance_id,),
            ).fetchone()
            if row is None:
                return None
            return self._to_instance(row)

    def list_by_date_range(self, start: date, end: date) -> list[TaskInstance]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_instance "
                "WHERE scheduled_date >= ? AND scheduled_date <= ? "
                "ORDER BY scheduled_date, id",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
            return [self._to_instance(r) for r in rows]

    def list_by_template_and_date(
        self, template_id: int, scheduled: date,
    ) -> list[TaskInstance]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_instance "
                "WHERE template_id = ? AND scheduled_date = ?",
                (template_id, scheduled.isoformat()),
            ).fetchall()
            return [self._to_instance(r) for r in rows]

    def create(self, instance: TaskInstance) -> TaskInstance:
        with get_transaction(self._db_path) as conn:
            now = datetime.now(timezone.utc).isoformat()
            cur = conn.execute(
                "INSERT INTO task_instance "
                "(template_id, title, scheduled_date, assignee_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    instance.template_id,
                    instance.title,
                    instance.scheduled_date.isoformat(),
                    instance.assignee_id,
                    now,
                ),
            )
            instance_id = cur.lastrowid
            row = conn.execute(
                "SELECT * FROM task_instance WHERE id = ?", (instance_id,),
            ).fetchone()
            return self._to_instance(row)

    def update(self, instance: TaskInstance) -> TaskInstance:
        with get_transaction(self._db_path) as conn:
            conn.execute(
                "UPDATE task_instance SET "
                "title = ?, scheduled_date = ?, assignee_id = ?, "
                "completed_at = ?, completed_by_id = ?, sp_cost_at_completion = ? "
                "WHERE id = ?",
                (
                    instance.title,
                    instance.scheduled_date.isoformat(),
                    instance.assignee_id,
                    instance.completed_at.isoformat() if instance.completed_at else None,
                    instance.completed_by_id,
                    instance.sp_cost_at_completion,
                    instance.id,
                ),
            )
            row = conn.execute(
                "SELECT * FROM task_instance WHERE id = ?", (instance.id,),
            ).fetchone()
            return self._to_instance(row)

    def list_completed_by_user_and_date_range(
        self, user_id: int, start: date, end: date,
    ) -> list[TaskInstance]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_instance "
                "WHERE completed_by_id = ? AND completed_at IS NOT NULL "
                "AND date(completed_at) >= ? AND date(completed_at) <= ? "
                "ORDER BY completed_at DESC",
                (user_id, start.isoformat(), end.isoformat()),
            ).fetchall()
            return [self._to_instance(r) for r in rows]

    def list_completed_recent(self, limit: int = 20) -> list[TaskInstance]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_instance "
                "WHERE completed_at IS NOT NULL "
                "ORDER BY completed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._to_instance(r) for r in rows]

    def list_overdue(self, today: date) -> list[TaskInstance]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_instance "
                "WHERE scheduled_date < ? AND completed_at IS NULL "
                "ORDER BY scheduled_date ASC",
                (today.isoformat(),),
            ).fetchall()
            return [self._to_instance(r) for r in rows]

    def count_by_status(self, today: date, status: str) -> int:
        with get_connection(self._db_path) as conn:
            if status == "pending":
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM task_instance "
                    "WHERE scheduled_date >= ? AND completed_at IS NULL",
                    (today.isoformat(),),
                ).fetchone()
            elif status == "overdue":
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM task_instance "
                    "WHERE scheduled_date < ? AND completed_at IS NULL",
                    (today.isoformat(),),
                ).fetchone()
            else:
                raise ValueError(f"Неизвестный статус: {status}")
            return row["cnt"]  # type: ignore[no-any-return]

    def count_done_current_month(self, today: date) -> int:
        with get_connection(self._db_path) as conn:
            month_start = date(today.year, today.month, 1).isoformat()
            if today.month == _MONTHS_IN_YEAR:
                next_month = date(today.year + 1, 1, 1).isoformat()
            else:
                next_month = date(today.year, today.month + 1, 1).isoformat()

            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM task_instance "
                "WHERE completed_at IS NOT NULL "
                "AND date(completed_at) >= ? AND date(completed_at) < ?",
                (month_start, next_month),
            ).fetchone()
            return row["cnt"]  # type: ignore[no-any-return]

    def delete_by_id(self, instance_id: int) -> None:
        with get_transaction(self._db_path) as conn:
            conn.execute(
                "DELETE FROM task_instance WHERE id = ?", (instance_id,),
            )

    @staticmethod
    def _to_instance(row: sqlite3.Row) -> TaskInstance:
        return TaskInstance(
            id=row["id"],
            template_id=row["template_id"],
            title=row["title"],
            scheduled_date=date.fromisoformat(row["scheduled_date"]),
            assignee_id=row["assignee_id"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            completed_by_id=row["completed_by_id"],
            sp_cost_at_completion=row["sp_cost_at_completion"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
