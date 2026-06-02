"""SQLite-реализация TaskTransferRepository."""
import sqlite3
from datetime import datetime, timezone

from src.application.ports.transfer_repo import TransferRepository
from src.domain.entities import TaskTransfer
from src.infrastructure.db.connection import get_connection, get_transaction


class SqliteTransferRepository(TransferRepository):
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def create(self, transfer: TaskTransfer) -> TaskTransfer:
        with get_transaction(self._db_path) as conn:
            now = datetime.now(timezone.utc).isoformat()
            cur = conn.execute(
                "INSERT INTO task_transfer "
                "(instance_id, from_user_id, to_user_id, transferred_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    transfer.instance_id,
                    transfer.from_user_id,
                    transfer.to_user_id,
                    now,
                ),
            )
            transfer_id = cur.lastrowid
            row = conn.execute(
                "SELECT * FROM task_transfer WHERE id = ?", (transfer_id,),
            ).fetchone()
            return self._to_transfer(row)

    def list_by_instance(self, instance_id: int) -> list[TaskTransfer]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM task_transfer "
                "WHERE instance_id = ? ORDER BY transferred_at ASC",
                (instance_id,),
            ).fetchall()
            return [self._to_transfer(r) for r in rows]

    @staticmethod
    def _to_transfer(row: sqlite3.Row) -> TaskTransfer:
        return TaskTransfer(
            id=row["id"],
            instance_id=row["instance_id"],
            from_user_id=row["from_user_id"],
            to_user_id=row["to_user_id"],
            transferred_at=datetime.fromisoformat(row["transferred_at"]),
        )
