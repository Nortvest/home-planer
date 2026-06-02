"""Роутер календаря: /api/calendar."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dtos import TaskInstanceDTO, UserDTO
from src.application.use_cases import GetCalendarUseCase
from src.domain.exceptions import DomainError
from src.presentation.deps import get_calendar_use_case
from src.presentation.schemas import (
    CalendarOut,
    TaskInstanceOut,
    TaskTransferOut,
    UserOut,
)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def _dto_to_out(inst: TaskInstanceDTO) -> TaskInstanceOut:
    return TaskInstanceOut(
        id=inst.id,
        template_id=inst.template_id,
        title=inst.title,
        scheduled_date=inst.scheduled_date,
        assignee=UserOut.model_validate(inst.assignee.__dict__) if inst.assignee else None,
        status=inst.status,
        sp_cost_current=inst.sp_cost_current,
        sp_cost_at_completion=inst.sp_cost_at_completion,
        completed_at=inst.completed_at,
        completed_by=(
            UserOut.model_validate(inst.completed_by.__dict__) if inst.completed_by else None
        ),
        transfers=[
            TaskTransferOut(
                id=t.id,
                from_user=(
                    UserOut.model_validate(t.from_user.__dict__) if t.from_user else None
                ),
                to_user=(
                    UserOut.model_validate(t.to_user.__dict__) if t.to_user else None
                ),
                transferred_at=t.transferred_at,
            )
            for t in inst.transfers
        ],
    )


def _user_dto_to_out(u: UserDTO) -> UserOut:
    return UserOut.model_validate(u.__dict__)


@router.get("", response_model=CalendarOut)
def get_calendar(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    uc: GetCalendarUseCase = Depends(get_calendar_use_case),  # noqa: B008
) -> CalendarOut:
    try:
        cal = uc.execute(year, month)
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": str(exc)},
        ) from exc

    days: dict[str, list[TaskInstanceOut]] = {}
    for date_str, instances in cal.days.items():
        days[date_str] = [_dto_to_out(i) for i in instances]

    users = [_user_dto_to_out(u) for u in cal.users]
    return CalendarOut(year=cal.year, month=cal.month, days=days, users=users)
