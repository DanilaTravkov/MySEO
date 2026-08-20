from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.service import analyze_discovery_run
from app.clustering.service import cluster_discovery_run
from app.core.config import get_settings
from app.models import (
    DiscoveryRun,
    Keyword,
    KeywordObservation,
    MonthlySearchVolume,
    Seed,
    Workspace,
)
from app.models.keyword import normalize_keyword
from app.providers.base import SearchDataProvider


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    run_id: UUID
    provider: str
    status: str
    keyword_count: int
    observation_count: int
    monthly_volume_count: int
    cluster_count: int
    sample_keywords: tuple[str, ...]


async def run_discovery(
    session: Session,
    provider: SearchDataProvider,
    *,
    provider_id: str,
    seeds: list[str],
    language: str,
    geo: str,
    limit: int,
    config: dict[str, Any] | None = None,
    workspace: Workspace | None = None,
    monitor_id: UUID | None = None,
    trigger: str = "manual",
    scheduled_for: datetime | None = None,
) -> DiscoveryResult:
    workspace = workspace or session.scalar(
        select(Workspace).where(Workspace.name == "Local workspace")
    )
    if workspace is None:
        workspace = Workspace(name="Local workspace")
        session.add(workspace)
        session.flush()

    clean_seeds = list(dict.fromkeys(seed.strip() for seed in seeds if seed.strip()))
    run = DiscoveryRun(
        workspace=workspace,
        monitor_id=monitor_id,
        provider=provider_id,
        status="running",
        trigger=trigger,
        scheduled_for=scheduled_for,
        language=language,
        geo=geo,
        started_at=datetime.now(UTC),
        config_json={"limit": limit, **(config or {})},
        seeds=[Seed(text=seed) for seed in clean_seeds],
    )
    session.add(run)
    session.commit()
    run_id = run.id

    try:
        ideas = await provider.discover_keywords(clean_seeds, language, geo, limit)
        unique_ideas = {
            normalize_keyword(idea.text): idea
            for idea in ideas
            if normalize_keyword(idea.text)
        }
        metrics = await provider.historical_metrics(
            [idea.text for idea in unique_ideas.values()],
            language,
            geo,
        )
        metrics_by_keyword = {normalize_keyword(item.keyword): item for item in metrics}

        normalized_keys = list(metrics_by_keyword)
        existing_keywords = session.scalars(
            select(Keyword).where(
                Keyword.language == language,
                Keyword.geo == geo,
                Keyword.normalized_text.in_(normalized_keys),
            )
        ).all()
        keywords_by_key = {keyword.normalized_text: keyword for keyword in existing_keywords}

        for normalized in normalized_keys:
            if normalized not in keywords_by_key:
                item = metrics_by_keyword[normalized]
                keyword = Keyword(
                    normalized_text=normalized,
                    display_text=item.keyword,
                    language=language,
                    geo=geo,
                )
                session.add(keyword)
                keywords_by_key[normalized] = keyword
        session.flush()

        monthly_volume_count = 0
        for normalized, item in metrics_by_keyword.items():
            observation = KeywordObservation(
                keyword=keywords_by_key[normalized],
                discovery_run_id=run_id,
                provider=provider_id,
                avg_monthly_searches=item.avg_monthly_searches,
                competition=item.competition,
                competition_index=item.competition_index,
                low_top_page_bid=item.low_top_page_bid,
                high_top_page_bid=item.high_top_page_bid,
                currency=item.currency,
                raw_json=dict(item.raw_data),
                monthly_volumes=[
                    MonthlySearchVolume(
                        year=monthly.year,
                        month=monthly.month,
                        searches=monthly.searches,
                    )
                    for monthly in item.monthly_volumes
                ],
            )
            monthly_volume_count += len(item.monthly_volumes)
            session.add(observation)

        session.flush()
        analyze_discovery_run(session, run_id)
        clustering = cluster_discovery_run(
            session,
            run_id,
            similarity_threshold=get_settings().clustering_similarity_threshold,
        )
        persisted_run = session.get(DiscoveryRun, run_id)
        assert persisted_run is not None
        persisted_run.status = "completed"
        persisted_run.completed_at = datetime.now(UTC)
        persisted_run.error = None
        session.commit()
    except Exception as error:
        session.rollback()
        failed_run = session.get(DiscoveryRun, run_id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.completed_at = datetime.now(UTC)
            failed_run.error = str(error)[:4000]
            session.commit()
        raise

    return DiscoveryResult(
        run_id=run_id,
        provider=provider_id,
        status="completed",
        keyword_count=len(metrics_by_keyword),
        observation_count=len(metrics_by_keyword),
        monthly_volume_count=monthly_volume_count,
        cluster_count=clustering.cluster_count,
        sample_keywords=tuple(item.keyword for item in metrics[:10]),
    )
