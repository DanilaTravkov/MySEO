from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class KeywordIdea:
    text: str


@dataclass(frozen=True, slots=True)
class MonthlyMetric:
    year: int
    month: int
    searches: int


@dataclass(frozen=True, slots=True)
class KeywordMetrics:
    keyword: str
    avg_monthly_searches: int
    competition: str | None
    competition_index: Decimal | None
    low_top_page_bid: Decimal | None
    high_top_page_bid: Decimal | None
    currency: str | None
    monthly_volumes: tuple[MonthlyMetric, ...]
    raw_data: dict[str, object]


class SearchDataProvider(Protocol):
    async def discover_keywords(
        self,
        seeds: list[str],
        language: str,
        geo: str,
        limit: int,
    ) -> list[KeywordIdea]: ...

    async def historical_metrics(
        self,
        keywords: list[str],
        language: str,
        geo: str,
    ) -> list[KeywordMetrics]: ...
