from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel

from newslens.config import Settings
from newslens.security.providers import validate_provider_base_url


class ProviderUnavailableError(RuntimeError):
    """Raised when an optional hosted model provider is not configured."""


class OpenAICompatibleClient:
    """Small OpenAI-compatible chat/embeddings client, configured by base URL."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = validate_provider_base_url(settings.openai_base_url)

    @property
    def configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    async def chat_json(self, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        if not self.configured:
            raise ProviderUnavailableError("OPENAI_API_KEY is not configured")
        json_schema = schema.model_json_schema()
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__.lower()[:64],
                "description": f"Return a value matching the {schema.__name__} schema.",
                "strict": False,
                "schema": json_schema,
            },
        }
        async with httpx.AsyncClient(timeout=45) as client:
            request = {
                "model": self.settings.openai_chat_model,
                "response_format": response_format,
                "messages": [
                    {
                        "role": "system",
                        "content": f"{system}\nReturn JSON matching this schema: {json.dumps(json_schema)}",
                    },
                    {"role": "user", "content": user},
                ],
            }
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json=request,
            )
            if response.status_code == 400:
                # Many OpenAI-compatible endpoints implement JSON mode but not JSON Schema mode.
                request["response_format"] = {"type": "json_object"}
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json=request,
                )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return schema.model_validate_json(content)

    async def embed(self, text: str) -> list[float]:
        if not self.configured:
            raise ProviderUnavailableError("OPENAI_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.openai_embedding_model,
                    "input": text[:8000],
                    "dimensions": self.settings.embedding_dimensions,
                },
            )
            response.raise_for_status()
        vector: list[float] = response.json()["data"][0]["embedding"]
        if len(vector) != self.settings.embedding_dimensions:
            raise ValueError("Embedding provider returned an unexpected vector dimension")
        return vector


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
