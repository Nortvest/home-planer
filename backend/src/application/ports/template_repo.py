from abc import ABC, abstractmethod

from src.domain.entities import TaskTemplate


class TemplateRepository(ABC):
    @abstractmethod
    def get(self, template_id: int) -> TaskTemplate | None:
        """Возвращает шаблон по ID или None, если не найден."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[TaskTemplate]:
        """Возвращает все шаблоны (включая неактивные)."""
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> list[TaskTemplate]:
        """Возвращает только активные шаблоны."""
        raise NotImplementedError

    @abstractmethod
    def create(  # noqa: PLR0913, PLR0917
        self,
        title: str,
        description: str | None,
        sp_cost: int,
        recurrence_type: str,
        recurrence_params: dict[str, int],
        default_assignee_id: int | None,
    ) -> TaskTemplate:
        """Создаёт новый шаблон задачи и возвращает его с назначенным ID."""
        raise NotImplementedError

    @abstractmethod
    def update(  # noqa: PLR0913
        self,
        template_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        sp_cost: int | None = None,
        recurrence_type: str | None = None,
        recurrence_params: dict[str, int] | None = None,
        default_assignee_id: int | None = None,
    ) -> TaskTemplate:
        """Обновляет поля существующего шаблона и возвращает актуальную запись."""
        raise NotImplementedError

    @abstractmethod
    def deactivate(self, template_id: int) -> TaskTemplate:
        """Выполняет мягкое удаление шаблона (active=False)."""
        raise NotImplementedError
