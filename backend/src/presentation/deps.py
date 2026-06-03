"""Dependency injection: сборка use-кейсов из репозиториев."""

from src.application.ports import (
    Clock,
    InstanceRepository,
    TemplateRepository,
    TransferRepository,
    UserRepository,
)
from src.application.use_cases import (
    CancelInstanceUseCase,
    CompleteInstanceUseCase,
    GetCalendarRangeUseCase,
    GetCalendarUseCase,
    GetDashboardUseCase,
    MaterializerUseCase,
    ReassignInstanceUseCase,
    RestoreInstanceUseCase,
    TemplateManagementUseCase,
    UncompleteInstanceUseCase,
    UserManagementUseCase,
)
from src.infrastructure.repos.clock_adapter import SystemClock
from src.infrastructure.repos.instance_repo_sqlite import SqliteInstanceRepository
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository
from src.infrastructure.repos.transfer_repo_sqlite import SqliteTransferRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository
from src.infrastructure.settings import get_settings


def _make_repos() -> tuple[
    UserRepository,
    TemplateRepository,
    InstanceRepository,
    TransferRepository,
    Clock,
]:
    db_path = get_settings().db_path_resolved
    user_repo: UserRepository = SqliteUserRepository(db_path)
    template_repo: TemplateRepository = SqliteTemplateRepository(db_path)
    instance_repo: InstanceRepository = SqliteInstanceRepository(db_path)
    transfer_repo: TransferRepository = SqliteTransferRepository(db_path)
    clock: Clock = SystemClock()
    return user_repo, template_repo, instance_repo, transfer_repo, clock


def get_user_use_case() -> UserManagementUseCase:
    user_repo, *_ = _make_repos()
    return UserManagementUseCase(user_repo)


def get_template_use_case() -> TemplateManagementUseCase:
    _, template_repo, *_ = _make_repos()
    return TemplateManagementUseCase(template_repo)


def get_calendar_use_case() -> GetCalendarUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    materializer = MaterializerUseCase(template_repo, instance_repo)
    return GetCalendarUseCase(
        materializer,
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_calendar_range_use_case() -> GetCalendarRangeUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    materializer = MaterializerUseCase(template_repo, instance_repo)
    return GetCalendarRangeUseCase(
        materializer,
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_reassign_use_case() -> ReassignInstanceUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return ReassignInstanceUseCase(instance_repo, user_repo, transfer_repo, template_repo, clock)


def get_complete_use_case() -> CompleteInstanceUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return CompleteInstanceUseCase(
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_uncomplete_use_case() -> UncompleteInstanceUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return UncompleteInstanceUseCase(
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_cancel_use_case() -> CancelInstanceUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return CancelInstanceUseCase(
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_restore_use_case() -> RestoreInstanceUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return RestoreInstanceUseCase(
        instance_repo,
        user_repo,
        transfer_repo,
        template_repo,
        clock,
    )


def get_dashboard_use_case() -> GetDashboardUseCase:
    user_repo, template_repo, instance_repo, transfer_repo, clock = _make_repos()
    return GetDashboardUseCase(
        user_repo,
        instance_repo,
        template_repo,
        transfer_repo,
        clock,
    )
