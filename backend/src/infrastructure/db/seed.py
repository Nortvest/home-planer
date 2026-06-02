"""Сид: наполнение БД демо-данными для первого запуска.

Создаёт двух пользователей и набор базовых шаблонов задач.
Использует существующие use-кейсы через DI.

Использование:
    cd backend
    uv run python -m src.infrastructure.db.seed
"""
# ruff: noqa: T201
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.application.use_cases import (
    TemplateManagementUseCase,
    UserManagementUseCase,
)
from src.infrastructure.db.migrations import init_if_needed
from src.infrastructure.repos.template_repo_sqlite import SqliteTemplateRepository
from src.infrastructure.repos.user_repo_sqlite import SqliteUserRepository
from src.infrastructure.settings import get_settings


def _seed(db_path: str | None = None) -> None:
    # ruff: noqa: PLR0915
    settings = get_settings()
    db_path = db_path or settings.db_path_resolved

    init_if_needed(db_path)

    user_repo = SqliteUserRepository(db_path)
    template_repo = SqliteTemplateRepository(db_path)

    user_uc = UserManagementUseCase(user_repo)
    template_uc = TemplateManagementUseCase(template_repo)

    existing_users = user_repo.list_all()
    existing_templates = template_repo.list_all()

    if existing_users or existing_templates:
        print("Данные уже существуют, сид пропущен.")
        return

    user1 = user_uc.create("Анна", "#4A90D9")
    print(f"Создан пользователь: {user1.name} ({user1.color})")

    user2 = user_uc.create("Борис", "#D94A4A")
    print(f"Создан пользователь: {user2.name} ({user2.color})")

    _create_templates(template_uc, user1.id, user2.id)
    print("\nСид завершён. Создано 2 пользователя и 7 шаблонов задач.")
    print("Откройте /api/calendar?year=2026&month=6 для просмотра задач.")


def _create_templates(
    template_uc: TemplateManagementUseCase,
    uid1: int,
    uid2: int,
) -> None:
    templates_data: list[dict[str, object]] = [
        {
            "title": "Помыть посуду",
            "description": "Посудомоечная машина или вручную",
            "sp_cost": 2,
            "recurrence_type": "daily",
            "recurrence_params": {},
            "default_assignee_id": uid1,
        },
        {
            "title": "Вынести мусор",
            "description": None,
            "sp_cost": 1,
            "recurrence_type": "daily",
            "recurrence_params": {},
            "default_assignee_id": uid2,
        },
        {
            "title": "Протереть пыль",
            "description": "Все видимые поверхности",
            "sp_cost": 3,
            "recurrence_type": "weekly",
            "recurrence_params": {"weekday": 0},
            "default_assignee_id": uid1,
        },
        {
            "title": "Помыть пол",
            "description": "Кухня и ванная",
            "sp_cost": 4,
            "recurrence_type": "weekly",
            "recurrence_params": {"weekday": 3},
            "default_assignee_id": uid2,
        },
        {
            "title": "Купить продукты",
            "description": "Основной закуп",
            "sp_cost": 5,
            "recurrence_type": "every_n_days",
            "recurrence_params": {"interval_days": 3},
            "default_assignee_id": uid1,
        },
        {
            "title": "Покормить кота",
            "description": "Утро и вечер",
            "sp_cost": 1,
            "recurrence_type": "daily",
            "recurrence_params": {},
            "default_assignee_id": uid2,
        },
        {
            "title": "Убрать ванную",
            "description": "Глубокая уборка: кафель, раковина, унитаз",
            "sp_cost": 6,
            "recurrence_type": "every_n_days",
            "recurrence_params": {"interval_days": 7},
            "default_assignee_id": uid1,
        },
    ]

    for tpl_data in templates_data:
        tpl = template_uc.create(
            title=tpl_data["title"],  # type: ignore[arg-type]
            description=tpl_data["description"],  # type: ignore[arg-type]
            sp_cost=tpl_data["sp_cost"],  # type: ignore[arg-type]
            recurrence_type=tpl_data["recurrence_type"],  # type: ignore[arg-type]
            recurrence_params=tpl_data["recurrence_params"],  # type: ignore[arg-type]
            default_assignee_id=tpl_data["default_assignee_id"],  # type: ignore[arg-type]
        )
        print(f"Создан шаблон: {tpl.title} (SP: {tpl.sp_cost})")


def main() -> None:
    _seed(None)


if __name__ == "__main__":
    main()
