from abc import ABC, abstractmethod

from src.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> User | None:
        """Возвращает пользователя по ID или None, если не найден."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[User]:
        """Возвращает всех пользователей (включая неактивных)."""
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> list[User]:
        """Возвращает только активных пользователей."""
        raise NotImplementedError

    @abstractmethod
    def create(self, name: str, color: str) -> User:
        """Создаёт нового пользователя и возвращает его с назначенным ID."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self, user_id: int, *, name: str | None = None, color: str | None = None, active: bool | None = None,
    ) -> User:
        """Обновляет поля существующего пользователя и возвращает актуальную запись."""
        raise NotImplementedError

    @abstractmethod
    def deactivate(self, user_id: int) -> User:
        """Выполняет мягкое удаление (active=False) и возвращает обновлённую запись."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: int) -> None:
        """Жёстко удаляет пользователя из БД."""
        raise NotImplementedError

    @abstractmethod
    def has_active_instances(self, user_id: int) -> bool:
        """Возвращает True, если у пользователя есть незакрытые инстансы задач."""
        raise NotImplementedError
