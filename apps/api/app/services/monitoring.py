from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Cluster,
    DiscoveryRun,
    KeywordObservation,
    MonitorSignal,
    Opportunity,
    SearchMonitor,
    Workspace,
)
from app.providers.mock import MOCK_DATASET_SIZE, MockSearchDataProvider
from app.services.discovery import DiscoveryResult, run_discovery


class MonitorProviderUnavailable(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ClaimedMonitor:
    monitor_id: UUID
    scheduled_for: datetime


def add_one_month(value: datetime) -> datetime:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def local_workspace(session: Session) -> Workspace:
    workspace = session.scalar(select(Workspace).where(Workspace.name == "Local workspace"))
    if workspace is None:
        workspace = Workspace(name="Local workspace")
        session.add(workspace)
        session.flush()
    return workspace


def create_monitor(
    session: Session,
    *,
    name: str,
    provider: str,
    seeds: list[str],
    language: str,
    geo: str,
    frequency: str,
    enabled: bool,
    limit: int = MOCK_DATASET_SIZE,
) -> SearchMonitor:
    if provider != "mock":
        raise MonitorProviderUnavailable(
            "This source cannot refresh automatically yet. Use the mock source for the "
            "monitoring demo or configure a live provider first."
        )
    clean_seeds = list(dict.fromkeys(seed.strip() for seed in seeds if seed.strip()))
    if not clean_seeds:
        raise ValueError("At least one non-empty seed is required.")
    now = datetime.now(UTC)
    monitor = SearchMonitor(
        workspace=local_workspace(session),
        name=name.strip(),
        provider=provider,
        language=language,
        geo=geo,
        seeds_json=clean_seeds,
        config_json={"limit": limit},
        frequency=frequency,
        enabled=enabled,
        next_run_at=add_one_month(now) if enabled and frequency == "monthly" else None,
    )
    session.add(monitor)
    session.commit()
    return monitor


def _severity(magnitude: float) -> str:
    absolute = abs(magnitude)
    if absolute >= 0.5:
        return "high"
    if absolute >= 0.25:
        return "medium"
    return "low"


def _observation_map(
    session: Session,
    run_id: UUID,
) -> dict[str, KeywordObservation]:
    observations = session.scalars(
        select(KeywordObservation)
        .where(KeywordObservation.discovery_run_id == run_id)
        .options(joinedload(KeywordObservation.keyword))
    ).unique()
    return {item.keyword.normalized_text: item for item in observations}


def _competition(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def detect_monitor_signals(
    session: Session,
    monitor: SearchMonitor,
    previous_run: DiscoveryRun,
    current_run: DiscoveryRun,
) -> int:
    session.execute(delete(MonitorSignal).where(MonitorSignal.current_run_id == current_run.id))
    previous = _observation_map(session, previous_run.id)
    current = _observation_map(session, current_run.id)
    signals: list[MonitorSignal] = []

    new_items = sorted(
        (item for key, item in current.items() if key not in previous),
        key=lambda item: item.avg_monthly_searches or 0,
        reverse=True,
    )[:25]
    for item in new_items:
        volume = item.avg_monthly_searches or 0
        signals.append(
            MonitorSignal(
                monitor=monitor,
                previous_run_id=previous_run.id,
                current_run_id=current_run.id,
                signal_type="new_keyword",
                severity="medium" if volume >= 10_000 else "low",
                entity_key=item.keyword.normalized_text,
                title=item.keyword.display_text,
                summary=f"New query with approximately {volume:,} monthly searches.",
                magnitude=float(volume),
                details_json={"current_volume": volume},
            )
        )

    for key in current.keys() & previous.keys():
        before = previous[key]
        after = current[key]
        before_volume = before.avg_monthly_searches
        after_volume = after.avg_monthly_searches
        if before_volume is not None and after_volume is not None:
            change = (after_volume - before_volume) / max(before_volume, 1)
            if abs(change) >= 0.20 and abs(after_volume - before_volume) >= 100:
                growing = change > 0
                signals.append(
                    MonitorSignal(
                        monitor=monitor,
                        previous_run_id=previous_run.id,
                        current_run_id=current_run.id,
                        signal_type="demand_growth" if growing else "demand_decline",
                        severity=_severity(change),
                        entity_key=key,
                        title=after.keyword.display_text,
                        summary=(
                            f"Monthly demand {'increased' if growing else 'declined'} "
                            f"by {abs(change):.0%}."
                        ),
                        magnitude=change,
                        details_json={
                            "previous_volume": before_volume,
                            "current_volume": after_volume,
                        },
                    )
                )

        before_competition = _competition(before.competition_index)
        after_competition = _competition(after.competition_index)
        if before_competition is not None and after_competition is not None:
            delta = after_competition - before_competition
            if abs(delta) >= 10:
                signals.append(
                    MonitorSignal(
                        monitor=monitor,
                        previous_run_id=previous_run.id,
                        current_run_id=current_run.id,
                        signal_type="competition_shift",
                        severity="high" if abs(delta) >= 25 else "medium",
                        entity_key=key,
                        title=after.keyword.display_text,
                        summary=f"Competition index changed by {delta:+.0f} points.",
                        magnitude=delta,
                        details_json={
                            "previous_competition": before_competition,
                            "current_competition": after_competition,
                        },
                    )
                )

    previous_clusters = {
        cluster.name.casefold(): cluster
        for cluster in session.scalars(
            select(Cluster).where(Cluster.discovery_run_id == previous_run.id)
        )
    }
    current_clusters = {
        cluster.name.casefold(): cluster
        for cluster in session.scalars(
            select(Cluster).where(Cluster.discovery_run_id == current_run.id)
        )
    }
    for key in current_clusters.keys() - previous_clusters.keys():
        cluster = current_clusters[key]
        signals.append(
            MonitorSignal(
                monitor=monitor,
                previous_run_id=previous_run.id,
                current_run_id=current_run.id,
                signal_type="new_cluster",
                severity="medium" if cluster.keyword_count >= 5 else "low",
                entity_key=key,
                title=cluster.name,
                summary=f"New search-intent cluster containing {cluster.keyword_count} keywords.",
                magnitude=float(cluster.keyword_count),
                details_json={"keyword_count": cluster.keyword_count},
            )
        )

    def opportunity_scores(run_id: UUID) -> dict[str, float]:
        rows = session.execute(
            select(Cluster.name, Opportunity.opportunity_score)
            .join(Opportunity, Opportunity.cluster_id == Cluster.id)
            .where(Cluster.discovery_run_id == run_id)
        )
        return {name.casefold(): score for name, score in rows}

    previous_scores = opportunity_scores(previous_run.id)
    current_scores = opportunity_scores(current_run.id)
    for key in current_scores.keys() & previous_scores.keys():
        delta = current_scores[key] - previous_scores[key]
        if abs(delta) >= 10:
            opportunity_cluster = current_clusters.get(key)
            signals.append(
                MonitorSignal(
                    monitor=monitor,
                    previous_run_id=previous_run.id,
                    current_run_id=current_run.id,
                    signal_type="opportunity_shift",
                    severity="high" if abs(delta) >= 20 else "medium",
                    entity_key=key,
                    title=opportunity_cluster.name if opportunity_cluster else key,
                    summary=f"Opportunity score changed by {delta:+.0f} points.",
                    magnitude=delta,
                    details_json={
                        "previous_score": previous_scores[key],
                        "current_score": current_scores[key],
                    },
                )
            )

    session.add_all(signals)
    session.flush()
    return len(signals)


async def run_monitor(
    session: Session,
    monitor_id: UUID,
    *,
    trigger: str = "manual",
    scheduled_for: datetime | None = None,
) -> DiscoveryResult:
    monitor = session.get(SearchMonitor, monitor_id)
    if monitor is None:
        raise LookupError("Monitor not found.")
    if monitor.provider != "mock":
        raise MonitorProviderUnavailable("The selected provider is not configured for refreshes.")

    previous_run = session.scalar(
        select(DiscoveryRun)
        .where(
            DiscoveryRun.monitor_id == monitor.id,
            DiscoveryRun.status == "completed",
        )
        .order_by(DiscoveryRun.completed_at.desc())
        .limit(1)
    )
    result = await run_discovery(
        session,
        MockSearchDataProvider(),
        provider_id=monitor.provider,
        seeds=list(monitor.seeds_json),
        language=monitor.language,
        geo=monitor.geo,
        limit=int(monitor.config_json.get("limit", MOCK_DATASET_SIZE)),
        config={"monitor_name": monitor.name},
        workspace=monitor.workspace,
        monitor_id=monitor.id,
        trigger=trigger,
        scheduled_for=scheduled_for,
    )
    current_run = session.get(DiscoveryRun, result.run_id)
    assert current_run is not None
    if previous_run is not None:
        detect_monitor_signals(session, monitor, previous_run, current_run)
    monitor.last_run_at = current_run.completed_at
    now = datetime.now(UTC)
    if monitor.enabled and monitor.frequency == "monthly" and (
        monitor.next_run_at is None or as_utc(monitor.next_run_at) <= now
    ):
        monitor.next_run_at = add_one_month(now)
    session.commit()
    return result


def claim_due_monitors(
    session: Session,
    *,
    now: datetime | None = None,
    limit: int = 25,
) -> list[ClaimedMonitor]:
    current_time = now or datetime.now(UTC)
    due = session.scalars(
        select(SearchMonitor)
        .where(
            SearchMonitor.enabled.is_(True),
            SearchMonitor.frequency == "monthly",
            SearchMonitor.next_run_at.is_not(None),
            SearchMonitor.next_run_at <= current_time,
        )
        .order_by(SearchMonitor.next_run_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    ).all()
    claimed: list[ClaimedMonitor] = []
    for monitor in due:
        assert monitor.next_run_at is not None
        scheduled_for = monitor.next_run_at
        monitor.next_run_at = add_one_month(scheduled_for)
        claimed.append(ClaimedMonitor(monitor.id, scheduled_for))
    session.commit()
    return claimed
