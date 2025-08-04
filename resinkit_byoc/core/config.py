import os

from pydantic import (
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict



_CURRENT_ENV = os.getenv("ENV", "dev")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.common", f".env.{_CURRENT_ENV}"),
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
    )

    ##### Environment #####
    @property
    @computed_field
    def IS_PRODUCTION(self) -> bool:
        return _CURRENT_ENV.lower() == "production"



_settings: Settings | None = None


def _get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

