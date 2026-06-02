"""Test domain entities validation and invariants."""
from datetime import date, datetime, timezone

import pytest

from src.domain.entities import TaskInstance, TaskTemplate, TaskTransfer, User
from src.domain.exceptions import DomainError, InvalidColorError
from src.domain.value_objects import RecurrenceType


class TestUser:

    def test_valid_user(self) -> None:
        u = User(id=1, name="Alice", color="#FF00AA")
        assert u.name == "Alice"
        assert u.color == "#FF00AA"
        assert u.active is True

    def test_strips_name(self) -> None:
        u = User(id=1, name="  Bob  ", color="#00FF00")
        assert u.name == "Bob"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(DomainError, match="не может быть пустым"):
            User(id=1, name="", color="#00FF00")

    def test_whitespace_only_name_raises(self) -> None:
        with pytest.raises(DomainError, match="не может быть пустым"):
            User(id=1, name="   ", color="#00FF00")

    def test_invalid_color_raises(self) -> None:
        with pytest.raises(InvalidColorError):
            User(id=1, name="Test", color="red")

    def test_valid_lowercase_color(self) -> None:
        u = User(id=1, name="Test", color="#abcdef")
        assert u.color == "#abcdef"

    def test_color_uppercase_preserved(self) -> None:
        u = User(id=1, name="Test", color="#ABCDEF")
        assert u.color == "#ABCDEF"

    def test_too_short_color_raises(self) -> None:
        with pytest.raises(InvalidColorError):
            User(id=1, name="Test", color="#FFF")

    def test_too_long_color_raises(self) -> None:
        with pytest.raises(InvalidColorError):
            User(id=1, name="Test", color="#AABBCCDD")

    def test_inactive_user(self) -> None:
        u = User(id=1, name="Old", color="#000000", active=False)
        assert u.active is False


class TestTaskTemplate:

    def test_valid_template(self) -> None:
        tpl = TaskTemplate(id=1, title="Dishes", sp_cost=3)
        assert tpl.title == "Dishes"
        assert tpl.sp_cost == 3
        assert tpl.recurrence_type == RecurrenceType.NONE
        assert tpl.active is True

    def test_title_stripped(self) -> None:
        tpl = TaskTemplate(id=1, title="  Chores  ", sp_cost=1)
        assert tpl.title == "Chores"

    def test_empty_title_raises(self) -> None:
        with pytest.raises(DomainError, match="не может быть пустым"):
            TaskTemplate(id=1, title="")

    def test_negative_sp_cost_raises(self) -> None:
        with pytest.raises(DomainError, match="отрицательным"):
            TaskTemplate(id=1, title="Test", sp_cost=-1)

    def test_zero_sp_cost_allowed(self) -> None:
        tpl = TaskTemplate(id=1, title="Test", sp_cost=0)
        assert tpl.sp_cost == 0

    def test_weekly_with_valid_weekday(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Weekly",
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_params={"weekday": 3},
        )
        assert tpl.recurrence_type == RecurrenceType.WEEKLY

    def test_weekly_without_weekday_raises(self) -> None:
        with pytest.raises(DomainError, match="weekday"):
            TaskTemplate(
                id=1,
                title="Weekly",
                recurrence_type=RecurrenceType.WEEKLY,
                recurrence_params={},
            )

    def test_weekly_invalid_weekday_raises(self) -> None:
        with pytest.raises(DomainError, match="weekday"):
            TaskTemplate(
                id=1,
                title="Weekly",
                recurrence_type=RecurrenceType.WEEKLY,
                recurrence_params={"weekday": 7},
            )

    def test_every_n_days_valid(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Every3Days",
            recurrence_type=RecurrenceType.EVERY_N_DAYS,
            recurrence_params={"interval_days": 3},
        )
        assert tpl.recurrence_type == RecurrenceType.EVERY_N_DAYS

    def test_every_n_days_zero_raises(self) -> None:
        with pytest.raises(DomainError, match="interval_days"):
            TaskTemplate(
                id=1,
                title="Bad",
                recurrence_type=RecurrenceType.EVERY_N_DAYS,
                recurrence_params={"interval_days": 0},
            )

    def test_every_n_days_missing_raises(self) -> None:
        with pytest.raises(DomainError, match="interval_days"):
            TaskTemplate(
                id=1,
                title="Bad",
                recurrence_type=RecurrenceType.EVERY_N_DAYS,
                recurrence_params={},
            )

    def test_none_with_empty_params(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="OneOff",
            recurrence_type=RecurrenceType.NONE,
            recurrence_params={},
        )
        assert tpl.recurrence_params == {}

    def test_with_description(self) -> None:
        tpl = TaskTemplate(id=1, title="Test", description="Some desc")
        assert tpl.description == "Some desc"

    def test_with_default_assignee(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Test",
            default_assignee_id=42,
        )
        assert tpl.default_assignee_id == 42


class TestTaskInstance:

    def test_valid_uncompleted(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Dishes",
            scheduled_date=date(2026, 6, 1),
            assignee_id=1,
        )
        assert inst.is_done is False
        assert inst.completed_at is None

    def test_valid_completed(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Dishes",
            scheduled_date=date(2026, 6, 1),
            assignee_id=1,
            completed_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            completed_by_id=2,
            sp_cost_at_completion=3,
        )
        assert inst.is_done is True
        assert inst.completed_by_id == 2

    def test_completed_at_without_completed_by_raises(self) -> None:
        with pytest.raises(DomainError, match="completed_by_id"):
            TaskInstance(
                id=1,
                template_id=1,
                title="Test",
                scheduled_date=date(2026, 6, 1),
                assignee_id=1,
                completed_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            )

    def test_completed_at_without_sp_cost_raises(self) -> None:
        with pytest.raises(DomainError, match="sp_cost_at_completion"):
            TaskInstance(
                id=1,
                template_id=1,
                title="Test",
                scheduled_date=date(2026, 6, 1),
                assignee_id=1,
                completed_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
                completed_by_id=1,
            )

    def test_null_template_id_allowed(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=None,
            title="OneOff",
            scheduled_date=date(2026, 6, 1),
            assignee_id=1,
        )
        assert inst.template_id is None

    def test_null_assignee_allowed(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Unassigned",
            scheduled_date=date(2026, 6, 1),
            assignee_id=None,
        )
        assert inst.assignee_id is None


class TestTaskTransfer:

    def test_valid_transfer(self) -> None:
        tr = TaskTransfer(
            id=1,
            instance_id=5,
            from_user_id=1,
            to_user_id=2,
            transferred_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        )
        assert tr.from_user_id == 1
        assert tr.to_user_id == 2
        assert tr.instance_id == 5

    def test_null_from_user_allowed(self) -> None:
        tr = TaskTransfer(
            id=1,
            instance_id=5,
            from_user_id=None,
            to_user_id=2,
            transferred_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        )
        assert tr.from_user_id is None
