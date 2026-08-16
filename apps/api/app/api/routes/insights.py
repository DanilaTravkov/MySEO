from datetime import datetime
from decimal import Decimal
from statistics import median
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.analytics.service import latest_completed_run
from app.db.session import get_session
from app.models import (
    Cluster,
    ClusterKeyword,
    DiscoveryRun,
    Keyword,
    KeywordAnalysis,
    KeywordObservation,
    Opportunity,
)
from app.providers.registry import provider_registry

router = APIRouter(tags=["insights"])


class ProviderSummary(BaseModel):
    id: str
    name: str
    status: str


class LastRunSummary(BaseModel):
    id: UUID
    provider: str
    status: str
    completed_at: datetime | None


class DashboardResponse(BaseModel):
    total_discovered_keywords: int
    active_opportunities: int
    strong_opportunities: int
    median_search_volume: float | None
    median_growth: float | None
    last_discovery_run: LastRunSummary | None
    providers: list[ProviderSummary]


class KeywordResultRow(BaseModel):
    id: UUID
    keyword: str
    volume: int | None
    growth: float | None
    competition: float | None
    bid: float | None
    z_score: float | None
    tool_intent: float | None
    opportunity_score: float | None


class DiscoveryResultsResponse(BaseModel):
    run_id: UUID
    provider: str
    completed_at: datetime | None
    rows: list[KeywordResultRow]


class MonthlyVolumeResponse(BaseModel):
    year: int
    month: int
    searches: int


class KeywordDetailResponse(BaseModel):
    id: UUID
    keyword: str
    language: str
    geo: str
    provider: str
    current: int | None
    average: int | None
    growth: float | None
    trend: float | None
    volatility: float | None
    z_score: float | None
    robust_z_score: float | None
    percentile: float | None
    competition: float | None
    bid: float | None
    skewness: float | None
    monthly_volumes: list[MonthlyVolumeResponse]
    explanations: list[str]


class OpportunityCardResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    opportunity_score: float
    demand: float
    growth: float
    commercial: float
    competition: float
    tool_intent: float
    buildability: float
    stability: float
    recommendation: str
    analyze_available: bool = False


def _midpoint(low: Decimal | None, high: Decimal | None) -> float | None:
    values = [float(value) for value in (low, high) if value is not None]
    return sum(values) / len(values) if values else None


def _latest_run_or_404(session: Session, run_id: UUID | None) -> DiscoveryRun:
    run = session.get(DiscoveryRun, run_id) if run_id else latest_completed_run(session)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed discovery run is available.",
        )
    return run


def _opportunity_signals(
    session: Session,
    keyword_ids: list[UUID],
    run_id: UUID,
) -> dict[UUID, Opportunity]:
    if not keyword_ids:
        return {}
    rows = session.execute(
        select(ClusterKeyword.keyword_id, Opportunity)
        .join(Opportunity, Opportunity.cluster_id == ClusterKeyword.cluster_id)
        .join(Cluster, Cluster.id == ClusterKeyword.cluster_id)
        .where(ClusterKeyword.keyword_id.in_(keyword_ids))
        .where(Cluster.discovery_run_id == run_id)
        .order_by(Opportunity.opportunity_score.desc())
    ).all()
    signals: dict[UUID, Opportunity] = {}
    for keyword_id, opportunity in rows:
        signals.setdefault(keyword_id, opportunity)
    return signals


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(session: Annotated[Session, Depends(get_session)]) -> DashboardResponse:
    latest_run = latest_completed_run(session)
    total_keywords = session.scalar(select(func.count()).select_from(Keyword)) or 0
    active_opportunities = (
        session.scalar(
            select(func.count()).select_from(Opportunity).where(
                Opportunity.recommendation != "IGNORE"
            )
        )
        or 0
    )
    strong_opportunities = (
        session.scalar(
            select(func.count()).select_from(Opportunity).where(
                Opportunity.recommendation.in_(["STRONG", "BUILD"])
            )
        )
        or 0
    )

    volumes: list[float] = []
    growth_values: list[float] = []
    if latest_run is not None:
        volumes = [
            float(value)
            for value in session.scalars(
                select(KeywordObservation.avg_monthly_searches).where(
                    KeywordObservation.discovery_run_id == latest_run.id,
                    KeywordObservation.avg_monthly_searches.is_not(None),
                )
            ).all()
            if value is not None
        ]
        growth_values = [
            float(value)
            for value in session.scalars(
                select(KeywordAnalysis.growth_3m).where(
                    KeywordAnalysis.discovery_run_id == latest_run.id,
                    KeywordAnalysis.growth_3m.is_not(None),
                )
            ).all()
            if value is not None
        ]

    return DashboardResponse(
        total_discovered_keywords=total_keywords,
        active_opportunities=active_opportunities,
        strong_opportunities=strong_opportunities,
        median_search_volume=median(volumes) if volumes else None,
        median_growth=median(growth_values) if growth_values else None,
        last_discovery_run=(
            LastRunSummary(
                id=latest_run.id,
                provider=latest_run.provider,
                status=latest_run.status,
                completed_at=latest_run.completed_at,
            )
            if latest_run
            else None
        ),
        providers=[
            ProviderSummary(id=item.id, name=item.name, status=item.status)
            for item in provider_registry()
        ],
    )


@router.get("/discovery/results", response_model=DiscoveryResultsResponse)
def discovery_results(
    session: Annotated[Session, Depends(get_session)],
    run_id: Annotated[UUID | None, Query()] = None,
) -> DiscoveryResultsResponse:
    run = _latest_run_or_404(session, run_id)
    observations = session.scalars(
        select(KeywordObservation)
        .options(joinedload(KeywordObservation.keyword))
        .where(KeywordObservation.discovery_run_id == run.id)
        .order_by(KeywordObservation.avg_monthly_searches.desc())
    ).unique().all()
    analyses = {
        analysis.keyword_id: analysis
        for analysis in session.scalars(
            select(KeywordAnalysis).where(KeywordAnalysis.discovery_run_id == run.id)
        ).all()
    }
    opportunity_signals = _opportunity_signals(
        session,
        [observation.keyword_id for observation in observations],
        run.id,
    )

    rows: list[KeywordResultRow] = []
    for observation in observations:
        analysis = analyses.get(observation.keyword_id)
        opportunity = opportunity_signals.get(observation.keyword_id)
        rows.append(
            KeywordResultRow(
                id=observation.keyword_id,
                keyword=observation.keyword.display_text,
                volume=observation.avg_monthly_searches,
                growth=analysis.growth_3m if analysis else None,
                competition=(
                    float(observation.competition_index)
                    if observation.competition_index is not None
                    else None
                ),
                bid=_midpoint(observation.low_top_page_bid, observation.high_top_page_bid),
                z_score=analysis.z_score if analysis else None,
                tool_intent=opportunity.tool_intent_score if opportunity else None,
                opportunity_score=opportunity.opportunity_score if opportunity else None,
            )
        )
    return DiscoveryResultsResponse(
        run_id=run.id,
        provider=run.provider,
        completed_at=run.completed_at,
        rows=rows,
    )


def _analytics_explanations(analysis: KeywordAnalysis | None) -> list[str]:
    if analysis is None:
        return ["Statistical analysis is not available for this observation."]
    explanations: list[str] = []
    if analysis.z_score is None:
        explanations.append(
            "Classical Z-score is unavailable because the historical variance is zero "
            "or insufficient."
        )
    else:
        direction = "above" if analysis.z_score >= 0 else "below"
        explanations.append(
            f"Demand is {abs(analysis.z_score):.1f} standard deviations {direction} "
            "the historical mean."
        )
    if analysis.skewness is not None and abs(analysis.skewness) >= 1:
        if analysis.robust_z_score is not None:
            explanations.append(
                "The series is highly skewed, so robust Z-score is a more reliable outlier "
                "indicator for this keyword."
            )
        else:
            explanations.append(
                "The series is highly skewed, but robust Z-score is unavailable because "
                "MAD is zero."
            )
    elif analysis.robust_z_score is not None:
        explanations.append(
            "Classical and robust outlier indicators are both available for comparison."
        )
    if analysis.growth_3m is not None:
        direction = "increased" if analysis.growth_3m >= 0 else "decreased"
        explanations.append(
            f"The latest three-month average {direction} by "
            f"{abs(analysis.growth_3m) * 100:.1f}% versus the previous window."
        )
    return explanations


@router.get("/keywords/{keyword_id}", response_model=KeywordDetailResponse)
def keyword_detail(
    keyword_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> KeywordDetailResponse:
    keyword = session.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found.")
    observation = session.scalar(
        select(KeywordObservation)
        .options(selectinload(KeywordObservation.monthly_volumes))
        .where(KeywordObservation.keyword_id == keyword_id)
        .order_by(KeywordObservation.observed_at.desc())
        .limit(1)
    )
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword has no observations.",
        )
    analysis = session.scalar(
        select(KeywordAnalysis)
        .where(
            KeywordAnalysis.keyword_id == keyword_id,
            KeywordAnalysis.discovery_run_id == observation.discovery_run_id,
        )
        .order_by(KeywordAnalysis.calculated_at.desc())
        .limit(1)
    )
    monthly = sorted(observation.monthly_volumes, key=lambda item: (item.year, item.month))
    return KeywordDetailResponse(
        id=keyword.id,
        keyword=keyword.display_text,
        language=keyword.language,
        geo=keyword.geo,
        provider=observation.provider,
        current=monthly[-1].searches if monthly else None,
        average=observation.avg_monthly_searches,
        growth=analysis.growth_3m if analysis else None,
        trend=analysis.normalized_slope if analysis else None,
        volatility=analysis.volatility if analysis else None,
        z_score=analysis.z_score if analysis else None,
        robust_z_score=analysis.robust_z_score if analysis else None,
        percentile=analysis.historical_percentile if analysis else None,
        competition=(
            float(observation.competition_index)
            if observation.competition_index is not None
            else None
        ),
        bid=_midpoint(observation.low_top_page_bid, observation.high_top_page_bid),
        skewness=analysis.skewness if analysis else None,
        monthly_volumes=[
            MonthlyVolumeResponse(year=item.year, month=item.month, searches=item.searches)
            for item in monthly
        ],
        explanations=_analytics_explanations(analysis),
    )


@router.get("/opportunities", response_model=list[OpportunityCardResponse])
def opportunities(
    session: Annotated[Session, Depends(get_session)],
) -> list[OpportunityCardResponse]:
    rows = session.execute(
        select(Opportunity, Cluster)
        .join(Cluster, Cluster.id == Opportunity.cluster_id)
        .order_by(Opportunity.opportunity_score.desc())
    ).all()
    return [
        OpportunityCardResponse(
            id=opportunity.id,
            title=cluster.name,
            description=cluster.description,
            opportunity_score=opportunity.opportunity_score,
            demand=opportunity.demand_score,
            growth=opportunity.growth_score,
            commercial=opportunity.commercial_score,
            competition=opportunity.competition_score,
            tool_intent=opportunity.tool_intent_score,
            buildability=opportunity.buildability_score,
            stability=opportunity.stability_score,
            recommendation=opportunity.recommendation,
        )
        for opportunity, cluster in rows
    ]
