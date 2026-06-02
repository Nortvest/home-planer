"""Централизованные настройки через pydantic-settings.

Читает .env и переменные окружения.
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_PATH: str | None = Field(
        default=None,
        description="Путь к SQLite-файлу. По умолчанию <корень>/data/planner.db",
    )
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000
    TZ: str = ""
    SERVE_FRONTEND: bool = False
    FRONTEND_DIR: str = ""
    CORS_ALLOW_ORIGINS: str = "*"
    DB_TIMEOUT: int = 30
    DB_BUSY_TIMEOUT: int = 5000

    model_config = {"env_prefix": ""}

    @property
    def db_path_resolved(self) -> str:
        if self.DB_PATH:
            return self.DB_PATH

        root = Path(__file__).resolve().parents[3]
        return str(root / "data" / "planner.db")

    @property
    def frontend_dir_resolved(self) -> str:
        if self.FRONTEND_DIR:
            return self.FRONTEND_DIR

        root = Path(__file__).resolve().parents[3]
        return str(root / "frontend")

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ALLOW_ORIGINS == "*":
            return ["*"]
        return [o for o in self.CORS_ALLOW_ORIGINS.split(",") if o]


class _SettingsHolder:
    instance: Settings | None = None


def get_settings() -> Settings:
    if _SettingsHolder.instance is None:
        _SettingsHolder.instance = Settings()
    return _SettingsHolder.instance


def set_settings(s: Settings) -> None:
    _SettingsHolder.instance = s


def reset_settings() -> None:
    _SettingsHolder.instance = None
