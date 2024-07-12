from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Any
import sys


class Config(BaseSettings):
    # API settings
    API_V1_PREFIX: str = "/v1"

    # Geographic settings
    SRID: int = 2056  # To use for x,y coords in CH | CH1903+ / LV95
    CONVEX_HULL_BUFFER: float = 1.0  # Buffer distance for convex hulls

    # Image settings
    IMAGE_MAX_SIZE: int = 1000  # Maximum pixel size for images on either x/y

    # Instrument settings
    INSTRUMENT_PLOT_DOWNSAMPLE_THRESHOLD: int = 50

    # PostGIS settings
    DB_HOST: str | None = None
    DB_PORT: int | None = None  # 5432
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None

    DB_NAME: str | None = None  # postgres
    DB_PREFIX: str = "postgresql+asyncpg"

    DB_URL: str | None = None

    @model_validator(mode="after")
    @classmethod
    def form_db_url(cls, values: dict) -> dict:
        """Form the DB URL from the settings"""
        if not values.DB_URL:
            values.DB_URL = (
                "{prefix}://{user}:{password}@{host}:{port}/{db}".format(
                    prefix=values.DB_PREFIX,
                    user=values.DB_USER,
                    password=values.DB_PASSWORD,
                    host=values.DB_HOST,
                    port=values.DB_PORT,
                    db=values.DB_NAME,
                )
            )
        return values

    @model_validator(mode="before")
    def dummy_variables_for_testing(cls, values: dict) -> dict:
        """Add some dummy variables for testing the model validator"""
        if "pytest" in sys.modules:
            return {
                "DB_URL": "sqlite+aiosqlite:///",
            }
        return values


@lru_cache()
def get_config():
    return Config()


config = get_config()
