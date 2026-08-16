import math

from app.analytics.distribution import analyze_distribution


def test_distribution_returns_empirical_histogram_normal_fit_and_qq() -> None:
    values = [math.log1p(value) for value in range(1, 101)]

    result = analyze_distribution(values, metric="log_demand", label="Log demand")

    assert sum(item.count for item in result.histogram) == 100
    assert all(item.normal_fit is not None for item in result.histogram)
    assert len(result.qq_points) == 100
    assert result.diagnostics.sample_size == 100
    assert result.diagnostics.mean is not None
    assert result.diagnostics.median is not None
    assert result.diagnostics.mad is not None
    assert result.diagnostics.shapiro_wilk_p_value is not None
    assert "Gaussian" not in result.diagnostics.summary
    assert not result.insufficient_sample


def test_distribution_warns_for_small_samples() -> None:
    result = analyze_distribution([1, 2, 3], metric="growth", label="Growth")

    assert result.insufficient_sample
    assert result.diagnostics.summary == (
        "Insufficient sample size for reliable distribution diagnostics."
    )


def test_constant_distribution_does_not_invent_normal_fit() -> None:
    result = analyze_distribution([5.0] * 20, metric="competition", label="Competition")

    assert len(result.histogram) == 1
    assert result.histogram[0].normal_fit is None
    assert result.qq_points == ()
    assert result.diagnostics.shapiro_wilk_p_value is None
