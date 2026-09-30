"""
core/config.py - Sovelluksen asetukset
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    tavily_api_key: str = os.environ.get("TAVILY_API_KEY", "")
    model_name: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.0
    chroma_persist_dir: str = "./chroma_db"
    retrieval_top_k: int = 4
    max_iterations: int = 3
    cors_allowed_origins: str = "http://127.0.0.1:5500,http://localhost:5500"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
