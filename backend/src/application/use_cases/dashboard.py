from datetime import date

from src.application.dtos import (
    BalanceEntryDTO,
    DashboardDTO,
    SummaryDTO,
    TaskInstanceDTO,
    UserDTO,
)
from src.application.ports import (
    Clock,
    InstanceRepository,
    TemplateRepository,
    TransferRepository,
    UserRepository,
)
from src.application.use_cases.instances import _to_instance_dto
from src.domain.entities import TaskInstance, User
from src.domain.services import (
    compute_monthly_balance,
    compute_sliding_30d_balance,
)


class GetDashboardUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        instance_repo: InstanceRepository,
        template_repo: TemplateRepository,
        transfer_repo: TransferRepository,
        clock: Clock,
    ) -> None:
        self._user_repo = user_repo
        self._instance_repo = instance_repo
        self._template_repo = template_repo
        self._transfer_repo = transfer_repo
        self._clock = clock

    def execute(self) -> DashboardDTO:
        today = self._clock.today()
        users = self._user_repo.list_active()
        all_instances = self._instance_repo.list_completed_recent(limit=1000)

        balance_30d = self._compute_30d(all_instances, users, today)
        year, month = today.year, today.month
        balance_current_month = self._compute_monthly(all_instances, users, year, month)

        overdue_instances = self._instance_repo.list_overdue(today)
        overdue_dtos = self._to_dtos(overdue_instances)

        recent = self._instance_repo.list_completed_recent(limit=20)
        recent_dtos = self._to_dtos(recent)

        summary = SummaryDTO(
            pending=self._instance_repo.count_by_status(today, "pending"),
            overdue=self._instance_repo.count_by_status(today, "overdue"),
            done_this_month=self._instance_repo.count_done_current_month(today),
        )

        return DashboardDTO(
            balance_30d=balance_30d,
            balance_current_month=balance_current_month,
            overdue=overdue_dtos,
            recent_done=recent_dtos,
            summary=summary,
        )

    def _compute_30d(
        self,
        instances: list[TaskInstance],
        users: list[User],
        today: date,
    ) -> list[BalanceEntryDTO]:
        result: list[BalanceEntryDTO] = []
        for u in users:
            sp_sum, count = compute_sliding_30d_balance(instances, u.id, today)
            result.append(
                BalanceEntryDTO(
                    user=_to_user_dto(u),
                    sp_sum=sp_sum,
                    tasks_count=count,
                ),
            )
        return result

    def _compute_monthly(
        self,
        instances: list[TaskInstance],
        users: list[User],
        year: int,
        month: int,
    ) -> list[BalanceEntryDTO]:
        result: list[BalanceEntryDTO] = []
        for u in users:
            sp_sum, count = compute_monthly_balance(instances, u.id, year, month)
            result.append(
                BalanceEntryDTO(
                    user=_to_user_dto(u),
                    sp_sum=sp_sum,
                    tasks_count=count,
                ),
            )
        return result

    def _to_dtos(
        self, instances: list[TaskInstance],
    ) -> list[TaskInstanceDTO]:
        return [
            _to_instance_dto(
                inst,
                self._user_repo,
                self._transfer_repo,
                self._clock,
                self._template_repo,
            )
            for inst in instances
        ]


def _to_user_dto(u: User) -> UserDTO:
    return UserDTO(
        id=u.id,
        name=u.name,
        color=u.color,
        active=u.active,
        created_at=u.created_at,
    )
