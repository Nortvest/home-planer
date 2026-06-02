from dataclasses import dataclass
from datetime import (
    date,
    datetime,
)


@dataclass
class UserDTO:
    id: int
    name: str
    color: str
    active: bool
    created_at: datetime | None


@dataclass
class TaskTemplateDTO:
    id: int
    title: str
    description: str | None
    sp_cost: int
    recurrence_type: str
    recurrence_params: dict[str, int]
    default_assignee_id: int | None
    active: bool
    created_at: datetime | None


@dataclass
class TaskTransferDTO:
    id: int
    from_user: UserDTO | None
    to_user: UserDTO | None
    transferred_at: datetime


@dataclass
class TaskInstanceDTO:
    id: int
    template_id: int | None
    title: str
    scheduled_date: date
    assignee: UserDTO | None
    status: str
    sp_cost_current: int
    sp_cost_at_completion: int | None
    completed_at: datetime | None
    completed_by: UserDTO | None
    transfers: list[TaskTransferDTO]


@dataclass
class CalendarDayDTO:
    date: date
    instances: list[TaskInstanceDTO]


@dataclass
class CalendarDTO:
    year: int
    month: int
    days: dict[str, list[TaskInstanceDTO]]
    users: list[UserDTO]


@dataclass
class BalanceEntryDTO:
    user: UserDTO
    sp_sum: int
    tasks_count: int


@dataclass
class SummaryDTO:
    pending: int
    overdue: int
    done_this_month: int


@dataclass
class DashboardDTO:
    balance_30d: list[BalanceEntryDTO]
    balance_current_month: list[BalanceEntryDTO]
    overdue: list[TaskInstanceDTO]
    recent_done: list[TaskInstanceDTO]
    summary: SummaryDTO
