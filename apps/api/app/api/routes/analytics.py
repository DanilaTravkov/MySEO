from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.analytics.scoring import configured_thresholds, configured_weights
from app.analytics.service import analyze_discovery_run, distribution_for_run
from app.db.session import get_session

router = APIRouter(tags=["analytics"])
DistributionMetric = Literal[
    "avg_monthly_searches",
    "log_avg_monthly_searches",
    "growth",
    "cpc",
    "competition",
    "opportunity_score",
    "tool_intent",
    "buildability",
]


class AnalysisRunResponse(BaseModel):
    run_id: UUID
    analysis_count: int
    analysis_version: str = "analytics-v1"


class HistogramBinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start: float
    end: float
    count: int
    normal_fit: float | None


class QQPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theoretical: float
    observed: float


class DiagnosticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mean: float | None
    median: float | None
    std: float | None
    mad: float | None
    skewness: float | None
    kurtosis: float | None
    shapiro_wilk_p_value: float | None
    sample_size: int
    summary: str


class DistributionResponse(BaseModel):
    run_id: UUID
    metric: str
    label: str
    normal_fit_label: str = "Normal fit"
    histogram: list[HistogramBinResponse]
    qq_points: list[QQPointResponse]
    diagnostics: DiagnosticsResponse
    insufficient_sample: bool


class ScoringConfigurationResponse(BaseModel):
    weights: dict[str, float]
    thresholds: dict[str, float]


@router.post("/analytics/runs/{run_id}", response_model=AnalysisRunResponse)
def recalculate_run(
    run_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisRunResponse:
    try:
        count = analyze_discovery_run(session, run_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    session.commit()
    return AnalysisRunResponse(run_id=run_id, analysis_count=count)


@router.get("/analytics/scoring-config", response_model=ScoringConfigurationResponse)
def scoring_configuration() -> ScoringConfigurationResponse:
    weights = configured_weights()
    thresholds = configured_thresholds()
    return ScoringConfigurationResponse(
        weights={
            "demand": weights.demand,
            "growth": weights.growth,
            "commercial_value": weights.commercial_value,
            "low_competition": weights.low_competition,
            "tool_intent": weights.tool_intent,
            "buildability": weights.buildability,
            "stability": weights.stability,
        },
        thresholds={
            "watch": thresholds.watch,
            "investigate": thresholds.investigate,
            "strong": thresholds.strong,
            "build": thresholds.build,
        },
    )


@router.get("/distributions", response_model=DistributionResponse)
def distribution(
    session: Annotated[Session, Depends(get_session)],
    metric: Annotated[DistributionMetric, Query()] = "avg_monthly_searches",
    run_id: Annotated[UUID | None, Query()] = None,
) -> DistributionResponse:
    try:
        selected_run_id, result = distribution_for_run(session, metric, run_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return DistributionResponse(
        run_id=selected_run_id,
        metric=result.metric,
        label=result.label,
        histogram=[HistogramBinResponse.model_validate(item) for item in result.histogram],
        qq_points=[QQPointResponse.model_validate(item) for item in result.qq_points],
        diagnostics=DiagnosticsResponse.model_validate(result.diagnostics),
        insufficient_sample=result.insufficient_sample,
    )
