from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://devs@localhost:5432/borderwt"

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    bwt_url: str = "https://bwt.cbp.gov/xml/bwt.xml"
    bwt_fetch_timeout_seconds: int = 30
    bwt_fetch_max_attempts: int = 3

    cors_allow_origins: list[str] = [
        "http://localhost:5183",
        "http://127.0.0.1:5183",
    ]

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
