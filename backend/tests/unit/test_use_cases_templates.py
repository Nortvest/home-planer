"""Test use cases with mock repositories."""
import pytest

from src.application.ports.template_repo import TemplateRepository
from src.application.use_cases.templates import TemplateManagementUseCase
from src.domain.entities import TaskTemplate
from src.domain.exceptions import TemplateNotFoundError
from src.domain.value_objects import RecurrenceType


class MockTemplateRepo(TemplateRepository):
    def __init__(self, templates: list[TaskTemplate] | None = None) -> None:
        self._templates = {t.id: t for t in (templates or [])}
        self._next_id = max((t.id for t in self._templates.values()), default=0) + 1

    def get(self, template_id: int) -> TaskTemplate | None:
        return self._templates.get(template_id)

    def list_all(self) -> list[TaskTemplate]:
        return list(self._templates.values())

    def list_active(self) -> list[TaskTemplate]:
        return [t for t in self._templates.values() if t.active]

    def create(
        self,
        title: str,
        description: str | None,
        sp_cost: int,
        recurrence_type: str,
        recurrence_params: dict[str, int],
        default_assignee_id: int | None,
    ) -> TaskTemplate:
        tpl = TaskTemplate(
            id=self._next_id,
            title=title,
            description=description,
            sp_cost=sp_cost,
            recurrence_type=RecurrenceType(recurrence_type),
            recurrence_params=recurrence_params,
            default_assignee_id=default_assignee_id,
        )
        self._next_id += 1
        self._templates[tpl.id] = tpl
        return tpl

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
        active: bool | None = None,
    ) -> TaskTemplate:
        t = self._templates[template_id]
        t = TaskTemplate(
            id=t.id,
            title=(title or t.title),
            description=(description if description is not None else t.description),
            sp_cost=(sp_cost if sp_cost is not None else t.sp_cost),
            recurrence_type=RecurrenceType(recurrence_type) if recurrence_type else t.recurrence_type,
            recurrence_params=recurrence_params if recurrence_params is not None else t.recurrence_params,
            default_assignee_id=default_assignee_id if default_assignee_id is not None else t.default_assignee_id,
            active=(active if active is not None else t.active),
        )
        self._templates[template_id] = t
        return t

    def deactivate(self, template_id: int) -> TaskTemplate:
        t = self._templates[template_id]
        t = TaskTemplate(
            id=t.id, title=t.title, description=t.description, sp_cost=t.sp_cost,
            recurrence_type=t.recurrence_type, recurrence_params=t.recurrence_params,
            default_assignee_id=t.default_assignee_id, active=False,
        )
        self._templates[template_id] = t
        return t

    def delete(self, template_id: int) -> None:
        self._templates.pop(template_id, None)


class TestTemplateManagementUseCase:

    def test_get_all(self) -> None:
        tpl = TaskTemplate(id=1, title="Dishes", sp_cost=2)
        repo = MockTemplateRepo(templates=[tpl])
        uc = TemplateManagementUseCase(repo)
        result = uc.get_all()
        assert len(result) == 1
        assert result[0].title == "Dishes"

    def test_get_active_only(self) -> None:
        t1 = TaskTemplate(id=1, title="Active", sp_cost=1, active=True)
        t2 = TaskTemplate(id=2, title="Inactive", sp_cost=1, active=False)
        repo = MockTemplateRepo(templates=[t1, t2])
        uc = TemplateManagementUseCase(repo)
        result = uc.get_active()
        assert len(result) == 1
        assert result[0].title == "Active"

    def test_create(self) -> None:
        repo = MockTemplateRepo()
        uc = TemplateManagementUseCase(repo)
        result = uc.create(
            title="New Task",
            description="Desc",
            sp_cost=5,
            recurrence_type="none",
            recurrence_params={},
            default_assignee_id=None,
        )
        assert result.title == "New Task"
        assert result.sp_cost == 5
        assert result.recurrence_type == "none"

    def test_create_weekly(self) -> None:
        repo = MockTemplateRepo()
        uc = TemplateManagementUseCase(repo)
        result = uc.create(
            title="Weekly",
            description=None,
            sp_cost=3,
            recurrence_type="weekly",
            recurrence_params={"weekday": 0},
            default_assignee_id=1,
        )
        assert result.recurrence_type == "weekly"
        assert result.recurrence_params == {"weekday": 0}
        assert result.default_assignee_id == 1

    def test_update(self) -> None:
        tpl = TaskTemplate(id=1, title="Old", sp_cost=2)
        repo = MockTemplateRepo(templates=[tpl])
        uc = TemplateManagementUseCase(repo)
        result = uc.update(1, title="New", sp_cost=5)
        assert result.title == "New"
        assert result.sp_cost == 5

    def test_deactivate(self) -> None:
        tpl = TaskTemplate(id=1, title="Test", sp_cost=1)
        repo = MockTemplateRepo(templates=[tpl])
        uc = TemplateManagementUseCase(repo)
        uc.deactivate(1)
        active = uc.get_active()
        assert len(active) == 0

    def test_deactivate_nonexistent_raises(self) -> None:
        repo = MockTemplateRepo()
        uc = TemplateManagementUseCase(repo)
        with pytest.raises(TemplateNotFoundError):
            uc.deactivate(999)

    def test_delete(self) -> None:
        tpl = TaskTemplate(id=1, title="Test", sp_cost=1)
        repo = MockTemplateRepo(templates=[tpl])
        uc = TemplateManagementUseCase(repo)
        uc.delete(1)
        assert len(uc.get_all()) == 0

    def test_delete_nonexistent_raises(self) -> None:
        repo = MockTemplateRepo()
        uc = TemplateManagementUseCase(repo)
        with pytest.raises(TemplateNotFoundError):
            uc.delete(999)
