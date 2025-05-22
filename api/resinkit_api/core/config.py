import os
from typing import Union

from pydantic import (
    BaseModel,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from resinkit_api.core.find_root import find_project_root


_CURRENT_ENV = os.getenv("ENV", "dev")


class DeepSubModel(BaseModel):
    v4: str = "default_v4"


class SubModel(BaseModel):
    v1: str = "default_v1"
    v2: bytes = b"default_v2"
    v3: int = 0
    deep: DeepSubModel = DeepSubModel()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.common", f".env.{_CURRENT_ENV}"),
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
    )
    sub_model: SubModel = SubModel()

    ##### Environment #####
    @computed_field
    @property
    def IS_BYOC(self) -> bool:
        return _CURRENT_ENV.lower() == "byoc"

    ##### Logging #####
    LOG_LEVEL: str = "INFO"
    LOG_JSON_FORMAT: bool = False

    ##### Flink #####
    FLINK_HOME: str = "/usr/local/flink"
    FLINK_CDC_HOME: str = "/usr/local/flink-cdc"
    FLINK_JOB_MANAGER_URL: str = "http://localhost:8081"
    FLINK_SQL_GATEWAY_URL: str = "http://localhost:8083"

    ##### Resinkit #####
    X_RESINKIT_PAT: str | None = None

    @computed_field
    @property
    def FLINK_LIB_DIR(self) -> str:
        return f"{self.FLINK_HOME}/lib"

    ##### Database #####
    DB_PATH: str = "_data_/sqlite.db"
    SQLALCHEMY_ECHO: Union[bool, str] = True

    VARIABLE_ENCRYPTION_KEY: str = "resinkit-default-encryption-key-0519"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        # Get the absolute path for the database
        project_root = find_project_root()
        db_path = project_root / self.DB_PATH
        return f"sqlite:///{db_path}"


settings = Settings()
