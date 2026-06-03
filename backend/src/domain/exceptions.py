class DomainError(Exception):
    """Базовое доменное исключение."""


class UserHasActiveTasksError(DomainError):
    """У пользователя есть незакрытые задачи — нельзя удалить/деактивировать."""


class InvalidColorError(DomainError):
    """Недопустимый hex-цвет."""


class UserNotFoundError(DomainError):
    """Пользователь не найден."""


class TemplateNotFoundError(DomainError):
    """Шаблон задачи не найден."""


class InstanceNotFoundError(DomainError):
    """Инстанс задачи не найден."""


class InstanceAlreadyCompletedError(DomainError):
    """Попытка закрыть уже закрытый инстанс."""


class DuplicateUserNameError(DomainError):
    """Имя пользователя уже занято."""


class InstanceNotCompletedError(DomainError):
    """Попытка отменить выполнение незавершённого инстанса."""


class InstanceAlreadyCancelledError(DomainError):
    """Попытка отменить уже отменённый инстанс."""
