"""Environment-based application configuration with production guardrails."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_environment: Literal["local", "production"] = "local"
    database_backend: Literal["sqlite", "cosmos"] = "sqlite"
    openai_api_key: str = ""
    tavily_api_key: str = ""
    model_name: str = "gpt-6-luna"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.0
    chroma_persist_dir: str = "./chroma_db"
    rag_index_blob_url: str = ""
    azure_client_id: str = ""
    cosmos_endpoint: str = ""
    cosmos_database_name: str = "koivu"
    retrieval_top_k: int = 4
    max_iterations: int = 3
    cors_allowed_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    database_path: str = "./koivu.sqlite3"
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    support_agent_api_key: str = ""
    catalog_setup_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    public_app_url: str = ""
    provider_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_production_configuration(self):
        payment_values = (self.stripe_secret_key.strip(), self.stripe_webhook_secret.strip(), self.public_app_url.strip())
        if any(payment_values) and not all(payment_values):
            raise ValueError("Stripe test checkout requires STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, and PUBLIC_APP_URL")
        if self.stripe_secret_key and not self.stripe_secret_key.startswith("sk_test_"):
            raise ValueError("Only a Stripe test-mode secret key is accepted")
        if self.stripe_webhook_secret and not self.stripe_webhook_secret.startswith("whsec_"):
            raise ValueError("STRIPE_WEBHOOK_SECRET must be a Stripe webhook endpoint secret")
        if self.public_app_url:
            parsed_app_url = urlsplit(self.public_app_url)
            if (
                parsed_app_url.scheme not in {"http", "https"}
                or not parsed_app_url.netloc
                or parsed_app_url.username
                or parsed_app_url.password
                or parsed_app_url.path not in {"", "/"}
                or parsed_app_url.query
                or parsed_app_url.fragment
            ):
                raise ValueError("PUBLIC_APP_URL must be an absolute HTTP(S) origin without query or fragment")
        if self.app_environment == "production":
            required = {
                "OPENAI_API_KEY": self.openai_api_key,
                "COSMOS_ENDPOINT": self.cosmos_endpoint,
                "RAG_INDEX_BLOB_URL": self.rag_index_blob_url,
                "SUPPORT_AGENT_API_KEY": self.support_agent_api_key,
            }
            missing = [name for name, value in required.items() if not value.strip()]
            if missing:
                raise ValueError("Production configuration is missing: " + ", ".join(missing))
            if self.database_backend != "cosmos":
                raise ValueError("DATABASE_BACKEND must be 'cosmos' in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
            if not self.cosmos_endpoint.startswith("https://"):
                raise ValueError("COSMOS_ENDPOINT must use HTTPS")
            if not self.rag_index_blob_url.startswith("https://") or "?" in self.rag_index_blob_url:
                raise ValueError("RAG_INDEX_BLOB_URL must be a private HTTPS blob URL without a SAS query")
            if "*" in self.cors_allowed_origins:
                raise ValueError("CORS_ALLOWED_ORIGINS cannot contain a wildcard")
            if len(self.support_agent_api_key) < 32:
                raise ValueError("SUPPORT_AGENT_API_KEY must contain at least 32 characters in production")
            if self.public_app_url and not self.public_app_url.startswith("https://"):
                raise ValueError("PUBLIC_APP_URL must use HTTPS in production")
        if self.provider_timeout_seconds <= 0:
            raise ValueError("PROVIDER_TIMEOUT_SECONDS must be positive")
        return self

    @property
    def stripe_test_checkout_enabled(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_webhook_secret and self.public_app_url)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
