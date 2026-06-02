"""Тесты TaskTemplateRepositorySqlite."""
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository


class TestSqliteTemplateRepository:

    def test_create_and_get(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        tmpl = repo.create(
            title="Мусор",
            description="Вынесите мусор",
            sp_cost=3,
            recurrence_type="weekly",
            recurrence_params={"weekday": 1},
            default_assignee_id=None,
        )
        assert tmpl.title == "Мусор"
        assert tmpl.sp_cost == 3
        assert tmpl.recurrence_params == {"weekday": 1}

        found = repo.get(tmpl.id)
        assert found is not None
        assert found.title == "Мусор"

    def test_list_active_filters_deactivated(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        t1 = repo.create("Т1", None, 1, "none", {}, None)
        repo.create("Т2", None, 2, "none", {}, None)
        repo.deactivate(t1.id)
        active = repo.list_active()
        assert len(active) == 1
        assert active[0].title == "Т2"

    def test_update_fields(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        tmpl = repo.create("Т1", None, 1, "none", {}, None)
        updated = repo.update(tmpl.id, title="Новое имя", sp_cost=5)
        assert updated.title == "Новое имя"
        assert updated.sp_cost == 5

    def test_deactivate(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        tmpl = repo.create("Т1", None, 1, "none", {}, None)
        deactivated = repo.deactivate(tmpl.id)
        assert deactivated.active is False

    def test_get_nonexistent(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        assert repo.get(999) is None

    def test_list_all_includes_inactive(self, db_path: str) -> None:
        repo = SqliteTemplateRepository(db_path)
        repo.create("A", None, 1, "none", {}, None)
        t2 = repo.create("B", None, 2, "none", {}, None)
        repo.deactivate(t2.id)
        all_ = repo.list_all()
        assert len(all_) == 2
