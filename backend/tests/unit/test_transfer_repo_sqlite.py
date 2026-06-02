"""Тесты TaskTransferRepositorySqlite."""
from datetime import date, datetime, timezone

from src.domain.entities import TaskInstance, TaskTransfer
from src.infrastructure.repos.instance_repo_sqlite import SqliteInstanceRepository
from src.infrastructure.repos.transfer_repo_sqlite import SqliteTransferRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository


class TestSqliteTransferRepository:

    def test_create_and_list(self, db_path: str) -> None:
        user_repo = SqliteUserRepository(db_path)
        u_from = user_repo.create("From", "#111111")
        u_to = user_repo.create("To", "#222222")

        inst_repo = SqliteInstanceRepository(db_path)
        inst = inst_repo.create(TaskInstance(0, None, "T", date(2026, 6, 1), None))

        transfer_repo = SqliteTransferRepository(db_path)
        transfer = TaskTransfer(
            id=0,
            instance_id=inst.id,
            from_user_id=u_from.id,
            to_user_id=u_to.id,
            transferred_at=datetime.now(timezone.utc),
        )
        created = transfer_repo.create(transfer)
        assert created.id > 0
        assert created.from_user_id == u_from.id
        assert created.to_user_id == u_to.id

        transfers = transfer_repo.list_by_instance(inst.id)
        assert len(transfers) == 1

    def test_list_empty(self, db_path: str) -> None:
        repo = SqliteTransferRepository(db_path)
        transfers = repo.list_by_instance(999)
        assert len(transfers) == 0

    def test_multiple_transfers_ordered(self, db_path: str) -> None:
        _create_and_verify_multi_transfer(db_path)


def _create_and_verify_multi_transfer(db_path: str) -> None:
    user_repo = SqliteUserRepository(db_path)
    u1 = user_repo.create("U1", "#111111")
    u2 = user_repo.create("U2", "#222222")
    u3 = user_repo.create("U3", "#333333")

    inst_repo = SqliteInstanceRepository(db_path)
    inst = inst_repo.create(TaskInstance(0, None, "T", date(2026, 6, 1), None))

    repo = SqliteTransferRepository(db_path)
    t1 = TaskTransfer(
        id=0, instance_id=inst.id, from_user_id=u1.id, to_user_id=u2.id,
        transferred_at=datetime.now(timezone.utc),
    )
    t2 = TaskTransfer(
        id=0, instance_id=inst.id, from_user_id=u2.id, to_user_id=u3.id,
        transferred_at=datetime.now(timezone.utc),
    )
    repo.create(t1)
    repo.create(t2)
    transfers = repo.list_by_instance(inst.id)
    assert len(transfers) == 2
    assert transfers[0].to_user_id == u2.id
    assert transfers[1].to_user_id == u3.id
