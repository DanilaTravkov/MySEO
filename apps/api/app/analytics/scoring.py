import math
from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class OpportunityComponents:
    demand: float
    growth: float
    commercial_value: float
    low_competition: float
    tool_intent: float
    buildability: float
    stability: float

    def __post_init__(self) -> None:
        for name, value in self.values().items():
            if not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError(f"{name} must be a finite score between 0 and 100.")

    def values(self) -> dict[str, float]:
        return {
            "demand": self.demand,
            "growth": self.growth,
            "commercial_value": self.commercial_value,
            "low_competition": self.low_competition,
            "tool_intent": self.tool_intent,
            "buildability": self.buildability,
            "stability": self.stability,
        }


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    demand: float = 0.20
    growth: float = 0.15
    commercial_value: float = 0.15
    low_competition: float = 0.15
    tool_intent: float = 0.15
    buildability: float = 0.15
    stability: float = 0.05

    def __post_init__(self) -> None:
        values = self.values().values()
        if any(value < 0 for value in values):
            raise ValueError("Scoring weights must be non-negative.")
        if not math.isclose(sum(self.values().values()), 1.0, abs_tol=1e-9):
            raise ValueError("Scoring weights must sum to 1.0.")

    def values(self) -> dict[str, float]:
        return {
            "demand": self.demand,
            "growth": self.growth,
            "commercial_value": self.commercial_value,
            "low_competition": self.low_competition,
            "tool_intent": self.tool_intent,
            "buildability": self.buildability,
            "stability": self.stability,
        }


@dataclass(frozen=True, slots=True)
class RecommendationThresholds:
    watch: float = 40
    investigate: float = 60
    strong: float = 75
    build: float = 85

    def __post_init__(self) -> None:
        values = (self.watch, self.investigate, self.strong, self.build)
        if not 0 <= values[0] < values[1] < values[2] < values[3] <= 100:
            raise ValueError("Recommendation thresholds must be ordered within 0..100.")


def configured_weights() -> ScoringWeights:
    settings = get_settings()
    return ScoringWeights(
        demand=settings.score_weight_demand,
        growth=settings.score_weight_growth,
        commercial_value=settings.score_weight_commercial,
        low_competition=settings.score_weight_low_competition,
        tool_intent=settings.score_weight_tool_intent,
        buildability=settings.score_weight_buildability,
        stability=settings.score_weight_stability,
    )


def configured_thresholds() -> RecommendationThresholds:
    settings = get_settings()
    return RecommendationThresholds(
        watch=settings.recommendation_watch_min,
        investigate=settings.recommendation_investigate_min,
        strong=settings.recommendation_strong_min,
        build=settings.recommendation_build_min,
    )


def opportunity_score(
    components: OpportunityComponents,
    weights: ScoringWeights | None = None,
) -> float:
    selected = weights or configured_weights()
    score = sum(
        components.values()[field] * weight for field, weight in selected.values().items()
    )
    return round(min(100.0, max(0.0, score)), 2)


def recommendation(
    score: float,
    thresholds: RecommendationThresholds | None = None,
) -> str:
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError("Opportunity score must be a finite value between 0 and 100.")
    selected = thresholds or configured_thresholds()
    if score >= selected.build:
        return "BUILD"
    if score >= selected.strong:
        return "STRONG"
    if score >= selected.investigate:
        return "INVESTIGATE"
    if score >= selected.watch:
        return "WATCH"
    return "IGNORE"
