from src.application.dtos import TaskTemplateDTO
from src.application.ports import TemplateRepository
from src.domain.entities import TaskTemplate
from src.domain.exceptions import TemplateNotFoundError


class TemplateManagementUseCase:
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    def get_all(self) -> list[TaskTemplateDTO]:
        return [_to_dto(t) for t in self._repo.list_all()]

    def get_active(self) -> list[TaskTemplateDTO]:
        return [_to_dto(t) for t in self._repo.list_active()]

    def create(
        self,
        title: str,
        description: str | None,
        sp_cost: int,
        recurrence_type: str,
        recurrence_params: dict[str, int],
        default_assignee_id: int | None,
    ) -> TaskTemplateDTO:
        template = self._repo.create(
            title,
            description,
            sp_cost,
            recurrence_type,
            recurrence_params,
            default_assignee_id,
        )
        return _to_dto(template)

    def update(
        self,
        template_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        sp_cost: int | None = None,
        recurrence_type: str | None = None,
        recurrence_params: dict[str, int] | None = None,
        default_assignee_id: int | None = None,
    ) -> TaskTemplateDTO:
        template = self._repo.update(
            template_id,
            title=title,
            description=description,
            sp_cost=sp_cost,
            recurrence_type=recurrence_type,
            recurrence_params=recurrence_params,
            default_assignee_id=default_assignee_id,
        )
        return _to_dto(template)

    def deactivate(self, template_id: int) -> None:
        tpl = self._repo.get(template_id)
        if tpl is None:
            raise TemplateNotFoundError(f"Шаблон не найден: {template_id}")
        self._repo.deactivate(template_id)


def _to_dto(t: TaskTemplate) -> TaskTemplateDTO:
    return TaskTemplateDTO(
        id=t.id,
        title=t.title,
        description=t.description,
        sp_cost=t.sp_cost,
        recurrence_type=t.recurrence_type.value,
        recurrence_params=dict(t.recurrence_params),
        default_assignee_id=t.default_assignee_id,
        active=t.active,
        created_at=t.created_at,
    )
