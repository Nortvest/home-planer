"""Адаптер «часы» — реальный источник текущей даты."""
from datetime import date, datetime, timezone

from src.application.ports.clock import Clock


class SystemClock(Clock):
    """Берёт текущую дату из системного времени."""

    def __init__(self) -> None:
        self._tz = timezone.utc

    def today(self) -> date:
        return datetime.now(self._tz).date()


class FixedClock(Clock):
    """Возвращает фиксированную дату (для тестов)."""

    def __init__(self, fixed_date: date) -> None:
        self._fixed_date = fixed_date

    def today(self) -> date:  # type: ignore[override]
        return self._fixed_date
