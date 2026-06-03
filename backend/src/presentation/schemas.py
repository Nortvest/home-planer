"""Pydantic-схемы для API-контракта §13.

Каждая схема соответствует DTO из API-контракта.
Используются для валидации запросов и сериализации ответов.
"""

import re
from datetime import (
    date,
    datetime,
)

from pydantic import BaseModel, Field, model_validator

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class UserOut(BaseModel):
    id: int
    name: str
    color: str
    active: bool
    created_at: datetime | None


class UsersListOut(BaseModel):
    users: list[UserOut]


class UserCreateIn(BaseModel):
    name: str = Field(min_length=1)
    color: str

    @model_validator(mode="after")
    def _validate_color(self) -> "UserCreateIn":
        if not HEX_COLOR_RE.match(self.color):
            raise ValueError("Цвет должен быть в формате #RRGGBB")
        return self


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    color: str | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def _validate_color(self) -> "UserUpdateIn":
        if self.color is not None and not HEX_COLOR_RE.match(self.color):
            raise ValueError("Цвет должен быть в формате #RRGGBB")
        return self


class RecurrenceParamsIn(BaseModel):
    weekday: int | None = None
    interval_days: int | None = None


class TaskTemplateOut(BaseModel):
    id: int
    title: str
    description: str | None
    sp_cost: int
    recurrence_type: str
    recurrence_params: dict[str, int]
    default_assignee_id: int | None
    active: bool
    created_at: datetime | None


class TaskTemplateCreateIn(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    sp_cost: int = Field(ge=0)
    recurrence_type: str = Field(pattern=r"^(none|daily|weekly|every_n_days)$")
    recurrence_params: RecurrenceParamsIn = Field(default_factory=RecurrenceParamsIn)
    default_assignee_id: int | None = None

    def to_params_dict(self) -> dict[str, int]:
        d: dict[str, int] = {}
        if self.recurrence_params.weekday is not None:
            d["weekday"] = self.recurrence_params.weekday
        if self.recurrence_params.interval_days is not None:
            d["interval_days"] = self.recurrence_params.interval_days
        return d


class TaskTemplateUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    sp_cost: int | None = Field(default=None, ge=0)
    recurrence_type: str | None = Field(
        default=None,
        pattern=r"^(none|daily|weekly|every_n_days)$",
    )
    recurrence_params: RecurrenceParamsIn | None = None
    default_assignee_id: int | None = None
    active: bool | None = None

    def to_params_dict(self) -> dict[str, int]:
        if self.recurrence_params is None:
            return {}
        d: dict[str, int] = {}
        if self.recurrence_params.weekday is not None:
            d["weekday"] = self.recurrence_params.weekday
        if self.recurrence_params.interval_days is not None:
            d["interval_days"] = self.recurrence_params.interval_days
        return d


class TemplatesListOut(BaseModel):
    templates: list[TaskTemplateOut]


class TaskTransferOut(BaseModel):
    id: int
    from_user: UserOut | None
    to_user: UserOut | None
    transferred_at: datetime


class TaskInstanceOut(BaseModel):
    id: int
    template_id: int | None
    title: str
    scheduled_date: date
    assignee: UserOut | None
    status: str
    sp_cost_current: int
    sp_cost_at_completion: int | None
    completed_at: datetime | None
    completed_by: UserOut | None
    transfers: list[TaskTransferOut]


class TaskInstanceCreateIn(BaseModel):
    title: str = Field(min_length=1)
    scheduled_date: date
    sp_cost: int = Field(ge=0, default=0)
    assignee_id: int | None = None


class ReassignIn(BaseModel):
    to_user_id: int


class CompleteIn(BaseModel):
    completed_by_id: int


class TransfersOut(BaseModel):
    transfers: list[TaskTransferOut]


class CalendarRangeOut(BaseModel):
    days: dict[str, list[TaskInstanceOut]]
    users: list[UserOut]


class CalendarOut(BaseModel):
    year: int
    month: int
    days: dict[str, list[TaskInstanceOut]]
    users: list[UserOut]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2026,
                    "month": 6,
                    "days": {
                        "2026-06-01": [
                            {
                                "id": 1,
                                "template_id": 1,
                                "title": "Пол",
                                "scheduled_date": "2026-06-01",
                                "assignee": {
                                    "id": 1,
                                    "name": "Аня",
                                    "color": "#FF5733",
                                    "active": True,
                                    "created_at": "2026-01-01T00:00:00+00:00",
                                },
                                "status": "pending",
                                "sp_cost_current": 3,
                                "sp_cost_at_completion": None,
                                "completed_at": None,
                                "completed_by": None,
                                "transfers": [],
                            },
                        ],
                    },
                    "users": [
                        {
                            "id": 1,
                            "name": "Аня",
                            "color": "#FF5733",
                            "active": True,
                            "created_at": "2026-01-01T00:00:00+00:00",
                        },
                    ],
                },
            ],
        },
    }


class BalanceEntryOut(BaseModel):
    user: UserOut
    sp_sum: int
    tasks_count: int


class SummaryOut(BaseModel):
    pending: int
    overdue: int
    done_this_month: int


class DashboardOut(BaseModel):
    balance_30d: list[BalanceEntryOut]
    balance_current_month: list[BalanceEntryOut]
    overdue: list[TaskInstanceOut]
    recent_done: list[TaskInstanceOut]
    summary: SummaryOut


class ErrorOut(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorOut
