"""Тесты clock adaptation."""
from datetime import date, datetime, timezone

from src.infrastructure.repos.clock_adapter import FixedClock, SystemClock


class TestClock:

    def test_system_clock_returns_today(self) -> None:
        clock = SystemClock()
        today = clock.today()
        expected = datetime.now(timezone.utc).date()
        assert today == expected

    def test_fixed_clock_returns_fixed(self) -> None:
        fixed = date(2026, 6, 15)
        clock = FixedClock(fixed)
        assert clock.today() == fixed
