from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOSTNAME: str = ""  # set by docker
    RUN_ID: str = ""
    DB_FILEPATH: str = "sqlite.db"
    PROMETHEUS_BASE_URL: str = "http://localhost:9090"


@lru_cache
def get_settings():
    return Settings()
