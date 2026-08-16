import math
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import InstrumentedAttribute, Session, selectinload

from app.analytics.distribution import DistributionResult, analyze_distribution
from app.analytics.metrics import KeywordStatistics, calculate_keyword_statistics
from app.analytics.normalization import percentile_rank
from app.models import (
    ClusterKeyword,
    DiscoveryRun,
    KeywordAnalysis,
    KeywordObservation,
    Opportunity,
)

ANALYSIS_VERSION = "analytics-v1"

METRIC_LABELS = {
    "avg_monthly_searches": "Average monthly searches",
    "log_avg_monthly_searches": "Log average monthly searches",
    "growth": "Growth (3 month)",
    "cpc": "CPC / bid",
    "competition": "Competition",
    "opportunity_score": "Opportunity score",
    "tool_intent": "Tool intent",
    "buildability": "Buildability",
}


@dataclass(frozen=True, slots=True)
class _AnalysisCandidate:
    observation: KeywordObservation
    statistics: KeywordStatistics
    commercial_signal: float | None


def _commercial_signal(observation: KeywordObservation) -> float | None:
    bids = [
        float(value)
        for value in (observation.low_top_page_bid, observation.high_top_page_bid)
        if value is not None
    ]
    if not bids:
        return None
    return math.log1p(sum(bids) / len(bids))


def analyze_discovery_run(session: Session, run_id: UUID) -> int:
    run = session.get(DiscoveryRun, run_id)
    if run is None:
        raise LookupError(f"Discovery run {run_id} was not found.")

    observations = session.scalars(
        select(KeywordObservation)
        .options(selectinload(KeywordObservation.monthly_volumes))
        .where(KeywordObservation.discovery_run_id == run_id)
        .order_by(KeywordObservation.keyword_id)
    ).all()
    candidates: list[_AnalysisCandidate] = []
    for observation in observations:
        monthly = sorted(
            observation.monthly_volumes,
            key=lambda item: (item.year, item.month),
        )
        if not monthly:
            continue
        statistics = calculate_keyword_statistics([item.searches for item in monthly])
        candidates.append(
            _AnalysisCandidate(
                observation=observation,
                statistics=statistics,
                commercial_signal=_commercial_signal(observation),
            )
        )

    demand_scores = percentile_rank(
        [
            math.log1p(candidate.observation.avg_monthly_searches)
            if candidate.observation.avg_monthly_searches is not None
            else None
            for candidate in candidates
        ]
    )
    growth_scores = percentile_rank(
        [candidate.statistics.growth_3m for candidate in candidates]
    )
    commercial_scores = percentile_rank(
        [candidate.commercial_signal for candidate in candidates]
    )
    competition_scores = percentile_rank(
        [
            float(candidate.observation.competition_index)
            if candidate.observation.competition_index is not None
            else None
            for candidate in candidates
        ],
        higher_is_better=False,
    )
    stability_scores = percentile_rank(
        [candidate.statistics.volatility for candidate in candidates],
        higher_is_better=False,
    )

    analysis_version = f"{ANALYSIS_VERSION}-{run_id.hex[:12]}"
    existing_analyses = {
        (analysis.keyword_id, analysis.analysis_version): analysis
        for analysis in session.scalars(
            select(KeywordAnalysis).where(
                KeywordAnalysis.discovery_run_id == run_id,
                KeywordAnalysis.analysis_version == analysis_version,
            )
        ).all()
    }
    for index, candidate in enumerate(candidates):
        key = (candidate.observation.keyword_id, analysis_version)
        analysis = existing_analyses.get(key)
        if analysis is None:
            analysis = KeywordAnalysis(
                keyword_id=candidate.observation.keyword_id,
                analysis_version=analysis_version,
            )
            session.add(analysis)
        statistics = candidate.statistics
        analysis.discovery_run_id = run_id
        analysis.growth_3m = statistics.growth_3m
        analysis.growth_6m = statistics.growth_6m
        analysis.normalized_slope = statistics.normalized_slope
        analysis.volatility = statistics.volatility
        analysis.z_score = statistics.z_score
        analysis.robust_z_score = statistics.robust_z_score
        analysis.historical_percentile = statistics.historical_percentile
        analysis.skewness = statistics.skewness
        analysis.kurtosis = statistics.kurtosis
        analysis.normality_p_value = statistics.normality_p_value
        analysis.demand_score = demand_scores[index]
        analysis.growth_score = growth_scores[index]
        analysis.commercial_score = commercial_scores[index]
        analysis.competition_score = competition_scores[index]
        analysis.stability_score = stability_scores[index]

    session.flush()
    return len(candidates)


def latest_completed_run(session: Session) -> DiscoveryRun | None:
    return session.scalar(
        select(DiscoveryRun)
        .where(DiscoveryRun.status == "completed")
        .order_by(DiscoveryRun.completed_at.desc())
        .limit(1)
    )


def _opportunity_query(
    run_id: UUID,
    column: InstrumentedAttribute[float],
) -> Select[tuple[float]]:
    return (
        select(column)
        .join(ClusterKeyword, ClusterKeyword.cluster_id == Opportunity.cluster_id)
        .join(KeywordObservation, KeywordObservation.keyword_id == ClusterKeyword.keyword_id)
        .where(KeywordObservation.discovery_run_id == run_id)
        .distinct()
    )


def distribution_for_run(
    session: Session,
    metric: str,
    run_id: UUID | None = None,
) -> tuple[UUID, DistributionResult]:
    if metric not in METRIC_LABELS:
        raise ValueError(f"Unsupported distribution metric: {metric}.")
    run = session.get(DiscoveryRun, run_id) if run_id else latest_completed_run(session)
    if run is None:
        raise LookupError("No completed discovery run is available.")

    values: list[float]
    if metric in {"avg_monthly_searches", "log_avg_monthly_searches", "cpc", "competition"}:
        observations = session.scalars(
            select(KeywordObservation).where(KeywordObservation.discovery_run_id == run.id)
        ).all()
        if metric == "avg_monthly_searches":
            values = [
                float(item.avg_monthly_searches)
                for item in observations
                if item.avg_monthly_searches is not None
            ]
        elif metric == "log_avg_monthly_searches":
            values = [
                math.log1p(item.avg_monthly_searches)
                for item in observations
                if item.avg_monthly_searches is not None
            ]
        elif metric == "competition":
            values = [
                float(item.competition_index)
                for item in observations
                if item.competition_index is not None
            ]
        else:
            values = [
                signal
                for item in observations
                if (signal := _commercial_signal(item)) is not None
            ]
    elif metric == "growth":
        values = [
            float(value)
            for value in session.scalars(
                select(KeywordAnalysis.growth_3m).where(
                    KeywordAnalysis.discovery_run_id == run.id,
                    KeywordAnalysis.growth_3m.is_not(None),
                )
            ).all()
            if value is not None
        ]
    else:
        column_by_metric = {
            "opportunity_score": Opportunity.opportunity_score,
            "tool_intent": Opportunity.tool_intent_score,
            "buildability": Opportunity.buildability_score,
        }
        values = [
            float(value)
            for value in session.scalars(
                _opportunity_query(run.id, column_by_metric[metric])
            ).all()
        ]

    return run.id, analyze_distribution(values, metric=metric, label=METRIC_LABELS[metric])
