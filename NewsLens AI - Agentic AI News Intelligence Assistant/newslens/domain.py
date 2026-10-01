from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class SourceType(StrEnum):
    PRIMARY = "PRIMARY"
    INDEPENDENT_REPORTING = "INDEPENDENT_REPORTING"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class ArticleCandidate(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    url: AnyHttpUrl
    source_name: str = Field(min_length=1, max_length=200)
    source_type: SourceType = SourceType.UNKNOWN
    published_at: datetime | None = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    snippet: str = Field(default="", max_length=2000)
    author: str | None = Field(default=None, max_length=200)
    geography: str = "GLOBAL"

    @field_validator("published_at", "discovered_at")
    @classmethod
    def ensure_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class RelevanceAssessment(BaseModel):
    relevant: bool
    score: float = Field(ge=0, le=1)
    topics: list[str] = Field(default_factory=list, max_length=8)
    geography: str = "GLOBAL"
    priority: str = "NORMAL"
    rationale: str = Field(default="", max_length=500)


class EvidenceItem(BaseModel):
    evidence_id: str
    title: str
    url: AnyHttpUrl
    publisher: str
    source_type: SourceType = SourceType.UNKNOWN
    excerpt: str = Field(default="", max_length=900)
    published_at: datetime | None = None


class EvidenceSynthesis(BaseModel):
    summary: str
    supported_claims: list[dict[str, str]] = Field(default_factory=list)
    uncertain: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    why_it_matters: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(UTC)
