"""Smoke-test: полный цикл — создать пользователя, шаблон, инстанс, закрыть, переназначить, проверить баланс."""
from datetime import date, datetime, timezone
from typing import TypedDict

from src.domain.entities import TaskInstance, TaskTemplate, TaskTransfer, User
from src.domain.services import compute_balance
from src.infrastructure.repos.instance_repo_sqlite import SqliteInstanceRepository
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository
from src.infrastructure.repos.transfer_repo_sqlite import SqliteTransferRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository


class _Repos(TypedDict):
    user_repo: SqliteUserRepository
    tmpl_repo: SqliteTemplateRepository
    inst_repo: SqliteInstanceRepository
    xfer_repo: SqliteTransferRepository


class TestSmoke:

    def test_full_lifecycle(self, db_path: str) -> None:
        repos = _setup_repos(db_path)
        u1, u2 = _create_users(repos["user_repo"])
        tmpl = _create_template(repos["tmpl_repo"], u1.id)
        inst = _create_instance(repos["inst_repo"], tmpl, u1.id)

        _reassign_to_user(repos["xfer_repo"], repos["inst_repo"], inst, u1.id, u2.id)
        _complete_instance(repos["inst_repo"], inst, u2.id)
        _verify_balance(repos["inst_repo"], u2.id)
        _verify_post_completion(repos["inst_repo"], repos["user_repo"], u2)


def _setup_repos(db_path: str) -> _Repos:
    return {
        "user_repo": SqliteUserRepository(db_path),
        "tmpl_repo": SqliteTemplateRepository(db_path),
        "inst_repo": SqliteInstanceRepository(db_path),
        "xfer_repo": SqliteTransferRepository(db_path),
    }


def _create_users(user_repo: SqliteUserRepository) -> tuple[User, User]:
    return user_repo.create("Иван", "#FF0000"), user_repo.create("Мария", "#00FF00")


def _create_template(tmpl_repo: SqliteTemplateRepository, assignee_id: int) -> TaskTemplate:
    return tmpl_repo.create(
        title="Мусор",
        description="Вынести мусор каждый понедельник",
        sp_cost=3,
        recurrence_type="weekly",
        recurrence_params={"weekday": 0},
        default_assignee_id=assignee_id,
    )


def _create_instance(
    inst_repo: SqliteInstanceRepository,
    tmpl: TaskTemplate,
    assignee_id: int,
) -> TaskInstance:
    inst = TaskInstance(
        id=0,
        template_id=tmpl.id,
        title="Мусор",
        scheduled_date=date(2026, 6, 1),
        assignee_id=assignee_id,
    )
    return inst_repo.create(inst)


def _reassign_to_user(
    xfer_repo: SqliteTransferRepository,
    inst_repo: SqliteInstanceRepository,
    inst: TaskInstance,
    from_id: int,
    to_id: int,
) -> None:
    transfer = TaskTransfer(
        id=0,
        instance_id=inst.id,
        from_user_id=from_id,
        to_user_id=to_id,
        transferred_at=datetime.now(tz=timezone.utc),
    )
    xfer = xfer_repo.create(transfer)
    assert xfer.to_user_id == to_id
    transfers = xfer_repo.list_by_instance(inst.id)
    assert len(transfers) == 1

    updated = inst_repo.update(TaskInstance(
        id=inst.id,
        template_id=inst.template_id,
        title=inst.title,
        scheduled_date=date(2026, 6, 1),
        assignee_id=to_id,
    ))
    assert updated.assignee_id == to_id


def _complete_instance(
    inst_repo: SqliteInstanceRepository,
    inst: TaskInstance,
    user_id: int,
) -> None:
    completed_at = datetime(2026, 6, 1, 14, 0, 0, tzinfo=timezone.utc)
    completed = inst_repo.update(TaskInstance(
        id=inst.id,
        template_id=inst.template_id,
        title="Мусор",
        scheduled_date=date(2026, 6, 1),
        assignee_id=user_id,
        completed_at=completed_at,
        completed_by_id=user_id,
        sp_cost_at_completion=3,
    ))
    assert completed.completed_by_id == user_id
    assert completed.sp_cost_at_completion == 3


def _verify_balance(
    inst_repo: SqliteInstanceRepository,
    user_id: int,
) -> None:
    completed_instances = inst_repo.list_completed_by_user_and_date_range(
        user_id, date(2026, 5, 1), date(2026, 6, 30),
    )
    assert len(completed_instances) == 1
    sp_sum, count = compute_balance(
        completed_instances, user_id, date(2026, 5, 1), date(2026, 6, 30),
    )
    assert sp_sum == 3
    assert count == 1


def _verify_post_completion(
    inst_repo: SqliteInstanceRepository,
    user_repo: SqliteUserRepository,
    u2: User,
) -> None:
    assert user_repo.has_active_instances(u2.id) is False
    overdue = inst_repo.list_overdue(date(2026, 6, 15))
    assert len(overdue) == 0
    recent = inst_repo.list_completed_recent(5)
    assert len(recent) == 1
    assert recent[0].title == "Мусор"
