from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities import TaskInstance


class InstanceRepository(ABC):
    @abstractmethod
    def get(self, instance_id: int) -> TaskInstance | None:
        """Возвращает инстанс по ID или None, если не найден."""
        raise NotImplementedError

    @abstractmethod
    def list_by_date_range(self, start: date, end: date) -> list[TaskInstance]:
        """Возвращает все инстансы с scheduled_date в диапазоне [start, end]."""
        raise NotImplementedError

    @abstractmethod
    def list_by_template_and_date(
        self, template_id: int, scheduled: date,
    ) -> list[TaskInstance]:
        """Возвращает инстансы для заданного шаблона и даты."""
        raise NotImplementedError

    @abstractmethod
    def create(self, instance: TaskInstance) -> TaskInstance:
        """Создаёт новый инстанс и возвращает его с назначенным ID."""
        raise NotImplementedError

    @abstractmethod
    def update(self, instance: TaskInstance) -> TaskInstance:
        """Обновляет инстанс и возвращает актуальную запись."""
        raise NotImplementedError

    @abstractmethod
    def list_completed_by_user_and_date_range(
        self, user_id: int, start: date, end: date,
    ) -> list[TaskInstance]:
        """Возвращает завершённые инстансы пользователя в диапазоне дат."""
        raise NotImplementedError

    @abstractmethod
    def list_completed_recent(self, limit: int = 20) -> list[TaskInstance]:
        """Возвращает последние завершённые инстансы (сортировка по completed_at desc)."""
        raise NotImplementedError

    @abstractmethod
    def list_overdue(self, today: date) -> list[TaskInstance]:
        """Возвращает просроченные инстансы (scheduled_date < today и не завершённые)."""
        raise NotImplementedError

    @abstractmethod
    def count_by_status(self, today: date, status: str) -> int:
        """Возвращает количество инстансов со статусом status (pending/overdue) на今天."""
        raise NotImplementedError

    @abstractmethod
    def count_done_current_month(self, today: date) -> int:
        """Возвращает количество завершённых инстансов за текущий календарный месяц."""
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, instance_id: int) -> None:
        """Удаляет инстанс по ID."""
        raise NotImplementedError
