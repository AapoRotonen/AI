from __future__ import annotations

import hashlib
import logging
import math
import re

import httpx

from newslens.config import Settings
from newslens.llm import OpenAICompatibleClient, ProviderUnavailableError

logger = logging.getLogger(__name__)


class HashEmbedding:
    """Stable lexical hashing fallback; it is not a substitute for semantic embeddings."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9+#]{2,}", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            vector[value % self.dimensions] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]


class EmbeddingService:
    def __init__(self, settings: Settings, llm: OpenAICompatibleClient) -> None:
        self.settings = settings
        self.llm = llm
        self.fallback = HashEmbedding(settings.embedding_dimensions)

    async def embed(self, text: str) -> tuple[list[float], str]:
        if self.llm.configured:
            try:
                mode = f"provider:{self.settings.openai_base_url.rstrip('/')}/{self.settings.openai_embedding_model}"
                return await self.llm.embed(text), mode[:128]
            except (
                ProviderUnavailableError,
                httpx.HTTPError,
                ValueError,
                KeyError,
                IndexError,
                TypeError,
            ) as exc:
                logger.warning(
                    "Embedding provider failed; using lexical fallback (%s)", type(exc).__name__
                )
        return await self.fallback.embed(text), "lexical-fallback"
