from datetime import datetime, timezone

from src.application.dtos import TaskInstanceDTO, TaskTransferDTO, UserDTO
from src.application.ports import (
    Clock,
    InstanceRepository,
    TemplateRepository,
    TransferRepository,
    UserRepository,
)
from src.domain.entities import TaskInstance, TaskTransfer
from src.domain.exceptions import (
    InstanceAlreadyCompletedError,
    InstanceNotFoundError,
    UserNotFoundError,
)
from src.domain.services import compute_status


class ReassignInstanceUseCase:
    def __init__(
        self,
        instance_repo: InstanceRepository,
        user_repo: UserRepository,
        transfer_repo: TransferRepository,
        clock: Clock,
    ) -> None:
        self._instance_repo = instance_repo
        self._user_repo = user_repo
        self._transfer_repo = transfer_repo
        self._clock = clock

    def execute(self, instance_id: int, to_user_id: int) -> TaskInstanceDTO:
        instance = self._instance_repo.get(instance_id)
        if instance is None:
            raise InstanceNotFoundError(f"Инстанс не найден: {instance_id}")

        to_user = self._user_repo.get(to_user_id)
        if to_user is None:
            raise UserNotFoundError(f"Пользователь не найден: {to_user_id}")

        transfer = TaskTransfer(
            id=0,
            instance_id=instance_id,
            from_user_id=instance.assignee_id,
            to_user_id=to_user_id,
            transferred_at=datetime.now(tz=timezone.utc),
        )
        self._transfer_repo.create(transfer)

        instance.assignee_id = to_user_id
        updated = self._instance_repo.update(instance)
        return _to_instance_dto(
            updated, self._user_repo, self._transfer_repo, self._clock,
        )


class CompleteInstanceUseCase:
    def __init__(
        self,
        instance_repo: InstanceRepository,
        user_repo: UserRepository,
        transfer_repo: TransferRepository,
        template_repo: TemplateRepository,
        clock: Clock,
    ) -> None:
        self._instance_repo = instance_repo
        self._user_repo = user_repo
        self._transfer_repo = transfer_repo
        self._template_repo = template_repo
        self._clock = clock

    def execute(self, instance_id: int, completed_by_id: int) -> TaskInstanceDTO:
        instance = _validate_complete_request(
            instance_id,
            completed_by_id,
            self._instance_repo,
            self._user_repo,
        )

        sp_cost = instance.sp_cost_at_completion
        if instance.template_id is not None:
            tpl = self._template_repo.get(instance.template_id)
            if tpl is not None:
                sp_cost = tpl.sp_cost

        instance.completed_at = datetime.now(tz=timezone.utc)
        instance.completed_by_id = completed_by_id
        instance.sp_cost_at_completion = sp_cost
        updated = self._instance_repo.update(instance)
        return _to_instance_dto(
            updated,
            self._user_repo,
            self._transfer_repo,
            self._clock,
            self._template_repo,
        )


def _validate_complete_request(
    instance_id: int,
    completed_by_id: int,
    instance_repo: InstanceRepository,
    user_repo: UserRepository,
) -> TaskInstance:
    instance = instance_repo.get(instance_id)
    if instance is None:
        raise InstanceNotFoundError(f"Инстанс не найден: {instance_id}")

    if instance.is_done:
        raise InstanceAlreadyCompletedError("Инстанс уже закрыт")

    completed_user = user_repo.get(completed_by_id)
    if completed_user is None:
        raise UserNotFoundError(f"Пользователь не найден: {completed_by_id}")

    return instance


def _to_instance_dto(
    inst: TaskInstance,
    user_repo: UserRepository,
    transfer_repo: TransferRepository,
    clock: Clock,
    template_repo: TemplateRepository | None = None,
) -> TaskInstanceDTO:
    assignee: UserDTO | None = _get_user_dto(user_repo, inst.assignee_id)
    completed_by: UserDTO | None = _get_user_dto(user_repo, inst.completed_by_id)

    status = compute_status(inst, clock.today()).value

    if inst.is_done and inst.sp_cost_at_completion is not None:
        sp_current = inst.sp_cost_at_completion
    elif template_repo is not None and inst.template_id is not None:
        tpl = template_repo.get(inst.template_id)
        sp_current = tpl.sp_cost if tpl is not None else 0
    else:
        sp_current = 0

    transfers = _get_transfers_dto(inst.id, transfer_repo, user_repo)

    return TaskInstanceDTO(
        id=inst.id,
        template_id=inst.template_id,
        title=inst.title,
        scheduled_date=inst.scheduled_date,
        assignee=assignee,
        status=status,
        sp_cost_current=sp_current,
        sp_cost_at_completion=inst.sp_cost_at_completion,
        completed_at=inst.completed_at,
        completed_by=completed_by,
        transfers=transfers,
    )


def _get_user_dto(user_repo: UserRepository, user_id: int | None) -> UserDTO | None:
    if user_id is None:
        return None
    u = user_repo.get(user_id)
    if u is None:
        return None
    return UserDTO(
        id=u.id,
        name=u.name,
        color=u.color,
        active=u.active,
        created_at=u.created_at,
    )


def _get_transfers_dto(
    instance_id: int,
    transfer_repo: TransferRepository,
    user_repo: UserRepository,
) -> list[TaskTransferDTO]:
    result: list[TaskTransferDTO] = []
    for tr in transfer_repo.list_by_instance(instance_id):
        fu = _get_user_dto(user_repo, tr.from_user_id)
        tu = _get_user_dto(user_repo, tr.to_user_id)
        result.append(
            TaskTransferDTO(
                id=tr.id,
                from_user=fu,
                to_user=tu,
                transferred_at=tr.transferred_at,
            ),
        )
    return result
