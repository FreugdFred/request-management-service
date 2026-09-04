from typing import Literal

from pydantic import AnyUrl, NatsDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Request-Management-Service-API"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    API_KEY: str | None = None
    LOCAL_TIMEZONE: str = "Europe/Amsterdam"

    DATABASE_URL: AnyUrl
    NATS_URL: NatsDsn | None = None

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )
