from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import CreatedAtMixin, UuidPrimaryKeyMixin


class Workspace(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    discovery_runs: Mapped[list[DiscoveryRun]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    search_monitors: Mapped[list[SearchMonitor]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class DiscoveryRun(UuidPrimaryKeyMixin, Base):
    __tablename__ = "discovery_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_discovery_runs_status",
        ),
        CheckConstraint(
            "trigger IN ('manual', 'scheduled')",
            name="ck_discovery_runs_trigger",
        ),
        UniqueConstraint(
            "monitor_id",
            "scheduled_for",
            name="uq_discovery_runs_monitor_scheduled_for",
        ),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monitor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("search_monitors.id", ondelete="SET NULL"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    trigger: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    geo: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

    workspace: Mapped[Workspace] = relationship(back_populates="discovery_runs")
    monitor: Mapped[SearchMonitor | None] = relationship(back_populates="discovery_runs")
    seeds: Mapped[list[Seed]] = relationship(
        back_populates="discovery_run",
        cascade="all, delete-orphan",
        order_by="Seed.id",
    )
    keyword_observations: Mapped[list[KeywordObservation]] = relationship(
        back_populates="discovery_run",
    )
    keyword_analyses: Mapped[list[KeywordAnalysis]] = relationship(
        back_populates="discovery_run",
    )
    clusters: Mapped[list[Cluster]] = relationship(
        back_populates="discovery_run",
        cascade="all, delete-orphan",
    )


class Seed(UuidPrimaryKeyMixin, Base):
    __tablename__ = "seeds"
    __table_args__ = (
        UniqueConstraint("discovery_run_id", "text", name="uq_seeds_run_text"),
    )

    discovery_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(512), nullable=False)

    discovery_run: Mapped[DiscoveryRun] = relationship(back_populates="seeds")


from app.models.keyword import KeywordAnalysis, KeywordObservation  # noqa: E402
from app.models.monitor import SearchMonitor  # noqa: E402
from app.models.opportunity import Cluster  # noqa: E402
