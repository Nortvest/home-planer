from abc import ABC, abstractmethod

from src.domain.entities import TaskTransfer


class TransferRepository(ABC):
    @abstractmethod
    def create(self, transfer: TaskTransfer) -> TaskTransfer:
        """Создаёт запись о переназначении и возвращает её с назначенным ID."""
        raise NotImplementedError

    @abstractmethod
    def list_by_instance(self, instance_id: int) -> list[TaskTransfer]:
        """Возвращает все переназначения для заданного инстанса (хронологически)."""
        raise NotImplementedError
