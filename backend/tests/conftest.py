from collections.abc import Generator
from pathlib import Path

import pytest

from src.infrastructure.db.migrations import init_if_needed
from src.infrastructure.settings import Settings, reset_settings, set_settings


@pytest.fixture
def db_path(tmp_path: Path) -> Generator[str, None, None]:
    """Возвращает путь к временной БД на диске."""
    path = str(tmp_path / "test.db")
    s = Settings(DB_PATH=path)
    set_settings(s)
    init_if_needed(path)
    yield path
    reset_settings()
