from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://newslens:newslens@localhost:5432/newslens"
    discord_bot_token: str | None = None
    discord_brief_channel_id: int | None = None
    discord_allowed_user_ids: str = ""
    discord_allow_public_commands: bool = False
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # The initial PostgreSQL migration uses vector(1536); keep provider dimensions aligned.
    embedding_dimensions: int = Field(default=1536, ge=1536, le=1536)
    tavily_api_key: str | None = None
    interests_file: Path = Path("config/interests.yaml")
    feeds_file: Path = Path("config/feeds.yaml")
    primary_domains_file: Path = Path("config/primary_domains.yaml")
    news_lookback_hours: int = Field(default=36, ge=1, le=720)
    brief_interval_minutes: int = Field(default=360, ge=5, le=10080)
    max_search_results: int = Field(default=5, ge=1, le=10)
    max_article_bytes: int = Field(default=1_000_000, ge=10_000, le=5_000_000)
    log_level: str = "INFO"


class InterestProfile(BaseModel):
    interests: list[str]
    high_priority: list[str]
    geographies: list[str] = Field(default_factory=lambda: ["GLOBAL"])


class FeedConfig(BaseModel):
    name: str
    url: str
    source_type: str = "UNKNOWN"
    geography: str = "GLOBAL"


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(content, dict):
        raise ValueError(f"Expected a YAML object in {path}")
    return content


def load_interests(path: Path) -> InterestProfile:
    return InterestProfile.model_validate(_load_yaml(path))


def load_feeds(path: Path) -> list[FeedConfig]:
    data = _load_yaml(path)
    return [FeedConfig.model_validate(item) for item in data.get("feeds", [])]


def load_primary_domains(path: Path) -> set[str]:
    domains = _load_yaml(path).get("domains", [])
    return {str(domain).lower().lstrip(".") for domain in domains}


def load_independent_domains(path: Path) -> set[str]:
    domains = _load_yaml(path).get("independent_reporting", [])
    return {str(domain).lower().lstrip(".") for domain in domains}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
