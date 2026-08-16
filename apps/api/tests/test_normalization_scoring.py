import pytest

from app.analytics.normalization import percentile_rank
from app.analytics.scoring import (
    OpportunityComponents,
    RecommendationThresholds,
    ScoringWeights,
    opportunity_score,
    recommendation,
)


def test_percentile_rank_handles_ties_missing_values_and_direction() -> None:
    values = [10.0, 20.0, 20.0, 30.0, None]

    assert percentile_rank(values) == [0.0, 50.0, 50.0, 100.0, None]
    assert percentile_rank(values, higher_is_better=False) == [100.0, 50.0, 50.0, 0.0, None]
    assert percentile_rank([42.0]) == [50.0]


def test_initial_opportunity_score_uses_configurable_weights() -> None:
    components = OpportunityComponents(
        demand=100,
        growth=80,
        commercial_value=60,
        low_competition=40,
        tool_intent=90,
        buildability=70,
        stability=50,
    )

    assert opportunity_score(components) == 73.5
    demand_only = ScoringWeights(
        demand=1,
        growth=0,
        commercial_value=0,
        low_competition=0,
        tool_intent=0,
        buildability=0,
        stability=0,
    )
    assert opportunity_score(components, demand_only) == 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "IGNORE"),
        (39.99, "IGNORE"),
        (40, "WATCH"),
        (60, "INVESTIGATE"),
        (75, "STRONG"),
        (85, "BUILD"),
        (100, "BUILD"),
    ],
)
def test_recommendation_boundaries(score: float, expected: str) -> None:
    assert recommendation(score) == expected


def test_scoring_configuration_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        ScoringWeights(demand=0.5)
    with pytest.raises(ValueError, match="ordered"):
        RecommendationThresholds(watch=70, investigate=60)
    with pytest.raises(ValueError, match="between 0 and 100"):
        OpportunityComponents(101, 0, 0, 0, 0, 0, 0)
