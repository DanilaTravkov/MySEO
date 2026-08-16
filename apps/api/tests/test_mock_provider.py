import asyncio
from decimal import Decimal

from app.providers.mock import (
    MOCK_DATASET_SIZE,
    MOCK_MONTHS,
    MockSearchDataProvider,
)


def test_mock_provider_builds_deterministic_500_by_12_fixture() -> None:
    provider = MockSearchDataProvider()

    async def load_fixture() -> tuple[object, object, object]:
        ideas = await provider.discover_keywords(
            ["json", "pdf", "typescript"],
            "en",
            "US",
            MOCK_DATASET_SIZE,
        )
        first = await provider.historical_metrics(
            [idea.text for idea in ideas],
            "en",
            "US",
        )
        second = await provider.historical_metrics(
            [idea.text for idea in ideas],
            "en",
            "US",
        )
        return ideas, first, second

    ideas, first_metrics, second_metrics = asyncio.run(load_fixture())

    assert len(ideas) == MOCK_DATASET_SIZE  # type: ignore[arg-type]
    assert len({idea.text for idea in ideas}) == MOCK_DATASET_SIZE  # type: ignore[union-attr]
    assert first_metrics == second_metrics
    assert all(len(item.monthly_volumes) == MOCK_MONTHS for item in first_metrics)  # type: ignore[union-attr]


def test_mock_fixture_contains_every_required_demand_shape() -> None:
    provider = MockSearchDataProvider()

    async def metrics() -> object:
        ideas = await provider.discover_keywords(["json"], "en", "US", MOCK_DATASET_SIZE)
        return await provider.historical_metrics([idea.text for idea in ideas], "en", "US")

    result = asyncio.run(metrics())
    profiles = {item.raw_data["profile"] for item in result}  # type: ignore[union-attr]

    assert profiles == {
        "stable",
        "declining",
        "growing",
        "spike",
        "seasonal",
        "noisy",
        "high_cpc_low_volume",
        "high_volume_low_intent",
    }
    high_cpc = [item for item in result if item.raw_data["profile"] == "high_cpc_low_volume"]  # type: ignore[union-attr]
    low_intent = [
        item for item in result if item.raw_data["profile"] == "high_volume_low_intent"  # type: ignore[union-attr]
    ]
    assert high_cpc and all(item.low_top_page_bid >= Decimal("7.5") for item in high_cpc)
    assert low_intent and all(item.avg_monthly_searches >= 75_000 for item in low_intent)

