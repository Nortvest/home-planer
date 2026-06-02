"""Test generate_recurrence_dates domain service."""
from datetime import date

from src.domain.entities import TaskTemplate
from src.domain.services import generate_recurrence_dates
from src.domain.value_objects import RecurrenceType


class TestGenerateRecurrenceDates:

    def test_none_returns_empty(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="OneTime",
            sp_cost=2,
            recurrence_type=RecurrenceType.NONE,
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 30))
        assert dates == []

    def test_daily_generates_every_day(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Daily",
            sp_cost=1,
            recurrence_type=RecurrenceType.DAILY,
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 3))
        assert dates == [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]

    def test_daily_single_day(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Daily",
            sp_cost=1,
            recurrence_type=RecurrenceType.DAILY,
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 5), date(2026, 6, 5))
        assert dates == [date(2026, 6, 5)]

    def test_weekly_monday_only(self) -> None:
        """June 1 2026 is Monday. Mondays in June 2026: 1, 8, 15, 22, 29."""
        tpl = TaskTemplate(
            id=1,
            title="Weekly",
            sp_cost=3,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_params={"weekday": 0},
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 30))
        assert dates == [date(2026, 6, 1), date(2026, 6, 8), date(2026, 6, 15), date(2026, 6, 22), date(2026, 6, 29)]

    def test_weekly_sunday(self) -> None:
        """Sundays in June 2026: 7, 14, 21, 28."""
        tpl = TaskTemplate(
            id=1,
            title="WeeklySun",
            sp_cost=2,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_params={"weekday": 6},
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 30))
        assert dates == [date(2026, 6, 7), date(2026, 6, 14), date(2026, 6, 21), date(2026, 6, 28)]

    def test_every_n_days_interval_2(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Every2Days",
            sp_cost=1,
            recurrence_type=RecurrenceType.EVERY_N_DAYS,
            recurrence_params={"interval_days": 2},
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 7))
        assert dates == [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 5), date(2026, 6, 7)]

    def test_every_n_days_interval_7(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Every7Days",
            sp_cost=5,
            recurrence_type=RecurrenceType.EVERY_N_DAYS,
            recurrence_params={"interval_days": 7},
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 1), date(2026, 6, 30))
        assert dates == [date(2026, 6, 1), date(2026, 6, 8), date(2026, 6, 15), date(2026, 6, 22), date(2026, 6, 29)]

    def test_empty_range_returns_empty(self) -> None:
        tpl = TaskTemplate(
            id=1,
            title="Daily",
            sp_cost=1,
            recurrence_type=RecurrenceType.DAILY,
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 10), date(2026, 6, 1))
        assert dates == []

    def test_weekly_no_match_in_range(self) -> None:
        """Range doesn't contain any Friday (weekday 4)."""
        tpl = TaskTemplate(
            id=1,
            title="WeeklyFri",
            sp_cost=2,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_params={"weekday": 4},
        )
        dates = generate_recurrence_dates(tpl, date(2026, 6, 2), date(2026, 6, 4))
        assert dates == []
