from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Config(BaseSettings):
    API_V1_PREFIX: str = "/v1"

    # PostGIS settings
    DB_HOST: str
    DB_PORT: int  # 5432
    DB_USER: str
    DB_PASSWORD: str

    DB_NAME: str  # postgres
    DB_PREFIX: str  # "postgresql+asyncpg"

    DB_URL: str | None = None

    @model_validator(mode="before")
    @classmethod
    def form_db_url(cls, values: dict) -> dict:
        """Form the DB URL from the settings"""
        if "DB_URL" not in values:
            values["DB_URL"] = (
                "{prefix}://{user}:{password}@{host}:{port}/{db}".format(
                    prefix=values.get("DB_PREFIX"),
                    user=values.get("DB_USER"),
                    password=values.get("DB_PASSWORD"),
                    host=values.get("DB_HOST"),
                    port=values.get("DB_PORT"),
                    db=values.get("DB_NAME"),
                )
            )
        return values


@lru_cache()
def get_config():
    return Config()


config = get_config()
