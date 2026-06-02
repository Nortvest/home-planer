"""Test use cases with mock repositories."""
import pytest

from src.application.ports.user_repo import UserRepository
from src.application.use_cases.users import UserManagementUseCase
from src.domain.entities import User
from src.domain.exceptions import DuplicateUserNameError, UserHasActiveTasksError, UserNotFoundError


class MockUserRepo(UserRepository):
    def __init__(
        self, users: list[User] | None = None,
        active_instances: dict[int, bool] | None = None,
    ) -> None:
        self._users = {u.id: u for u in (users or [])}
        self._active = active_instances or {}
        self._next_id = max((u.id for u in self._users.values()), default=0) + 1

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def list_active(self) -> list[User]:
        return [u for u in self._users.values() if u.active]

    def create(self, name: str, color: str) -> User:
        u = User(id=self._next_id, name=name, color=color)
        self._next_id += 1
        self._users[u.id] = u
        return u

    def update(
        self, user_id: int, *, name: str | None = None,
        color: str | None = None, active: bool | None = None,
    ) -> User:
        u = self._users[user_id]
        if name is not None:
            u = User(id=u.id, name=name, color=u.color, active=u.active, created_at=u.created_at)
            self._users[user_id] = u
        if color is not None:
            u = self._users[user_id]
            u = User(id=u.id, name=u.name, color=color, active=u.active, created_at=u.created_at)
            self._users[user_id] = u
        return self._users[user_id]

    def deactivate(self, user_id: int) -> User:
        u = self._users[user_id]
        u = User(id=u.id, name=u.name, color=u.color, active=False, created_at=u.created_at)
        self._users[user_id] = u
        return u

    def delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    def has_active_instances(self, user_id: int) -> bool:
        return self._active.get(user_id, False)


class TestUserManagementUseCase:

    def test_get_all(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        result = uc.get_all()
        assert len(result) == 1
        assert result[0].name == "Alice"

    def test_get_active_excludes_inactive(self) -> None:
        u1 = User(id=1, name="Active", color="#FF0000", active=True)
        u2 = User(id=2, name="Inactive", color="#00FF00", active=False)
        repo = MockUserRepo(users=[u1, u2])
        uc = UserManagementUseCase(repo)
        result = uc.get_active()
        assert len(result) == 1
        assert result[0].name == "Active"

    def test_create(self) -> None:
        repo = MockUserRepo()
        uc = UserManagementUseCase(repo)
        result = uc.create("NewUser", "#AABBCC")
        assert result.name == "NewUser"
        assert result.color == "#AABBCC"

    def test_create_duplicate_name_raises(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000", active=True)
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        with pytest.raises(DuplicateUserNameError):
            uc.create("alice", "#00FF00")

    def test_create_duplicate_case_insensitive(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000", active=True)
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        with pytest.raises(DuplicateUserNameError):
            uc.create("ALICE", "#00FF00")

    def test_create_inactive_user_name_allowed(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000", active=False)
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        result = uc.create("Alice", "#00FF00")
        assert result.name == "Alice"

    def test_update_existing(self) -> None:
        u1 = User(id=1, name="Old", color="#FF0000")
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        result = uc.update(1, name="NewName")
        assert result.name == "NewName"

    def test_update_nonexistent_raises(self) -> None:
        repo = MockUserRepo()
        uc = UserManagementUseCase(repo)
        with pytest.raises(UserNotFoundError):
            uc.update(999, name="X")

    def test_update_duplicate_name_raises(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        u2 = User(id=2, name="Bob", color="#00FF00")
        repo = MockUserRepo(users=[u1, u2])
        uc = UserManagementUseCase(repo)
        with pytest.raises(DuplicateUserNameError):
            uc.update(2, name="alice")

    def test_deactivate(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        result = uc.deactivate(1)
        assert result.active is False

    def test_deactivate_with_active_tasks_raises(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        repo = MockUserRepo(users=[u1], active_instances={1: True})
        uc = UserManagementUseCase(repo)
        with pytest.raises(UserHasActiveTasksError):
            uc.deactivate(1)

    def test_deactivate_nonexistent_raises(self) -> None:
        repo = MockUserRepo()
        uc = UserManagementUseCase(repo)
        with pytest.raises(UserNotFoundError):
            uc.deactivate(999)

    def test_delete(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        repo = MockUserRepo(users=[u1])
        uc = UserManagementUseCase(repo)
        uc.delete(1)
        assert repo.list_all() == []

    def test_delete_nonexistent_raises(self) -> None:
        repo = MockUserRepo()
        uc = UserManagementUseCase(repo)
        with pytest.raises(UserNotFoundError):
            uc.delete(999)
