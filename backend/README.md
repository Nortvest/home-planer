# Backend

FastAPI + SQLite, чистая архитектура.

## Структура

```
backend/src/
├── domain/          — сущности, перечисления, доменные сервисы, исключения
├── application/     — use-кейсы, DTO, порты (абстрактные репозитории)
├── infrastructure/  — SQLite-репозитории, подключение, миграции, часы
└── presentation/    — FastAPI-роутеры, pydantic-схемы, DI
```

## Требования

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

## Установка

```bash
uv sync --extra dev
```

## Запуск (dev)

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер доступен по `http://localhost:8000`, API — по `http://localhost:8000/api`.

## Переменные окружения

Создайте `.env` рядом с `pyproject.toml`:

```ini
DB_PATH=../data/planner.db
HOST=0.0.0.0
PORT=8000
TZ=Europe/Moscow
```

## Линтинг и тесты

```bash
uv run ruff check
uv run mypy src/
uv run pytest
```

## Миграции

Схема создаётся автоматически при первом запуске. Для ручной миграции:

```python
from src.infrastructure.db.migrations import run_migrations
run_migrations("path/to/planner.db")
```

## Docker

### Сборка образа

```bash
docker build -t planner-backend .
```

### Запуск

```bash
docker run -p 8000:8000 -v "$(pwd)/../data:/app/data" \
  -e DB_PATH=/app/data/planner.db \
  -e TZ=Europe/Moscow \
  planner-backend
```

### Логи и shell

```bash
docker logs <container-name>
docker exec -it <container-name> /bin/sh
```
