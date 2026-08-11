"""Application settings, loaded from the environment or a .env file."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Every configurable value in the application.

    Values come from environment variables, falling back to a local `.env`
    file. See `.env.example` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- application -------------------------------------------------------
    PROJECT_NAME: str = "Prisoner's Dilemma Strategy Tournament API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = True

    # --- database ----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+psycopg://pd_user:pd_password@localhost:5432/prisoners_dilemma"
    )
    DATABASE_ECHO: bool = False

    # --- security ----------------------------------------------------------
    SECRET_KEY: str = Field(
        default="change-me-in-production-this-is-not-a-secret",
        description="Signing key for JWTs. Must be overridden outside development.",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # --- CORS --------------------------------------------------------------
    # NoDecode keeps pydantic-settings from trying to JSON-parse the raw
    # environment value, so the validator below can accept a plain
    # comma-separated list as well as a JSON array.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- simulation limits -------------------------------------------------
    MAX_ROUNDS_PER_MATCH: int = 10_000
    MAX_TOURNAMENT_REPETITIONS: int = 1_000

    # --- first admin created by the seed script ----------------------------
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "admin12345"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string as well as a JSON array.

        `CORS_ORIGINS=http://localhost:5173,http://localhost:3000` is the more
        natural thing to write in a .env file than a JSON array, so both are
        supported.
        """
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                import json

                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Settings singleton. Cached so the .env file is read once."""
    return Settings()


settings = get_settings()
