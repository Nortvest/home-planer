"""Роутер действий над инстансами: /api/instances."""
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos import TaskInstanceDTO, TaskTransferDTO
from src.application.use_cases import (
    CancelInstanceUseCase,
    CompleteInstanceUseCase,
    ReassignInstanceUseCase,
    RestoreInstanceUseCase,
    UncompleteInstanceUseCase,
)
from src.application.use_cases.instances import _get_transfers_dto, _to_instance_dto
from src.domain.exceptions import (
    DomainError,
    InstanceAlreadyCancelledError,
    InstanceAlreadyCompletedError,
    InstanceNotCompletedError,
    InstanceNotFoundError,
    UserNotFoundError,
)
from src.infrastructure.repos.clock_adapter import SystemClock
from src.infrastructure.repos.instance_repo_sqlite import SqliteInstanceRepository
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository
from src.infrastructure.repos.transfer_repo_sqlite import SqliteTransferRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository
from src.infrastructure.settings import get_settings
from src.presentation.deps import (
    get_cancel_use_case,
    get_complete_use_case,
    get_reassign_use_case,
    get_restore_use_case,
    get_uncomplete_use_case,
)
from src.presentation.schemas import (
    CompleteIn,
    ReassignIn,
    TaskInstanceOut,
    TaskTransferOut,
    TransfersOut,
    UserOut,
)

router = APIRouter(prefix="/api/instances", tags=["instances"])


EXCEPTION_MAP: dict[type[DomainError], tuple[int, str]] = {
    InstanceNotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    InstanceAlreadyCancelledError: (status.HTTP_409_CONFLICT, "conflict"),
    InstanceAlreadyCompletedError: (status.HTTP_409_CONFLICT, "conflict"),
    InstanceNotCompletedError: (status.HTTP_409_CONFLICT, "conflict"),
}


def _handle_domain_error(exc: DomainError) -> None:
    http_code, error_code = EXCEPTION_MAP.get(
        type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error"),
    )
    raise HTTPException(
        status_code=http_code,
        detail={"code": error_code, "message": str(exc)},
    ) from exc


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


def _transfer_dto_to_out(t: TaskTransferDTO) -> TaskTransferOut:
    return TaskTransferOut(
        id=t.id,
        from_user=(
            UserOut.model_validate(t.from_user.__dict__) if t.from_user else None
        ),
        to_user=(
            UserOut.model_validate(t.to_user.__dict__) if t.to_user else None
        ),
        transferred_at=t.transferred_at,
    )


@router.get("/{instance_id:int}", response_model=TaskInstanceOut)
def get_instance(instance_id: int) -> TaskInstanceOut:
    db_path = get_settings().db_path_resolved
    user_repo = SqliteUserRepository(db_path)
    transfer_repo = SqliteTransferRepository(db_path)
    instance_repo = SqliteInstanceRepository(db_path)
    template_repo_instance = SqliteTemplateRepository(db_path)
    clock = SystemClock()

    instance = instance_repo.get(instance_id)
    if instance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Инстанс не найден: {instance_id}"},
        )

    inst_dto = _to_instance_dto(
        instance, user_repo, transfer_repo, clock, template_repo_instance,
    )
    return _instance_dto_to_out(inst_dto)


@router.post("/{instance_id:int}/reassign", response_model=TaskInstanceOut)
def reassign(
    instance_id: int,
    body: ReassignIn,
    uc: ReassignInstanceUseCase = Depends(get_reassign_use_case),  # noqa: B008
) -> TaskInstanceOut:
    try:
        inst = uc.execute(instance_id, body.to_user_id)
    except DomainError as exc:
        _handle_domain_error(exc)
    return _instance_dto_to_out(inst)


@router.post("/{instance_id:int}/complete", response_model=TaskInstanceOut)
def complete(
    instance_id: int,
    body: CompleteIn,
    uc: CompleteInstanceUseCase = Depends(get_complete_use_case),  # noqa: B008
) -> TaskInstanceOut:
    try:
        inst = uc.execute(instance_id, body.completed_by_id)
    except DomainError as exc:
        _handle_domain_error(exc)
    return _instance_dto_to_out(inst)


@router.post("/{instance_id:int}/uncomplete", response_model=TaskInstanceOut)
def uncomplete(
    instance_id: int,
    uc: UncompleteInstanceUseCase = Depends(get_uncomplete_use_case),  # noqa: B008
) -> TaskInstanceOut:
    try:
        inst = uc.execute(instance_id)
    except DomainError as exc:
        _handle_domain_error(exc)
    return _instance_dto_to_out(inst)


@router.post("/{instance_id:int}/cancel", response_model=TaskInstanceOut)
def cancel(
    instance_id: int,
    uc: CancelInstanceUseCase = Depends(get_cancel_use_case),  # noqa: B008
) -> TaskInstanceOut:
    try:
        inst = uc.execute(instance_id)
    except DomainError as exc:
        _handle_domain_error(exc)
    return _instance_dto_to_out(inst)


@router.post("/{instance_id:int}/restore", response_model=TaskInstanceOut)
def restore(
    instance_id: int,
    uc: RestoreInstanceUseCase = Depends(get_restore_use_case),  # noqa: B008
) -> TaskInstanceOut:
    try:
        inst = uc.execute(instance_id)
    except DomainError as exc:
        _handle_domain_error(exc)
    return _instance_dto_to_out(inst)


@router.get("/{instance_id:int}/transfers", response_model=TransfersOut)
def get_transfers(instance_id: int) -> TransfersOut:
    db_path = get_settings().db_path_resolved
    user_repo = SqliteUserRepository(db_path)
    transfer_repo = SqliteTransferRepository(db_path)
    instance_repo = SqliteInstanceRepository(db_path)

    instance = instance_repo.get(instance_id)
    if instance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Инстанс не найден: {instance_id}"},
        )

    transfers_dto = _get_transfers_dto(instance_id, transfer_repo, user_repo)
    transfers_out = [_transfer_dto_to_out(t) for t in transfers_dto]
    return TransfersOut(transfers=transfers_out)
