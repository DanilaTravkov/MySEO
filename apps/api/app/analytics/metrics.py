import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True, slots=True)
class KeywordStatistics:
    growth_3m: float | None
    growth_6m: float | None
    normalized_slope: float | None
    volatility: float | None
    z_score: float | None
    robust_z_score: float | None
    historical_percentile: float | None
    skewness: float | None
    kurtosis: float | None
    normality_p_value: float | None


def _finite(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _growth(values: np.ndarray, window: int) -> float | None:
    if values.size < window * 2:
        return None
    current_mean = float(np.mean(values[-window:]))
    previous_mean = float(np.mean(values[-window * 2 : -window]))
    if previous_mean == 0:
        return None
    return current_mean / previous_mean - 1


def calculate_keyword_statistics(searches: list[int]) -> KeywordStatistics:
    if not searches:
        raise ValueError("At least one monthly search value is required.")
    if any(value < 0 for value in searches):
        raise ValueError("Monthly search values must be non-negative.")

    values = np.asarray(searches, dtype=np.float64)
    history = values[:-1]
    log_values = np.log1p(values)

    slope: float | None = None
    if values.size >= 2:
        x = np.arange(values.size, dtype=np.float64)
        centered_x = x - float(np.mean(x))
        denominator = float(np.sum(centered_x**2))
        if denominator > 0:
            slope = _finite(
                float(np.sum(centered_x * (log_values - float(np.mean(log_values)))))
                / denominator
            )

    mean = float(np.mean(values))
    volatility = _finite(float(np.std(values, ddof=0)) / mean) if mean > 0 else None

    z_score: float | None = None
    robust_z_score: float | None = None
    percentile: float | None = None
    if history.size:
        history_std = float(np.std(history, ddof=0))
        if history_std > 0:
            z_score = _finite((float(values[-1]) - float(np.mean(history))) / history_std)

        history_median = float(np.median(history))
        mad = float(np.median(np.abs(history - history_median)))
        if mad > 0:
            robust_z_score = _finite(0.6745 * (float(values[-1]) - history_median) / mad)

        percentile = min(
            100.0,
            max(0.0, float(stats.percentileofscore(history, values[-1], kind="weak"))),
        )

    is_constant = bool(np.ptp(values) == 0)
    skewness = None
    kurtosis = None
    normality_p_value = None
    if not is_constant and values.size >= 3:
        skewness = _finite(float(stats.skew(values, bias=False)))
        normality_p_value = _finite(float(stats.shapiro(values).pvalue))
    if not is_constant and values.size >= 4:
        kurtosis = _finite(float(stats.kurtosis(values, fisher=True, bias=False)))

    return KeywordStatistics(
        growth_3m=_growth(values, 3),
        growth_6m=_growth(values, 6),
        normalized_slope=slope,
        volatility=volatility,
        z_score=z_score,
        robust_z_score=robust_z_score,
        historical_percentile=percentile,
        skewness=skewness,
        kurtosis=kurtosis,
        normality_p_value=normality_p_value,
    )
