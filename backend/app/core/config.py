"""Application configuration for OmniPharma backend.

Loads settings from environment variables and the optional `.env` file
using Pydantic's BaseSettings. All modules that need configuration must
import `get_settings()` from here rather than reading `os.environ`
directly, so the settings object is testable and injectable.

Imports/dependencies: pydantic-settings, os.

Public outputs: `Settings`, `get_settings()`.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration resolved from environment variables.

    Attributes:
        app_env: Runtime environment name (development | staging | production).
        database_url: SQLAlchemy connection string for the main patient DB.
        ppb_database_url: SQLAlchemy connection string for the PPB catalogue DB.
        llm_provider: Optional LLM provider identifier (e.g. ``openai``).
            ``None`` means the LLM layer is disabled and all calls to
            ``PharmacistAgent.explain()`` return ``None``.
        llm_api_key: API key for the chosen LLM provider.  Not required when
            ``llm_provider`` is ``None``.
        openfda_api_key: Optional API key for openFDA evidence lookups.
        log_level: Python ``logging`` level string (DEBUG | INFO | WARNING | ERROR).
        cors_allowed_origins: Comma-separated list of allowed CORS origins;
            parsed into a list by the property below.
        ruleset_version: Version tag embedded in every ``ScreeningResponse``
            so callers know which rule tables were in effect.
        inventory_aware: When ``True``, ``RecommendationService`` excludes
            out-of-stock candidates with reason ``OUT_OF_STOCK``; when
            ``False``, stock status is informational only.
        evidence_timeout_seconds: Per-source HTTP timeout for evidence retrieval.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "sqlite:///./data/omnipharm.db"
    ppb_database_url: str = "sqlite:///./data/ppb_drugs.db"
    llm_provider: str | None = None
    llm_api_key: str | None = None
    openfda_api_key: str | None = None
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    ruleset_version: str = "demo-1.0"
    inventory_aware: bool = False
    evidence_timeout_seconds: float = 5.0

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list, split on commas.

        Returns:
            A list of origin strings parsed from ``cors_allowed_origins``.
        """
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call).

    Returns:
        The application :class:`Settings` object, loaded once and cached
        for the lifetime of the process.
    """
    return Settings()
