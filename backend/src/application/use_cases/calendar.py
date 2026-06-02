from calendar import monthrange
from datetime import date

from src.application.dtos import CalendarDTO, TaskInstanceDTO, UserDTO
from src.application.ports import (
    Clock,
    InstanceRepository,
    TemplateRepository,
    TransferRepository,
    UserRepository,
)
from src.application.use_cases.instances import _to_instance_dto
from src.domain.entities import TaskInstance, TaskTemplate
from src.domain.services import generate_recurrence_dates


class MaterializerUseCase:
    """Материализация инстансов по запросу на диапазон дат."""

    def __init__(
        self,
        template_repo: TemplateRepository,
        instance_repo: InstanceRepository,
    ) -> None:
        self._template_repo = template_repo
        self._instance_repo = instance_repo

    def materialize(self, start: date, end: date, today: date) -> None:
        active_templates = self._template_repo.list_active()
        for tpl in active_templates:
            dates = generate_recurrence_dates(tpl, start, end)
            valid_dates = {d for d in dates if d >= today}

            for d in dates:
                if d < today:
                    continue
                existing = self._instance_repo.list_by_template_and_date(tpl.id, d)
                if not existing:
                    instance = TaskInstance(
                        id=0,
                        template_id=tpl.id,
                        title=tpl.title,
                        scheduled_date=d,
                        assignee_id=tpl.default_assignee_id,
                    )
                    self._instance_repo.create(instance)

            self._cleanup_orphaned(tpl, start, end, today, valid_dates)

    def _cleanup_orphaned(
        self, tpl: TaskTemplate, start: date, end: date,
        today: date, valid_dates: set[date],
    ) -> None:
        instances = self._instance_repo.list_by_date_range(start, end)
        for inst in instances:
            if inst.template_id != tpl.id:
                continue
            if inst.scheduled_date < today:
                continue
            if inst.is_done:
                continue
            if inst.scheduled_date not in valid_dates:
                self._instance_repo.delete_by_id(inst.id)


class GetCalendarUseCase:
    def __init__(  # noqa: PLR0913, PLR0917
        self,
        materializer: MaterializerUseCase,
        instance_repo: InstanceRepository,
        user_repo: UserRepository,
        transfer_repo: TransferRepository,
        template_repo: TemplateRepository,
        clock: Clock,
    ) -> None:
        self._materializer = materializer
        self._instance_repo = instance_repo
        self._user_repo = user_repo
        self._transfer_repo = transfer_repo
        self._template_repo = template_repo
        self._clock = clock

    def execute(self, year: int, month: int) -> CalendarDTO:
        start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end = date(year, month, last_day)

        self._materializer.materialize(start, end, self._clock.today())

        instances = self._instance_repo.list_by_date_range(start, end)
        users = self._user_repo.list_active()

        days: dict[str, list[TaskInstanceDTO]] = {}
        for inst in instances:
            key = inst.scheduled_date.isoformat()
            dto = _to_instance_dto(
                inst,
                self._user_repo,
                self._transfer_repo,
                self._clock,
                self._template_repo,
            )
            days.setdefault(key, []).append(dto)

        user_dtos = [
            UserDTO(
                id=u.id,
                name=u.name,
                color=u.color,
                active=u.active,
                created_at=u.created_at,
            )
            for u in users
        ]

        return CalendarDTO(
            year=year,
            month=month,
            days=days,
            users=user_dtos,
        )
