"""Test compute_balance and related domain services."""
from datetime import date, datetime, timedelta, timezone

import pytest

from src.domain.entities import TaskInstance
from src.domain.exceptions import DomainError
from src.domain.services import (
    compute_balance,
    compute_monthly_balance,
    compute_sliding_30d_balance,
)


def _make_instance(
    *,
    inst_id: int = 1,
    completed_by_id: int | None = None,
    completed_day: int | None = None,
    sp_cost: int | None = None,
    assignee_id: int = 1,
    scheduled_day: int = 1,
) -> TaskInstance:
    if completed_day is not None:
        completed_at = datetime(2026, 6, completed_day, 12, 0, tzinfo=timezone.utc)
    else:
        completed_at = None

    return TaskInstance(
        id=inst_id,
        template_id=1,
        title="Test",
        scheduled_date=date(2026, 6, scheduled_day),
        assignee_id=assignee_id,
        completed_at=completed_at,
        completed_by_id=completed_by_id,
        sp_cost_at_completion=sp_cost,
    )


class TestComputeBalance:

    def test_empty_list(self) -> None:
        sp_sum, count = compute_balance([], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 0
        assert count == 0

    def test_single_completed_instance(self) -> None:
        inst = _make_instance(inst_id=1, completed_by_id=1, completed_day=15, sp_cost=5)
        sp_sum, count = compute_balance([inst], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 5
        assert count == 1

    def test_filters_by_user_id(self) -> None:
        inst1 = _make_instance(inst_id=1, completed_by_id=1, completed_day=10, sp_cost=3)
        inst2 = _make_instance(inst_id=2, completed_by_id=2, completed_day=10, sp_cost=7)
        sp_sum, count = compute_balance([inst1, inst2], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 3
        assert count == 1

    def test_excludes_uncompleted(self) -> None:
        done = _make_instance(inst_id=1, completed_by_id=1, completed_day=10, sp_cost=3)
        pending = _make_instance(inst_id=2, completed_by_id=None, completed_day=None, sp_cost=5)
        sp_sum, count = compute_balance([done, pending], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 3
        assert count == 1

    def test_filters_by_date_range(self) -> None:
        in_range = _make_instance(inst_id=1, completed_by_id=1, completed_day=15, sp_cost=5)
        before_range = _make_instance(inst_id=2, completed_by_id=1, completed_day=1, sp_cost=2)
        sp_sum, count = compute_balance(
            [in_range, before_range], 1, date(2026, 6, 10), date(2026, 6, 20),
        )
        assert sp_sum == 5
        assert count == 1

    def test_multiple_in_range(self) -> None:
        inst1 = _make_instance(inst_id=1, completed_by_id=1, completed_day=5, sp_cost=2)
        inst2 = _make_instance(inst_id=2, completed_by_id=1, completed_day=10, sp_cost=3)
        inst3 = _make_instance(inst_id=3, completed_by_id=1, completed_day=15, sp_cost=4)
        sp_sum, count = compute_balance([inst1, inst2, inst3], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 9
        assert count == 3

    def test_zero_sp_cost_counts_task(self) -> None:
        inst = _make_instance(inst_id=1, completed_by_id=1, completed_day=5, sp_cost=0)
        sp_sum, count = compute_balance([inst], 1, date(2026, 6, 1), date(2026, 6, 30))
        assert sp_sum == 0
        assert count == 1

    def test_null_sp_cost_not_allowed_by_entity(self) -> None:

        with pytest.raises(DomainError, match="sp_cost_at_completion"):
            _make_instance(inst_id=1, completed_by_id=1, completed_day=5, sp_cost=None)


class TestComputeSliding30DBalance:

    def test_includes_today_minus_29_to_today(self) -> None:
        today = date(2026, 6, 15)
        inst = _make_instance(inst_id=1, completed_by_id=1, completed_day=15, sp_cost=3)
        sp_sum, count = compute_sliding_30d_balance([inst], 1, today)
        assert sp_sum == 3
        assert count == 1

    def test_excludes_before_window(self) -> None:
        today = date(2026, 7, 15)
        inst = TaskInstance(
            id=1, template_id=1, title="T", scheduled_date=date(2026, 6, 1), assignee_id=1,
            completed_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            completed_by_id=1, sp_cost_at_completion=5,
        )
        sp_sum, count = compute_sliding_30d_balance([inst], 1, today)
        assert sp_sum == 0
        assert count == 0

    def test_includes_window_boundary(self) -> None:
        today = date(2026, 6, 15)
        start_of_window = today - timedelta(days=29)
        inst = TaskInstance(
            id=1, template_id=1, title="T", scheduled_date=start_of_window, assignee_id=1,
            completed_at=datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
            completed_by_id=1, sp_cost_at_completion=4,
        )
        sp_sum, count = compute_sliding_30d_balance([inst], 1, today)
        assert sp_sum == 4
        assert count == 1

    def test_window_crosses_month(self) -> None:
        today = date(2026, 6, 5)
        inst_may = _make_instance(inst_id=1, completed_by_id=1, completed_day=10, sp_cost=2)
        inst_june = _make_instance(inst_id=2, completed_by_id=1, completed_day=3, sp_cost=3)
        sp_sum, count = compute_sliding_30d_balance([inst_may, inst_june], 1, today)
        assert count == 1
        assert sp_sum == 3


class TestComputeMonthlyBalance:

    def test_june_full_month(self) -> None:
        inst1 = _make_instance(inst_id=1, completed_by_id=1, completed_day=1, sp_cost=2)
        inst2 = _make_instance(inst_id=2, completed_by_id=1, completed_day=15, sp_cost=3)
        inst3 = _make_instance(inst_id=3, completed_by_id=1, completed_day=30, sp_cost=5)
        sp_sum, count = compute_monthly_balance([inst1, inst2, inst3], 1, 2026, 6)
        assert sp_sum == 10
        assert count == 3

    def test_excludes_other_month(self) -> None:
        may_inst = TaskInstance(
            id=1, template_id=1, title="May", scheduled_date=date(2026, 5, 25), assignee_id=1,
            completed_at=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
            completed_by_id=1, sp_cost_at_completion=7,
        )
        june_inst = _make_instance(inst_id=2, completed_by_id=1, completed_day=5, sp_cost=3)
        sp_sum, count = compute_monthly_balance([may_inst, june_inst], 1, 2026, 6)
        assert sp_sum == 3
        assert count == 1

    def test_december_boundary(self) -> None:
        inst = TaskInstance(
            id=1,
            template_id=1,
            title="Dec",
            scheduled_date=date(2026, 12, 25),
            assignee_id=1,
            completed_at=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
            completed_by_id=1,
            sp_cost_at_completion=10,
        )
        sp_sum, count = compute_monthly_balance([inst], 1, 2026, 12)
        assert sp_sum == 10
        assert count == 1
