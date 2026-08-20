from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import CreatedAtMixin, UuidPrimaryKeyMixin, utc_now


class SearchMonitor(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "search_monitors"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('manual', 'monthly')",
            name="ck_search_monitors_frequency",
        ),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    geo: Mapped[str] = mapped_column(String(16), nullable=False)
    seeds_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="search_monitors")
    discovery_runs: Mapped[list[DiscoveryRun]] = relationship(
        back_populates="monitor",
        order_by="DiscoveryRun.started_at.desc()",
    )
    signals: Mapped[list[MonitorSignal]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        order_by="MonitorSignal.created_at.desc()",
    )


class MonitorSignal(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "monitor_signals"
    __table_args__ = (
        CheckConstraint(
            "signal_type IN ('new_keyword', 'demand_growth', 'demand_decline', "
            "'competition_shift', 'new_cluster', 'opportunity_shift')",
            name="ck_monitor_signals_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_monitor_signals_severity",
        ),
    )

    monitor_id: Mapped[UUID] = mapped_column(
        ForeignKey("search_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        index=True,
    )
    current_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    magnitude: Mapped[float | None] = mapped_column(Float)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    monitor: Mapped[SearchMonitor] = relationship(back_populates="signals")
    previous_run: Mapped[DiscoveryRun | None] = relationship(
        foreign_keys=[previous_run_id],
    )
    current_run: Mapped[DiscoveryRun] = relationship(foreign_keys=[current_run_id])


from app.models.discovery import DiscoveryRun, Workspace  # noqa: E402
