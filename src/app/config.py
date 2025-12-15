from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    site_name: str = "Резюме Михаила Соловьева"
    site_tagline: str = "робототехника, дроны и автоматизация"
    admin_token: str = Field(
        default="change-me",
        description="Токен для доступа к админским маршрутам (заголовок X-Admin-Token).",
    )
    database_url: str | None = None
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Field(
        default=Path(__file__).resolve().parents[2] / "data",
        description="Директория с пользовательскими данными и медиа.",
    )
    trusted_hosts: str | List[str] = Field(default="*", description="Доверенные хосты или список через запятую.")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            raw = str(self.database_url)
            # если схема не указана, трактуем как путь до sqlite-файла
            if "://" not in raw:
                path = Path(raw)
                if not path.is_absolute():
                    path = self.data_dir / path
                return f"sqlite:///{path}"
            return raw
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.data_dir / 'app.db'}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
