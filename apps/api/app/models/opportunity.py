from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import CreatedAtMixin, UuidPrimaryKeyMixin


class Cluster(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "clusters"
    __table_args__ = (
        CheckConstraint("keyword_count >= 0", name="ck_clusters_keyword_count"),
        CheckConstraint("total_volume >= 0", name="ck_clusters_total_volume"),
        CheckConstraint(
            "similarity_threshold >= 0 AND similarity_threshold <= 1",
            name="ck_clusters_similarity_threshold",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    discovery_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        index=True,
    )
    algorithm_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="tfidf-agglomerative-v1"
    )
    similarity_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.15)
    total_volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    median_volume: Mapped[float | None] = mapped_column(Float)
    weighted_growth: Mapped[float | None] = mapped_column(Float)
    median_competition: Mapped[float | None] = mapped_column(Float)
    median_bid: Mapped[float | None] = mapped_column(Float)
    keyword_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    discovery_run: Mapped[DiscoveryRun | None] = relationship(back_populates="clusters")

    keyword_links: Mapped[list[ClusterKeyword]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
    )


class ClusterKeyword(Base):
    __tablename__ = "cluster_keywords"
    __table_args__ = (
        CheckConstraint(
            "similarity IS NULL OR (similarity >= 0 AND similarity <= 1)",
            name="ck_cluster_keywords_similarity",
        ),
    )

    cluster_id: Mapped[UUID] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    keyword_id: Mapped[UUID] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"),
        primary_key=True,
    )
    similarity: Mapped[float | None] = mapped_column(Float)

    cluster: Mapped[Cluster] = relationship(back_populates="keyword_links")
    keyword: Mapped[Keyword] = relationship(back_populates="cluster_links")


class Opportunity(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("cluster_id", "score_version", name="uq_opportunities_cluster_version"),
        CheckConstraint(
            "recommendation IN ('IGNORE', 'WATCH', 'INVESTIGATE', 'STRONG', 'BUILD')",
            name="ck_opportunities_recommendation",
        ),
        CheckConstraint(
            "demand_score >= 0 AND demand_score <= 100",
            name="ck_opportunities_demand_score",
        ),
        CheckConstraint(
            "growth_score >= 0 AND growth_score <= 100",
            name="ck_opportunities_growth_score",
        ),
        CheckConstraint(
            "commercial_score >= 0 AND commercial_score <= 100",
            name="ck_opportunities_commercial_score",
        ),
        CheckConstraint(
            "competition_score >= 0 AND competition_score <= 100",
            name="ck_opportunities_competition_score",
        ),
        CheckConstraint(
            "tool_intent_score >= 0 AND tool_intent_score <= 100",
            name="ck_opportunities_tool_intent_score",
        ),
        CheckConstraint(
            "buildability_score >= 0 AND buildability_score <= 100",
            name="ck_opportunities_buildability_score",
        ),
        CheckConstraint(
            "stability_score >= 0 AND stability_score <= 100",
            name="ck_opportunities_stability_score",
        ),
        CheckConstraint(
            "opportunity_score >= 0 AND opportunity_score <= 100",
            name="ck_opportunities_opportunity_score",
        ),
    )

    cluster_id: Mapped[UUID] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    growth_score: Mapped[float] = mapped_column(Float, nullable=False)
    commercial_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    tool_intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    buildability_score: Mapped[float] = mapped_column(Float, nullable=False)
    stability_score: Mapped[float] = mapped_column(Float, nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    score_version: Mapped[str] = mapped_column(String(32), nullable=False)

    cluster: Mapped[Cluster] = relationship(back_populates="opportunities")
    product_hypotheses: Mapped[list[ProductHypothesis]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )


class ProductHypothesis(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "product_hypotheses"
    __table_args__ = (
        CheckConstraint(
            "estimated_complexity IN ('low', 'medium', 'high')",
            name="ck_product_hypotheses_complexity",
        ),
    )

    opportunity_id: Mapped[UUID] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    target_user: Mapped[str] = mapped_column(Text, nullable=False)
    input_description: Mapped[str] = mapped_column(Text, nullable=False)
    output_description: Mapped[str] = mapped_column(Text, nullable=False)
    features_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    monetization_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    risks_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    estimated_complexity: Mapped[str] = mapped_column(String(16), nullable=False)
    build_brief_markdown: Mapped[str | None] = mapped_column(Text)
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    llm_model: Mapped[str | None] = mapped_column(String(128))

    opportunity: Mapped[Opportunity] = relationship(back_populates="product_hypotheses")


from app.models.discovery import DiscoveryRun  # noqa: E402
from app.models.keyword import Keyword  # noqa: E402
