"""Роутер шаблонов: /api/templates."""
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases import TemplateManagementUseCase
from src.domain.exceptions import (
    DomainError,
    TemplateNotFoundError,
)
from src.presentation.deps import get_template_use_case
from src.presentation.schemas import (
    TaskTemplateCreateIn,
    TaskTemplateOut,
    TaskTemplateUpdateIn,
    TemplatesListOut,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


EXCEPTION_MAP: dict[type[DomainError], tuple[int, str]] = {
    TemplateNotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
}


def _handle_domain_error(exc: DomainError) -> None:
    http_code, error_code = EXCEPTION_MAP.get(
        type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error"),
    )
    raise HTTPException(
        status_code=http_code,
        detail={"code": error_code, "message": str(exc)},
    ) from exc


@router.get("", response_model=TemplatesListOut)
def list_all(
    uc: TemplateManagementUseCase = Depends(get_template_use_case),  # noqa: B008
) -> TemplatesListOut:
    try:
        templates = uc.get_all()
    except DomainError as exc:
        _handle_domain_error(exc)
    return TemplatesListOut(
        templates=[TaskTemplateOut.model_validate(t.__dict__) for t in templates],
    )


@router.get("/active", response_model=TemplatesListOut)
def list_active(
    uc: TemplateManagementUseCase = Depends(get_template_use_case),  # noqa: B008
) -> TemplatesListOut:
    try:
        templates = uc.get_active()
    except DomainError as exc:
        _handle_domain_error(exc)
    return TemplatesListOut(
        templates=[TaskTemplateOut.model_validate(t.__dict__) for t in templates],
    )


@router.post("", response_model=TaskTemplateOut, status_code=status.HTTP_201_CREATED)
def create(
    body: TaskTemplateCreateIn,
    uc: TemplateManagementUseCase = Depends(get_template_use_case),  # noqa: B008
) -> TaskTemplateOut:
    try:
        tpl = uc.create(
            title=body.title,
            description=body.description,
            sp_cost=body.sp_cost,
            recurrence_type=body.recurrence_type,
            recurrence_params=body.to_params_dict(),
            default_assignee_id=body.default_assignee_id,
        )
    except DomainError as exc:
        _handle_domain_error(exc)
    return TaskTemplateOut.model_validate(tpl.__dict__)


@router.patch("/{template_id:int}", response_model=TaskTemplateOut)
def update(
    template_id: int,
    body: TaskTemplateUpdateIn,
    uc: TemplateManagementUseCase = Depends(get_template_use_case),  # noqa: B008
) -> TaskTemplateOut:
    try:
        tpl = uc.update(
            template_id,
            title=body.title,
            description=body.description,
            sp_cost=body.sp_cost,
            recurrence_type=body.recurrence_type,
            recurrence_params=(
                body.to_params_dict() if body.recurrence_params is not None else None
            ),
            default_assignee_id=body.default_assignee_id,
            active=body.active,
        )
    except DomainError as exc:
        _handle_domain_error(exc)
    return TaskTemplateOut.model_validate(tpl.__dict__)


@router.delete("/{template_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    template_id: int,
    uc: TemplateManagementUseCase = Depends(get_template_use_case),  # noqa: B008
) -> None:
    try:
        uc.delete(template_id)
    except DomainError as exc:
        _handle_domain_error(exc)
