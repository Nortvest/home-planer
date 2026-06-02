"""SQLite-реализация UserRepository."""
import sqlite3
from datetime import datetime, timezone

from src.application.ports.user_repo import UserRepository
from src.domain.entities import User
from src.infrastructure.db.connection import get_connection, get_transaction


class SqliteUserRepository(UserRepository):
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def get(self, user_id: int) -> User | None:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                'SELECT * FROM "user" WHERE id = ?', (user_id,),
            ).fetchone()
            if row is None:
                return None
            return self._to_user(row)

    def list_all(self) -> list[User]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                'SELECT * FROM "user" ORDER BY id',
            ).fetchall()
            return [self._to_user(r) for r in rows]

    def list_active(self) -> list[User]:
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                'SELECT * FROM "user" WHERE active = 1 ORDER BY id',
            ).fetchall()
            return [self._to_user(r) for r in rows]

    def create(self, name: str, color: str) -> User:
        with get_transaction(self._db_path) as conn:
            now = datetime.now(timezone.utc).isoformat()
            cur = conn.execute(
                'INSERT INTO "user" (name, color, created_at) VALUES (?, ?, ?)',
                (name, color, now),
            )
            user_id = cur.lastrowid
            row = conn.execute(
                'SELECT * FROM "user" WHERE id = ?', (user_id,),
            ).fetchone()
            return self._to_user(row)

    def update(
        self,
        user_id: int,
        *,
        name: str | None = None,
        color: str | None = None,
        active: bool | None = None,
    ) -> User:
        with get_transaction(self._db_path) as conn:
            has_any = name is not None or color is not None or active is not None
            if not has_any:
                row = conn.execute(
                    'SELECT * FROM "user" WHERE id = ?', (user_id,),
                ).fetchone()
                return self._to_user(row)

            if name is not None:
                conn.execute(
                    'UPDATE "user" SET name = ? WHERE id = ?', (name, user_id),
                )
            if color is not None:
                conn.execute(
                    'UPDATE "user" SET color = ? WHERE id = ?', (color, user_id),
                )
            if active is not None:
                conn.execute(
                    'UPDATE "user" SET active = ? WHERE id = ?', (1 if active else 0, user_id),
                )
            row = conn.execute(
                'SELECT * FROM "user" WHERE id = ?', (user_id,),
            ).fetchone()
            return self._to_user(row)

    def deactivate(self, user_id: int) -> User:
        with get_transaction(self._db_path) as conn:
            conn.execute(
                'UPDATE "user" SET active = 0 WHERE id = ?', (user_id,),
            )
            row = conn.execute(
                'SELECT * FROM "user" WHERE id = ?', (user_id,),
            ).fetchone()
            return self._to_user(row)

    def delete(self, user_id: int) -> None:
        with get_transaction(self._db_path) as conn:
            conn.execute(
                'DELETE FROM task_transfer WHERE from_user_id = ?', (user_id,),
            )
            conn.execute(
                'DELETE FROM task_transfer WHERE to_user_id = ?', (user_id,),
            )
            conn.execute(
                'DELETE FROM task_instance WHERE assignee_id = ?', (user_id,),
            )
            conn.execute(
                'DELETE FROM task_instance WHERE completed_by_id = ? AND completed_by_id IS NOT NULL', (user_id,),
            )
            conn.execute(
                'UPDATE task_template SET default_assignee_id = NULL WHERE default_assignee_id = ?', (user_id,),
            )
            conn.execute(
                'DELETE FROM "user" WHERE id = ?', (user_id,),
            )

    def has_active_instances(self, user_id: int) -> bool:
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM task_instance "
                "WHERE assignee_id = ? AND completed_at IS NULL",
                (user_id,),
            ).fetchone()
            return row["cnt"] > 0  # type: ignore[no-any-return]

    @staticmethod
    def _to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
