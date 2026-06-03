"""Test instance use cases (reassign, complete, uncomplete) with mock repos."""
from datetime import date, datetime, timezone

import pytest

from src.application.ports import (
    InstanceRepository,
    TemplateRepository,
    TransferRepository,
    UserRepository,
)
from src.application.use_cases.instances import (
    CompleteInstanceUseCase,
    ReassignInstanceUseCase,
    UncompleteInstanceUseCase,
)
from src.domain.entities import TaskInstance, TaskTemplate, TaskTransfer, User
from src.domain.exceptions import (
    InstanceAlreadyCompletedError,
    InstanceNotCompletedError,
    InstanceNotFoundError,
    UserNotFoundError,
)
from src.infrastructure.repos.clock_adapter import FixedClock


class MockUserRepoTest(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users = {u.id: u for u in (users or [])}

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def list_all(self) -> list[User]:
        return list(self._users.values())

    def list_active(self) -> list[User]:
        return [u for u in self._users.values() if u.active]

    def create(self, name: str, color: str) -> User:
        raise NotImplementedError

    def update(
        self, user_id: int, *, name: str | None = None,
        color: str | None = None, active: bool | None = None,
    ) -> User:
        raise NotImplementedError

    def deactivate(self, user_id: int) -> User:
        raise NotImplementedError

    def delete(self, user_id: int) -> None:
        raise NotImplementedError

    def has_active_instances(self, _user_id: int) -> bool:
        return False


class MockInstanceRepoTest(InstanceRepository):
    def __init__(self, instances: list[TaskInstance] | None = None) -> None:
        self._instances = {i.id: i for i in (instances or [])}

    def get(self, instance_id: int) -> TaskInstance | None:
        return self._instances.get(instance_id)

    def list_by_date_range(self, start: date, end: date) -> list[TaskInstance]:
        raise NotImplementedError

    def list_by_template_and_date(self, template_id: int, scheduled: date) -> list[TaskInstance]:
        raise NotImplementedError

    def create(self, instance: TaskInstance) -> TaskInstance:
        raise NotImplementedError

    def update(self, instance: TaskInstance) -> TaskInstance:
        self._instances[instance.id] = instance
        return instance

    def list_completed_by_user_and_date_range(self, user_id: int, start: date, end: date) -> list[TaskInstance]:
        raise NotImplementedError

    def list_completed_recent(self, limit: int = 20) -> list[TaskInstance]:
        raise NotImplementedError

    def list_overdue(self, today: date) -> list[TaskInstance]:
        raise NotImplementedError

    def count_by_status(self, today: date, status: str) -> int:
        raise NotImplementedError

    def count_done_current_month(self, today: date) -> int:
        raise NotImplementedError

    def delete_by_id(self, instance_id: int) -> None:
        raise NotImplementedError


class MockTransferRepoTest(TransferRepository):
    def __init__(self) -> None:
        self._transfers: dict[int, list[TaskTransfer]] = {}
        self._next_id = 1

    def create(self, transfer: TaskTransfer) -> TaskTransfer:
        t = TaskTransfer(
            id=self._next_id,
            instance_id=transfer.instance_id,
            from_user_id=transfer.from_user_id,
            to_user_id=transfer.to_user_id,
            transferred_at=transfer.transferred_at,
        )
        self._next_id += 1
        self._transfers.setdefault(t.instance_id, []).append(t)
        return t

    def list_by_instance(self, instance_id: int) -> list[TaskTransfer]:
        return self._transfers.get(instance_id, [])


class MockTemplateRepoTest(TemplateRepository):
    def __init__(self, templates: list[TaskTemplate] | None = None) -> None:
        self._templates = {t.id: t for t in (templates or [])}

    def get(self, template_id: int) -> TaskTemplate | None:
        return self._templates.get(template_id)

    def list_all(self) -> list[TaskTemplate]:
        return list(self._templates.values())

    def list_active(self) -> list[TaskTemplate]:
        return [t for t in self._templates.values() if t.active]

    def create(
        self, title: str, description: str | None, sp_cost: int,
        recurrence_type: str, recurrence_params: dict[str, int],
        default_assignee_id: int | None,
    ) -> TaskTemplate:
        raise NotImplementedError

    def update(
        self, template_id: int, *,
        title: str | None = None, description: str | None = None,
        sp_cost: int | None = None, recurrence_type: str | None = None,
        recurrence_params: dict[str, int] | None = None,
        default_assignee_id: int | None = None, active: bool | None = None,
    ) -> TaskTemplate:
        raise NotImplementedError

    def deactivate(self, template_id: int) -> TaskTemplate:
        raise NotImplementedError

    def delete(self, template_id: int) -> None:
        raise NotImplementedError


class TestReassignInstanceUseCase:

    def test_successful_reassign(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        u2 = User(id=2, name="Bob", color="#00FF00")
        inst = TaskInstance(id=1, template_id=1, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1)

        user_repo = MockUserRepoTest([u1, u2])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = ReassignInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        result = uc.execute(1, 2)

        assert result.assignee is not None
        assert result.assignee.id == 2
        transfers = trans_repo.list_by_instance(1)
        assert len(transfers) == 1
        assert transfers[0].from_user_id == 1
        assert transfers[0].to_user_id == 2

    def test_reassign_instance_not_found(self) -> None:
        u2 = User(id=2, name="Bob", color="#00FF00")
        user_repo = MockUserRepoTest([u2])
        inst_repo = MockInstanceRepoTest([])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = ReassignInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(InstanceNotFoundError):
            uc.execute(999, 2)

    def test_reassign_user_not_found(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        inst = TaskInstance(id=1, template_id=1, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1)

        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = ReassignInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(UserNotFoundError):
            uc.execute(1, 999)


class TestCompleteInstanceUseCase:

    def test_successful_complete(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        tpl = TaskTemplate(id=1, title="Dishes", sp_cost=3)
        inst = TaskInstance(id=1, template_id=1, title="Dishes", scheduled_date=date(2026, 6, 1), assignee_id=1)

        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([tpl])
        clock = FixedClock(date(2026, 6, 1))

        uc = CompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        result = uc.execute(1, 1)

        assert result.status == "done"
        assert result.completed_by is not None
        assert result.completed_by.id == 1
        assert result.sp_cost_at_completion == 3

    def test_already_completed_raises(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        tpl = TaskTemplate(id=1, title="Dishes", sp_cost=3)
        inst = TaskInstance(
            id=1, template_id=1, title="Dishes", scheduled_date=date(2026, 6, 1), assignee_id=1,
            completed_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            completed_by_id=1, sp_cost_at_completion=3,
        )

        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([tpl])
        clock = FixedClock(date(2026, 6, 1))

        uc = CompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(InstanceAlreadyCompletedError):
            uc.execute(1, 1)

    def test_instance_not_found_raises(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = CompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(InstanceNotFoundError):
            uc.execute(999, 1)

    def test_completed_by_not_found_raises(self) -> None:
        inst = TaskInstance(id=1, template_id=None, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1)
        user_repo = MockUserRepoTest([])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = CompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(UserNotFoundError):
            uc.execute(1, 999)

    def test_resolves_sp_from_template(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        tpl = TaskTemplate(id=1, title="Task", sp_cost=7)
        inst = TaskInstance(id=1, template_id=1, title="Task", scheduled_date=date(2026, 6, 1), assignee_id=1)

        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([tpl])
        clock = FixedClock(date(2026, 6, 1))

        uc = CompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        result = uc.execute(1, 1)
        assert result.sp_cost_at_completion == 7


class TestUncompleteInstanceUseCase:

    def test_successful_uncomplete(self) -> None:
        u1 = User(id=1, name="Alice", color="#FF0000")
        inst = TaskInstance(
            id=1, template_id=1, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1,
            completed_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            completed_by_id=1, sp_cost_at_completion=3,
        )

        user_repo = MockUserRepoTest([u1])
        inst_repo = MockInstanceRepoTest([inst])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = UncompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        result = uc.execute(1)

        assert result.completed_at is None
        assert result.sp_cost_at_completion is None

    def test_uncomplete_not_done_raises(self) -> None:
        inst = TaskInstance(id=1, template_id=1, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1)
        inst_repo = MockInstanceRepoTest([inst])
        user_repo = MockUserRepoTest([])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = UncompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(InstanceNotCompletedError):
            uc.execute(1)

    def test_uncomplete_not_found_raises(self) -> None:
        inst_repo = MockInstanceRepoTest([])
        user_repo = MockUserRepoTest([])
        trans_repo = MockTransferRepoTest()
        tmpl_repo = MockTemplateRepoTest([])
        clock = FixedClock(date(2026, 6, 1))

        uc = UncompleteInstanceUseCase(inst_repo, user_repo, trans_repo, tmpl_repo, clock)
        with pytest.raises(InstanceNotFoundError):
            uc.execute(999)
