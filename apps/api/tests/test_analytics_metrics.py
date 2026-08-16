import math

import pytest

from app.analytics.metrics import calculate_keyword_statistics


def test_growth_trend_volatility_and_outlier_metrics() -> None:
    result = calculate_keyword_statistics([10, 20, 30, 40, 50, 60])

    assert result.growth_3m == pytest.approx(1.5)
    assert result.normalized_slope is not None and result.normalized_slope > 0
    assert result.volatility is not None and result.volatility > 0
    assert result.z_score is not None
    assert result.robust_z_score is not None
    assert result.historical_percentile == 100
    assert result.skewness is not None
    assert result.kurtosis is not None
    assert result.normality_p_value is not None


def test_six_month_growth_uses_two_non_overlapping_windows() -> None:
    result = calculate_keyword_statistics([100] * 6 + [150] * 6)

    assert result.growth_6m == pytest.approx(0.5)


def test_zero_denominator_and_zero_dispersion_return_none() -> None:
    zero_denominator = calculate_keyword_statistics([0, 0, 0, 10, 20, 30])
    constant_history = calculate_keyword_statistics([10, 10, 10, 20])
    all_zero = calculate_keyword_statistics([0] * 12)

    assert zero_denominator.growth_3m is None
    assert constant_history.z_score is None
    assert constant_history.robust_z_score is None
    assert all_zero.volatility is None
    assert all_zero.z_score is None
    assert all_zero.robust_z_score is None
    assert all_zero.skewness is None
    assert all_zero.normality_p_value is None


def test_classical_and_robust_z_scores_use_prior_history() -> None:
    result = calculate_keyword_statistics([10, 20, 30, 40])

    assert result.z_score == pytest.approx(math.sqrt(6), rel=1e-6)
    assert result.robust_z_score == pytest.approx(1.349, rel=1e-6)


def test_negative_search_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        calculate_keyword_statistics([10, -1, 20])

