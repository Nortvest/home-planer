"""Роутер пользователей: /api/users."""
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases import UserManagementUseCase
from src.domain.exceptions import (
    DomainError,
    DuplicateUserNameError,
    UserHasActiveTasksError,
    UserNotFoundError,
)
from src.presentation.deps import get_user_use_case
from src.presentation.schemas import (
    UserCreateIn,
    UserOut,
    UsersListOut,
    UserUpdateIn,
)

router = APIRouter(prefix="/api/users", tags=["users"])


EXCEPTION_MAP: dict[type[DomainError], tuple[int, str]] = {
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    DuplicateUserNameError: (status.HTTP_409_CONFLICT, "conflict"),
    UserHasActiveTasksError: (status.HTTP_409_CONFLICT, "has_active_tasks"),
}


def _handle_domain_error(exc: DomainError) -> None:
    http_code, error_code = EXCEPTION_MAP.get(
        type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error"),
    )
    raise HTTPException(
        status_code=http_code,
        detail={"code": error_code, "message": str(exc)},
    ) from exc


@router.get("", response_model=UsersListOut)
def list_all(
    uc: UserManagementUseCase = Depends(get_user_use_case),  # noqa: B008
) -> UsersListOut:
    try:
        users = uc.get_all()
    except DomainError as exc:
        _handle_domain_error(exc)
    return UsersListOut(users=[UserOut.model_validate(u.__dict__) for u in users])


@router.get("/active", response_model=UsersListOut)
def list_active(
    uc: UserManagementUseCase = Depends(get_user_use_case),  # noqa: B008
) -> UsersListOut:
    try:
        users = uc.get_active()
    except DomainError as exc:
        _handle_domain_error(exc)
    return UsersListOut(users=[UserOut.model_validate(u.__dict__) for u in users])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create(
    body: UserCreateIn,
    uc: UserManagementUseCase = Depends(get_user_use_case),  # noqa: B008
) -> UserOut:
    try:
        user = uc.create(body.name, body.color)
    except DomainError as exc:
        _handle_domain_error(exc)
    return UserOut.model_validate(user.__dict__)


@router.patch("/{user_id:int}", response_model=UserOut)
def update(
    user_id: int,
    body: UserUpdateIn,
    uc: UserManagementUseCase = Depends(get_user_use_case),  # noqa: B008
) -> UserOut:
    try:
        user = uc.update(user_id, name=body.name, color=body.color, active=body.active)
    except DomainError as exc:
        _handle_domain_error(exc)
    return UserOut.model_validate(user.__dict__)


@router.delete("/{user_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    user_id: int,
    uc: UserManagementUseCase = Depends(get_user_use_case),  # noqa: B008
) -> None:
    try:
        uc.delete(user_id)
    except DomainError as exc:
        _handle_domain_error(exc)
