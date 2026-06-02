"""Роутер дашборда: /api/dashboard."""
from fastapi import APIRouter, Depends, HTTPException

from src.application.dtos import TaskInstanceDTO, UserDTO
from src.application.use_cases import GetDashboardUseCase
from src.domain.exceptions import DomainError
from src.presentation.deps import get_dashboard_use_case
from src.presentation.schemas import (
    BalanceEntryOut,
    DashboardOut,
    SummaryOut,
    TaskInstanceOut,
    TaskTransferOut,
    UserOut,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _user_dto_to_out(u: UserDTO) -> UserOut:
    return UserOut.model_validate(u.__dict__)


def _instance_dto_to_out(inst: TaskInstanceDTO) -> TaskInstanceOut:
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


@router.get("", response_model=DashboardOut)
def get_dashboard(
    uc: GetDashboardUseCase = Depends(get_dashboard_use_case),  # noqa: B008
) -> DashboardOut:
    try:
        dashboard = uc.execute()
    except DomainError as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": str(exc)},
        ) from exc

    balance_30d = [
        BalanceEntryOut(
            user=_user_dto_to_out(e.user),
            sp_sum=e.sp_sum,
            tasks_count=e.tasks_count,
        )
        for e in dashboard.balance_30d
    ]

    balance_current_month = [
        BalanceEntryOut(
            user=_user_dto_to_out(e.user),
            sp_sum=e.sp_sum,
            tasks_count=e.tasks_count,
        )
        for e in dashboard.balance_current_month
    ]

    overdue = [_instance_dto_to_out(i) for i in dashboard.overdue]
    recent_done = [_instance_dto_to_out(i) for i in dashboard.recent_done]
    summary = SummaryOut(
        pending=dashboard.summary.pending,
        overdue=dashboard.summary.overdue,
        done_this_month=dashboard.summary.done_this_month,
    )

    return DashboardOut(
        balance_30d=balance_30d,
        balance_current_month=balance_current_month,
        overdue=overdue,
        recent_done=recent_done,
        summary=summary,
    )
