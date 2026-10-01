from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def new_id() -> str:
    return str(uuid4())


class StoryRecord(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    geography: Mapped[str] = mapped_column(String(32), default="GLOBAL")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    articles: Mapped[list[ArticleRecord]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )


class ArticleRecord(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_articles_canonical_url"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_story_id", "story_id"),
        Index(
            "ix_articles_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    snippet: Mapped[str] = mapped_column(String(2000), default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    geography: Mapped[str] = mapped_column(String(32), default="GLOBAL")
    embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(1536).with_variant(JSON(), "sqlite"), nullable=True
    )
    embedding_mode: Mapped[str] = mapped_column(String(128), default="unknown", nullable=False)
    story_id: Mapped[str] = mapped_column(
        ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
    )
    story: Mapped[StoryRecord] = relationship(back_populates="articles")
