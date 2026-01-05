"""Configuration management using environment variables."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _load_dotenv() -> None:
    """Load .env file if it exists (simple implementation)."""
    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str
    tavily_api_key: str

    # Model configuration
    model_name: str = Field(default="gpt-4o")

    # Research settings
    max_tavily_results: int = Field(default=10)

    # Reflection loop settings
    max_reflection_iterations: int = Field(default=3)
    approval_threshold: int = Field(default=7)  # Score 1-10 for auto-approval

    # Planner settings
    max_plan_attempts: int = Field(default=3)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="console")  # "console" or "json"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings from environment.

    Returns:
        Settings instance loaded from environment
    """
    _load_dotenv()

    return Settings(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        tavily_api_key=os.environ["TAVILY_API_KEY"],
        model_name=os.environ.get("MODEL_NAME", "gpt-4o"),
        max_tavily_results=int(os.environ.get("MAX_TAVILY_RESULTS", "10")),
        max_reflection_iterations=int(os.environ.get("MAX_REFLECTION_ITERATIONS", "3")),
        approval_threshold=int(os.environ.get("APPROVAL_THRESHOLD", "7")),
        max_plan_attempts=int(os.environ.get("MAX_PLAN_ATTEMPTS", "3")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        log_format=os.environ.get("LOG_FORMAT", "console"),
    )
