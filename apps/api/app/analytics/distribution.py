import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True, slots=True)
class HistogramBin:
    start: float
    end: float
    count: int
    normal_fit: float | None


@dataclass(frozen=True, slots=True)
class QQPoint:
    theoretical: float
    observed: float


@dataclass(frozen=True, slots=True)
class DistributionDiagnostics:
    mean: float | None
    median: float | None
    std: float | None
    mad: float | None
    skewness: float | None
    kurtosis: float | None
    shapiro_wilk_p_value: float | None
    sample_size: int
    summary: str


@dataclass(frozen=True, slots=True)
class DistributionResult:
    metric: str
    label: str
    histogram: tuple[HistogramBin, ...]
    qq_points: tuple[QQPoint, ...]
    diagnostics: DistributionDiagnostics
    insufficient_sample: bool


def _finite(value: float) -> float | None:
    return value if math.isfinite(value) else None


def analyze_distribution(values: list[float], *, metric: str, label: str) -> DistributionResult:
    finite_values = [value for value in values if math.isfinite(value)]
    sample = np.asarray(finite_values, dtype=np.float64)
    size = int(sample.size)
    if size == 0:
        return DistributionResult(
            metric=metric,
            label=label,
            histogram=(),
            qq_points=(),
            diagnostics=DistributionDiagnostics(
                mean=None,
                median=None,
                std=None,
                mad=None,
                skewness=None,
                kurtosis=None,
                shapiro_wilk_p_value=None,
                sample_size=0,
                summary="No observations are available for this metric.",
            ),
            insufficient_sample=True,
        )

    mean = float(np.mean(sample))
    median = float(np.median(sample))
    std = float(np.std(sample, ddof=0))
    mad = float(np.median(np.abs(sample - median)))
    is_constant = bool(np.ptp(sample) == 0)
    skewness = (
        _finite(float(stats.skew(sample, bias=False)))
        if size >= 3 and not is_constant
        else None
    )
    kurtosis = (
        _finite(float(stats.kurtosis(sample, fisher=True, bias=False)))
        if size >= 4 and not is_constant
        else None
    )

    shapiro_p: float | None = None
    if size >= 3 and not is_constant:
        shapiro_sample = (
            sample
            if size <= 5000
            else sample[np.linspace(0, size - 1, 5000, dtype=int)]
        )
        shapiro_p = _finite(float(stats.shapiro(shapiro_sample).pvalue))

    insufficient = size < 8
    if insufficient:
        summary = "Insufficient sample size for reliable distribution diagnostics."
    elif is_constant:
        summary = "All observed values are identical; a normal fit is not informative."
    elif shapiro_p is not None and shapiro_p < 0.05:
        summary = "Data shows substantial deviation from a normal fit."
    else:
        summary = "Normality was not rejected at α = 0.05; this is not proof of Gaussianity."

    bin_count = min(30, max(1, round(math.sqrt(size))))
    if is_constant:
        edges = np.asarray([sample[0] - 0.5, sample[0] + 0.5], dtype=np.float64)
        counts = np.asarray([size], dtype=np.int64)
    else:
        raw_counts, raw_edges = np.histogram(sample, bins=bin_count)
        counts = np.asarray(raw_counts, dtype=np.int64)
        edges = np.asarray(raw_edges, dtype=np.float64)

    histogram: list[HistogramBin] = []
    for index, count in enumerate(counts):
        start = float(edges[index])
        end = float(edges[index + 1])
        normal_fit = None
        if std > 0:
            center = (start + end) / 2
            density = math.exp(-0.5 * ((center - mean) / std) ** 2) / (std * math.sqrt(math.tau))
            normal_fit = density * size * (end - start)
        histogram.append(HistogramBin(start, end, int(count), normal_fit))

    qq_points: list[QQPoint] = []
    if size >= 2 and not is_constant:
        observed = np.sort(sample)
        probabilities = (np.arange(1, size + 1) - 0.375) / (size + 0.25)
        theoretical = stats.norm.ppf(probabilities)
        qq_points = [
            QQPoint(float(expected), float(actual))
            for expected, actual in zip(theoretical, observed, strict=True)
        ]

    return DistributionResult(
        metric=metric,
        label=label,
        histogram=tuple(histogram),
        qq_points=tuple(qq_points),
        diagnostics=DistributionDiagnostics(
            mean=mean,
            median=median,
            std=std,
            mad=mad,
            skewness=skewness,
            kurtosis=kurtosis,
            shapiro_wilk_p_value=shapiro_p,
            sample_size=size,
            summary=summary,
        ),
        insufficient_sample=insufficient,
    )
