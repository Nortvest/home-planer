"""Опциональный маунт статики фронта.

Активируется только при SERVE_FRONTEND=1.
Бэк не знает конкретных имён HTML-файлов — просто отдаёт каталог как статику.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.infrastructure.settings import get_settings


def maybe_mount_static(app: FastAPI) -> None:
    settings = get_settings()
    if not settings.SERVE_FRONTEND:
        return

    app.mount("/", StaticFiles(directory=settings.frontend_dir_resolved, html=True))
