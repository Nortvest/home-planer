from src.application.dtos import UserDTO
from src.application.ports import UserRepository
from src.domain.entities import User
from src.domain.exceptions import (
    DuplicateUserNameError,
    UserHasActiveTasksError,
    UserNotFoundError,
)


class UserManagementUseCase:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_all(self) -> list[UserDTO]:
        return [_to_dto(u) for u in self._repo.list_all()]

    def get_active(self) -> list[UserDTO]:
        return [_to_dto(u) for u in self._repo.list_active()]

    def create(self, name: str, color: str) -> UserDTO:
        existing = self._repo.list_all()
        for u in existing:
            if u.active and u.name.lower() == name.strip().lower():
                raise DuplicateUserNameError(f"Имя пользователя уже занято: {name}")
        user = self._repo.create(name, color)
        return _to_dto(user)

    def update(
        self, user_id: int, *, name: str | None = None, color: str | None = None,
    ) -> UserDTO:
        existing = self._repo.get(user_id)
        if existing is None:
            raise UserNotFoundError(f"Пользователь не найден: {user_id}")

        if name is not None:
            all_users = self._repo.list_all()
            for u in all_users:
                if u.active and u.id != user_id and u.name.lower() == name.strip().lower():
                    raise DuplicateUserNameError(f"Имя пользователя уже занято: {name}")

        user = self._repo.update(user_id, name=name, color=color)
        return _to_dto(user)

    def deactivate(self, user_id: int) -> UserDTO:
        existing = self._repo.get(user_id)
        if existing is None:
            raise UserNotFoundError(f"Пользователь не найден: {user_id}")
        if self._repo.has_active_instances(user_id):
            raise UserHasActiveTasksError(
                "Нельзя удалить пользователя: у него есть незакрытые задачи",
            )
        user = self._repo.deactivate(user_id)
        return _to_dto(user)


def _to_dto(u: User) -> UserDTO:
    return UserDTO(
        id=u.id,
        name=u.name,
        color=u.color,
        active=u.active,
        created_at=u.created_at,
    )
