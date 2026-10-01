"""Initial NewsLens stories, articles, and vector index."""

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "stories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("geography", sa.String(length=32), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "articles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snippet", sa.String(length=2000), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("geography", sa.String(length=32), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.VECTOR(dim=1536), nullable=True),
        sa.Column("embedding_mode", sa.String(length=128), nullable=False),
        sa.Column(
            "story_id",
            sa.String(length=36),
            sa.ForeignKey("stories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("canonical_url", name="uq_articles_canonical_url"),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_story_id", "articles", ["story_id"])
    op.create_index(
        "ix_articles_embedding_hnsw",
        "articles",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_articles_embedding_hnsw", table_name="articles")
    op.drop_index("ix_articles_story_id", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_table("articles")
    op.drop_table("stories")
