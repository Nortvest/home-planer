import re
from dataclasses import dataclass, field
from datetime import date, datetime

from src.domain.exceptions import DomainError, InvalidColorError
from src.domain.value_objects import RecurrenceType

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_color(color: str) -> str:
    if not _COLOR_RE.match(color):
        raise InvalidColorError(f"Цвет должен быть в формате #RRGGBB, получено: {color!r}")
    return color


def _validate_recurrence(template_type: RecurrenceType, params: dict[str, int]) -> None:
    """Проверить корректность recurrence_params для заданного типа повтора."""
    if template_type == RecurrenceType.WEEKLY:
        wd = params.get("weekday")
        if wd is None or not isinstance(wd, int) or wd not in range(7):
            raise DomainError("Для weekly-повтора должен быть указан weekday (0-6)")
    elif template_type == RecurrenceType.EVERY_N_DAYS:
        n = params.get("interval_days")
        if n is None or not isinstance(n, int) or n < 1:
            raise DomainError("Для every_n_days должен быть указан interval_days >= 1")


@dataclass
class User:
    id: int
    name: str
    color: str
    active: bool = True
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainError("Имя пользователя не может быть пустым")
        self.name = self.name.strip()
        self.color = _validate_color(self.color)


@dataclass
class TaskTemplate:
    id: int
    title: str
    description: str | None = None
    sp_cost: int = 0
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_params: dict[str, int] = field(default_factory=dict)
    default_assignee_id: int | None = None
    active: bool = True
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise DomainError("Название шаблона не может быть пустым")
        self.title = self.title.strip()

        if self.sp_cost < 0:
            raise DomainError("sp_cost не может быть отрицательным")

        _validate_recurrence(self.recurrence_type, self.recurrence_params)


@dataclass
class TaskInstance:
    id: int
    template_id: int | None
    title: str
    scheduled_date: date
    assignee_id: int | None
    completed_at: datetime | None = None
    completed_by_id: int | None = None
    sp_cost_at_completion: int | None = None
    cancelled_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.completed_at is None:
            return
        if self.completed_by_id is None:
            raise DomainError("Если задано completed_at, должен быть указан completed_by_id")
        if self.sp_cost_at_completion is None:
            raise DomainError("Если задано completed_at, должен быть указан sp_cost_at_completion")

    @property
    def is_done(self) -> bool:
        return self.completed_at is not None

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None


@dataclass
class TaskTransfer:
    id: int
    instance_id: int
    from_user_id: int | None
    to_user_id: int
    transferred_at: datetime
