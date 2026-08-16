import asyncio
from decimal import Decimal

import pytest

from app.providers.csv_provider import CsvSearchDataProvider, CsvValidationError

HEADER = "keyword,year,month,searches,competition_index,low_bid,high_bid\n"


def test_csv_provider_groups_valid_historical_rows() -> None:
    provider = CsvSearchDataProvider(
        HEADER
        + "json formatter,2026,1,12000,55,0.8,2.1\n"
        + "json formatter,2026,2,14000,57,0.9,2.3\n"
        + "pdf compressor,2026,1,8000,42,1.2,3.4\n"
    )

    async def load() -> tuple[object, object]:
        ideas = await provider.discover_keywords([], "en", "US", 100)
        metrics = await provider.historical_metrics([idea.text for idea in ideas], "en", "US")
        return ideas, metrics

    ideas, metrics = asyncio.run(load())

    assert [idea.text for idea in ideas] == ["json formatter", "pdf compressor"]  # type: ignore[union-attr]
    json_metrics = metrics[0]  # type: ignore[index]
    assert json_metrics.avg_monthly_searches == 13_000
    assert json_metrics.competition_index == Decimal("56")
    assert len(json_metrics.monthly_volumes) == 2


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        ("keyword,year\njson,2026\n", "Missing required column"),
        (HEADER + "json,2026,1,oops,55,0.8,2.1\n", "Expected an integer"),
        (HEADER + "json,2026,13,100,55,0.8,2.1\n", "Month must be between 1 and 12"),
        (
            HEADER + "json,2026,1,100,55,0.8,2.1\nJSON,2026,1,200,55,0.8,2.1\n",
            "Duplicate keyword/year/month row",
        ),
    ],
)
def test_csv_provider_explains_validation_errors(content: str, expected_message: str) -> None:
    with pytest.raises(CsvValidationError) as caught:
        CsvSearchDataProvider(content)

    assert any(expected_message in issue.message for issue in caught.value.issues)

