from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import CreatedAtMixin, UuidPrimaryKeyMixin, utc_now

_WHITESPACE = re.compile(r"\s+")


def normalize_keyword(value: str) -> str:
    """Create a stable comparison key while preserving display text separately."""
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return _WHITESPACE.sub(" ", normalized)


class Keyword(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint(
            "normalized_text",
            "language",
            "geo",
            name="uq_keywords_normalized_language_geo",
        ),
        Index("ix_keywords_display_text", "display_text"),
    )

    normalized_text: Mapped[str] = mapped_column(String(512), nullable=False)
    display_text: Mapped[str] = mapped_column(String(512), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    geo: Mapped[str] = mapped_column(String(16), nullable=False)

    observations: Mapped[list[KeywordObservation]] = relationship(
        back_populates="keyword",
        cascade="all, delete-orphan",
        order_by="KeywordObservation.observed_at",
    )
    analyses: Mapped[list[KeywordAnalysis]] = relationship(
        back_populates="keyword",
        cascade="all, delete-orphan",
        order_by="KeywordAnalysis.calculated_at",
    )
    cluster_links: Mapped[list[ClusterKeyword]] = relationship(
        back_populates="keyword",
        cascade="all, delete-orphan",
    )


class KeywordObservation(UuidPrimaryKeyMixin, Base):
    __tablename__ = "keyword_observations"
    __table_args__ = (
        CheckConstraint(
            "avg_monthly_searches IS NULL OR avg_monthly_searches >= 0",
            name="ck_keyword_observations_avg_searches_nonnegative",
        ),
        CheckConstraint(
            "competition_index IS NULL OR "
            "(competition_index >= 0 AND competition_index <= 100)",
            name="ck_keyword_observations_competition_index_range",
        ),
        CheckConstraint(
            "low_top_page_bid IS NULL OR low_top_page_bid >= 0",
            name="ck_keyword_observations_low_bid_nonnegative",
        ),
        CheckConstraint(
            "high_top_page_bid IS NULL OR high_top_page_bid >= 0",
            name="ck_keyword_observations_high_bid_nonnegative",
        ),
        CheckConstraint(
            "low_top_page_bid IS NULL OR high_top_page_bid IS NULL OR "
            "high_top_page_bid >= low_top_page_bid",
            name="ck_keyword_observations_bid_order",
        ),
        Index("ix_keyword_observations_keyword_observed", "keyword_id", "observed_at"),
    )

    keyword_id: Mapped[UUID] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
    )
    discovery_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="SET NULL"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    avg_monthly_searches: Mapped[int | None] = mapped_column(Integer)
    competition: Mapped[str | None] = mapped_column(String(32))
    competition_index: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    low_top_page_bid: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    high_top_page_bid: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    keyword: Mapped[Keyword] = relationship(back_populates="observations")
    discovery_run: Mapped[DiscoveryRun | None] = relationship(
        back_populates="keyword_observations"
    )
    monthly_volumes: Mapped[list[MonthlySearchVolume]] = relationship(
        back_populates="keyword_observation",
        cascade="all, delete-orphan",
        order_by="MonthlySearchVolume.year, MonthlySearchVolume.month",
    )


class MonthlySearchVolume(UuidPrimaryKeyMixin, Base):
    __tablename__ = "monthly_search_volumes"
    __table_args__ = (
        UniqueConstraint(
            "keyword_observation_id",
            "year",
            "month",
            name="uq_monthly_volumes_observation_period",
        ),
        CheckConstraint("year >= 2000 AND year <= 2200", name="ck_monthly_volumes_year"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_monthly_volumes_month"),
        CheckConstraint("searches >= 0", name="ck_monthly_volumes_searches_nonnegative"),
    )

    keyword_observation_id: Mapped[UUID] = mapped_column(
        ForeignKey("keyword_observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    searches: Mapped[int] = mapped_column(Integer, nullable=False)

    keyword_observation: Mapped[KeywordObservation] = relationship(
        back_populates="monthly_volumes"
    )


class KeywordAnalysis(Base):
    __tablename__ = "keyword_analyses"
    __table_args__ = (
        CheckConstraint(
            "demand_score IS NULL OR (demand_score >= 0 AND demand_score <= 100)",
            name="ck_keyword_analyses_demand_score",
        ),
        CheckConstraint(
            "growth_score IS NULL OR (growth_score >= 0 AND growth_score <= 100)",
            name="ck_keyword_analyses_growth_score",
        ),
        CheckConstraint(
            "commercial_score IS NULL OR (commercial_score >= 0 AND commercial_score <= 100)",
            name="ck_keyword_analyses_commercial_score",
        ),
        CheckConstraint(
            "competition_score IS NULL OR (competition_score >= 0 AND competition_score <= 100)",
            name="ck_keyword_analyses_competition_score",
        ),
        CheckConstraint(
            "stability_score IS NULL OR (stability_score >= 0 AND stability_score <= 100)",
            name="ck_keyword_analyses_stability_score",
        ),
        CheckConstraint(
            "historical_percentile IS NULL OR "
            "(historical_percentile >= 0 AND historical_percentile <= 100)",
            name="ck_keyword_analyses_historical_percentile",
        ),
        CheckConstraint(
            "normality_p_value IS NULL OR "
            "(normality_p_value >= 0 AND normality_p_value <= 1)",
            name="ck_keyword_analyses_normality_p_value",
        ),
        CheckConstraint(
            "volatility IS NULL OR volatility >= 0",
            name="ck_keyword_analyses_volatility_nonnegative",
        ),
        Index("ix_keyword_analyses_calculated_at", "calculated_at"),
    )

    keyword_id: Mapped[UUID] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"),
        primary_key=True,
    )
    analysis_version: Mapped[str] = mapped_column(String(32), primary_key=True)
    discovery_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="SET NULL"),
        index=True,
    )
    growth_3m: Mapped[float | None] = mapped_column(Float)
    growth_6m: Mapped[float | None] = mapped_column(Float)
    normalized_slope: Mapped[float | None] = mapped_column(Float)
    volatility: Mapped[float | None] = mapped_column(Float)
    z_score: Mapped[float | None] = mapped_column(Float)
    robust_z_score: Mapped[float | None] = mapped_column(Float)
    historical_percentile: Mapped[float | None] = mapped_column(Float)
    skewness: Mapped[float | None] = mapped_column(Float)
    kurtosis: Mapped[float | None] = mapped_column(Float)
    normality_p_value: Mapped[float | None] = mapped_column(Float)
    demand_score: Mapped[float | None] = mapped_column(Float)
    growth_score: Mapped[float | None] = mapped_column(Float)
    commercial_score: Mapped[float | None] = mapped_column(Float)
    competition_score: Mapped[float | None] = mapped_column(Float)
    stability_score: Mapped[float | None] = mapped_column(Float)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    keyword: Mapped[Keyword] = relationship(back_populates="analyses")
    discovery_run: Mapped[DiscoveryRun | None] = relationship(back_populates="keyword_analyses")


from app.models.discovery import DiscoveryRun  # noqa: E402
from app.models.opportunity import ClusterKeyword  # noqa: E402
