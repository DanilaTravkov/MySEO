from collections.abc import Sequence

from scipy import stats


def percentile_rank(
    values: Sequence[float | None],
    *,
    higher_is_better: bool = True,
) -> list[float | None]:
    """Map valid values onto 0..100 with average ranks for ties."""
    valid_positions = [index for index, value in enumerate(values) if value is not None]
    result: list[float | None] = [None] * len(values)
    if not valid_positions:
        return result

    valid_values = [float(values[index]) for index in valid_positions]  # type: ignore[arg-type]
    if len(valid_values) == 1:
        result[valid_positions[0]] = 50.0
        return result

    ranks = stats.rankdata(valid_values, method="average")
    for position, rank in zip(valid_positions, ranks, strict=True):
        score = 100 * (float(rank) - 1) / (len(valid_values) - 1)
        result[position] = round(score if higher_is_better else 100 - score, 4)
    return result

