"""Тесты TaskInstanceRepositorySqlite."""
from datetime import date, datetime, timezone

from src.domain.entities import TaskInstance
from src.infrastructure.repos.instance_repo_sqlite import SqliteInstanceRepository
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository


class TestSqliteInstanceRepository:

    def test_create_and_get(self, db_path: str) -> None:
        repo = SqliteInstanceRepository(db_path)
        inst = TaskInstance(
            id=0,
            template_id=None,
            title="Разовая задача",
            scheduled_date=date(2026, 6, 15),
            assignee_id=None,
        )
        created = repo.create(inst)
        assert created.id > 0
        assert created.title == "Разовая задача"

        found = repo.get(created.id)
        assert found is not None
        assert found.title == "Разовая задача"

    def test_list_by_date_range(self, db_path: str) -> None:
        repo = SqliteInstanceRepository(db_path)
        d1 = date(2026, 6, 1)
        d2 = date(2026, 6, 10)
        repo.create(TaskInstance(0, None, "T1", date(2026, 6, 5), sp_cost=0, assignee_id=None))
        repo.create(TaskInstance(0, None, "T2", date(2026, 6, 20), sp_cost=0, assignee_id=None))
        results = repo.list_by_date_range(d1, d2)
        assert len(results) == 1
        assert results[0].title == "T1"

    def test_list_by_template_and_date(self, db_path: str) -> None:
        tmpl_repo = SqliteTemplateRepository(db_path)
        t1 = tmpl_repo.create("T1", None, 1, "none", {}, None)
        t2 = tmpl_repo.create("T2", None, 2, "none", {}, None)

        repo = SqliteInstanceRepository(db_path)
        repo.create(TaskInstance(0, t1.id, "Instance T1", date(2026, 6, 5), sp_cost=1, assignee_id=None))
        repo.create(TaskInstance(0, t2.id, "Instance T2", date(2026, 6, 5), sp_cost=2, assignee_id=None))
        results = repo.list_by_template_and_date(t1.id, date(2026, 6, 5))
        assert len(results) == 1
        assert results[0].template_id == t1.id

    def test_update_completed(self, db_path: str) -> None:
        user_repo = SqliteUserRepository(db_path)
        user = user_repo.create("Test", "#AAAAAA")
        repo = SqliteInstanceRepository(db_path)
        inst = TaskInstance(
            id=0, template_id=None, title="Test",
            scheduled_date=date(2026, 6, 1), assignee_id=None,
        )
        created = repo.create(inst)
        completed_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        completed = TaskInstance(
            id=created.id,
            template_id=None,
            title="Test",
            scheduled_date=date(2026, 6, 1),
            assignee_id=None,
            completed_at=completed_at,
            completed_by_id=user.id,
            sp_cost_at_completion=5,
        )
        updated = repo.update(completed)
        assert updated.completed_at == completed_at
        assert updated.completed_by_id == user.id
        assert updated.sp_cost_at_completion == 5

    def test_list_overdue(self, db_path: str) -> None:
        today = date(2026, 6, 15)
        repo = SqliteInstanceRepository(db_path)
        repo.create(TaskInstance(0, None, "Old", date(2026, 6, 1), sp_cost=0, assignee_id=None))
        repo.create(TaskInstance(0, None, "Future", date(2026, 6, 20), sp_cost=0, assignee_id=None))
        overdue = repo.list_overdue(today)
        assert len(overdue) == 1
        assert overdue[0].title == "Old"

    def test_count_by_status_pending(self, db_path: str) -> None:
        today = date(2026, 6, 15)
        repo = SqliteInstanceRepository(db_path)
        repo.create(TaskInstance(0, None, "Future", date(2026, 6, 20), sp_cost=0, assignee_id=None))
        repo.create(TaskInstance(0, None, "Old", date(2026, 6, 1), sp_cost=0, assignee_id=None))
        cnt = repo.count_by_status(today, "pending")
        assert cnt == 1

    def test_count_by_status_overdue(self, db_path: str) -> None:
        today = date(2026, 6, 15)
        repo = SqliteInstanceRepository(db_path)
        repo.create(TaskInstance(0, None, "Future", date(2026, 6, 20), sp_cost=0, assignee_id=None))
        repo.create(TaskInstance(0, None, "Old", date(2026, 6, 1), sp_cost=0, assignee_id=None))
        cnt = repo.count_by_status(today, "overdue")
        assert cnt == 1

    def test_list_completed_recent(self, db_path: str) -> None:
        user_repo = SqliteUserRepository(db_path)
        user = user_repo.create("Test", "#BBBBBB")
        repo = SqliteInstanceRepository(db_path)
        inst = TaskInstance(
            id=0, template_id=None, title="Recent",
            scheduled_date=date(2026, 6, 1), assignee_id=None,
        )
        created = repo.create(inst)
        completed = TaskInstance(
            id=created.id,
            template_id=None,
            title="Recent",
            scheduled_date=date(2026, 6, 1),
            assignee_id=None,
            completed_at=datetime(2026, 6, 5, 10, 0, 0, tzinfo=timezone.utc),
            completed_by_id=user.id,
            sp_cost_at_completion=3,
        )
        repo.update(completed)
        recent = repo.list_completed_recent(5)
        assert len(recent) == 1

    def test_get_nonexistent(self, db_path: str) -> None:
        repo = SqliteInstanceRepository(db_path)
        assert repo.get(999) is None
