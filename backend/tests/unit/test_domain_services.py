"""Test compute_status domain service."""
from datetime import date, datetime, timezone

from src.domain.entities import TaskInstance
from src.domain.services import compute_status
from src.domain.value_objects import TaskStatus


class TestComputeStatus:

    def test_done_instance_returns_done(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 6, 1),
            assignee_id=1,
            completed_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            completed_by_id=1,
            sp_cost_at_completion=2,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.DONE

    def test_past_uncompleted_is_overdue(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 5, 30),
            assignee_id=1,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.OVERDUE

    def test_today_uncompleted_is_pending(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 6, 1),
            assignee_id=1,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.PENDING

    def test_future_uncompleted_is_pending(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 6, 15),
            assignee_id=1,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.PENDING

    def test_done_overrides_past_date(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 5, 1),
            assignee_id=1,
            completed_at=datetime(2026, 5, 2, 10, 0, tzinfo=timezone.utc),
            completed_by_id=1,
            sp_cost_at_completion=1,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.DONE

    def test_done_overrides_future_date(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Test",
            scheduled_date=date(2026, 7, 1),
            assignee_id=1,
            completed_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            completed_by_id=1,
            sp_cost_at_completion=1,
        )
        assert compute_status(inst, date(2026, 6, 1)) == TaskStatus.DONE
