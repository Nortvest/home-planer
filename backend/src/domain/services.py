from datetime import date, timedelta

from src.domain.entities import TaskInstance, TaskTemplate
from src.domain.value_objects import RecurrenceType, TaskStatus

_MONTHS_IN_YEAR = 12


def compute_status(instance: TaskInstance, today: date) -> TaskStatus:  # noqa: PLR0911
    """Вычислить статус инстанса на основе scheduled_date и факта завершения."""
    if instance.is_cancelled:
        return TaskStatus.CANCELLED
    if instance.is_done:
        return TaskStatus.DONE
    if instance.scheduled_date < today:
        return TaskStatus.OVERDUE
    return TaskStatus.PENDING


def _generate_daily(start: date, end: date) -> list[date]:
    result: list[date] = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=1)
    return result


def _generate_weekly(template: TaskTemplate, start: date, end: date) -> list[date]:
    target_weekday = template.recurrence_params["weekday"]
    result: list[date] = []
    current = start
    while current <= end:
        if current.weekday() == target_weekday:
            result.append(current)
        current += timedelta(days=1)
    return result


def _generate_every_n_days(template: TaskTemplate, start: date, end: date) -> list[date]:
    interval = template.recurrence_params["interval_days"]
    result: list[date] = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=interval)
    return result


def generate_recurrence_dates(template: TaskTemplate, start: date, end: date) -> list[date]:
    """Сгенерировать даты повторов шаблона в диапазоне [start, end]."""
    result: list[date] = []
    match template.recurrence_type:
        case RecurrenceType.NONE:
            pass
        case RecurrenceType.DAILY:
            result = _generate_daily(start, end)
        case RecurrenceType.WEEKLY:
            result = _generate_weekly(template, start, end)
        case RecurrenceType.EVERY_N_DAYS:
            result = _generate_every_n_days(template, start, end)
    return result


def _is_in_range(inst_date: date, start: date, end: date) -> bool:
    return start <= inst_date <= end


def compute_balance(
    instances: list[TaskInstance],
    user_id: int,
    start: date,
    end: date,
) -> tuple[int, int]:
    """Подсчитать баланс пользователя за период [start, end].

    На вход — список завершённых инстансов, id пользователя, начала и конца периода.
    Возвращает (сумма SP, количество задач).
    """
    sp_sum = 0
    count = 0

    for inst in instances:
        if inst.completed_by_id != user_id:
            continue
        if not inst.is_done or inst.completed_at is None:
            continue

        inst_date = inst.completed_at.date()
        if not _is_in_range(inst_date, start, end):
            continue

        if inst.sp_cost_at_completion is not None:
            sp_sum += inst.sp_cost_at_completion
        count += 1

    return sp_sum, count


def compute_sliding_30d_balance(
    instances: list[TaskInstance],
    user_id: int,
    today: date,
) -> tuple[int, int]:
    """Скользящий 30-дневный баланс: [today - 29, today]."""
    start = today - timedelta(days=29)
    return compute_balance(instances, user_id, start, today)


def compute_monthly_balance(
    instances: list[TaskInstance],
    user_id: int,
    year: int,
    month: int,
) -> tuple[int, int]:
    """Помесячный баланс за календарный месяц."""
    start = date(year, month, 1)
    if month == _MONTHS_IN_YEAR:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return compute_balance(instances, user_id, start, end)
