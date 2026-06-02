"""Тесты UserRepositorySqlite."""
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository


class TestSqliteUserRepository:

    def test_create_and_get(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        user = repo.create("Иван", "#FF0000")
        assert user.name == "Иван"
        assert user.color == "#FF0000"
        assert user.active is True
        assert user.id is not None

        found = repo.get(user.id)
        assert found is not None
        assert found.name == "Иван"

    def test_list_all(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        repo.create("Аня", "#111111")
        repo.create("Борис", "#222222")
        all_users = repo.list_all()
        assert len(all_users) == 2

    def test_list_active(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        repo.create("Аня", "#111111")
        u2 = repo.create("Борис", "#222222")
        repo.deactivate(u2.id)
        active = repo.list_active()
        assert len(active) == 1
        assert active[0].name == "Аня"

    def test_update_name(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        user = repo.create("Аня", "#111111")
        updated = repo.update(user.id, name="Анастасия")
        assert updated.name == "Анастасия"
        assert updated.color == "#111111"

    def test_update_color(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        user = repo.create("Аня", "#111111")
        updated = repo.update(user.id, color="#AABBCC")
        assert updated.color == "#AABBCC"

    def test_deactivate(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        user = repo.create("Аня", "#111111")
        deactivated = repo.deactivate(user.id)
        assert deactivated.active is False

        found = repo.get(user.id)
        assert found is not None
        assert found.active is False

    def test_get_nonexistent(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        assert repo.get(999) is None

    def test_has_active_instances_false(self, db_path: str) -> None:
        repo = SqliteUserRepository(db_path)
        user = repo.create("Аня", "#111111")
        assert repo.has_active_instances(user.id) is False
