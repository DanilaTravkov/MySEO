import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.models.keyword import normalize_keyword
from app.providers.base import KeywordIdea, KeywordMetrics, MonthlyMetric

REQUIRED_COLUMNS = {
    "keyword",
    "year",
    "month",
    "searches",
    "competition_index",
    "low_bid",
    "high_bid",
}


@dataclass(frozen=True, slots=True)
class CsvValidationIssue:
    row: int | None
    column: str | None
    message: str
    value: str | None = None


class CsvValidationError(ValueError):
    def __init__(self, issues: list[CsvValidationIssue]) -> None:
        self.issues = issues
        super().__init__("CSV validation failed with " f"{len(issues)} issue(s).")


@dataclass(frozen=True, slots=True)
class _CsvRow:
    keyword: str
    year: int
    month: int
    searches: int
    competition_index: Decimal
    low_bid: Decimal
    high_bid: Decimal


class CsvSearchDataProvider:
    def __init__(self, content: str, *, currency: str = "USD") -> None:
        self.currency = currency.upper()
        self._rows = self._parse(content)
        self._metrics = self._aggregate(self._rows)

    async def discover_keywords(
        self,
        seeds: list[str],
        language: str,
        geo: str,
        limit: int,
    ) -> list[KeywordIdea]:
        del language, geo
        filters = [normalize_keyword(seed) for seed in seeds if seed.strip()]
        keywords = [metrics.keyword for metrics in self._metrics.values()]
        if filters:
            keywords = [
                keyword
                for keyword in keywords
                if any(seed in normalize_keyword(keyword) for seed in filters)
            ]
        return [KeywordIdea(text=keyword) for keyword in keywords[:limit]]

    async def historical_metrics(
        self,
        keywords: list[str],
        language: str,
        geo: str,
    ) -> list[KeywordMetrics]:
        del language, geo
        return [
            self._metrics[normalized]
            for keyword in keywords
            if (normalized := normalize_keyword(keyword)) in self._metrics
        ]

    @staticmethod
    def _parse(content: str) -> list[_CsvRow]:
        reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise CsvValidationError(
                [
                    CsvValidationIssue(
                        row=None,
                        column=column,
                        message=f"Missing required column: {column}.",
                    )
                    for column in missing
                ]
            )

        parsed: list[_CsvRow] = []
        issues: list[CsvValidationIssue] = []
        seen: set[tuple[str, int, int]] = set()
        for row_number, raw in enumerate(reader, start=2):
            row_issues, row = CsvSearchDataProvider._parse_row(raw, row_number)
            issues.extend(row_issues)
            if row is None:
                continue
            key = (normalize_keyword(row.keyword), row.year, row.month)
            if key in seen:
                issues.append(
                    CsvValidationIssue(
                        row=row_number,
                        column=None,
                        message="Duplicate keyword/year/month row.",
                    )
                )
                continue
            seen.add(key)
            parsed.append(row)

        if not parsed and not issues:
            issues.append(
                CsvValidationIssue(row=None, column=None, message="CSV contains no data rows.")
            )
        if issues:
            raise CsvValidationError(issues)
        return parsed

    @staticmethod
    def _parse_row(
        raw: dict[str, str | None],
        row_number: int,
    ) -> tuple[list[CsvValidationIssue], _CsvRow | None]:
        issues: list[CsvValidationIssue] = []
        keyword = (raw.get("keyword") or "").strip()
        if not keyword:
            issues.append(CsvValidationIssue(row_number, "keyword", "Keyword must not be empty."))

        year = CsvSearchDataProvider._integer(raw, "year", row_number, issues)
        month = CsvSearchDataProvider._integer(raw, "month", row_number, issues)
        searches = CsvSearchDataProvider._integer(raw, "searches", row_number, issues)
        competition = CsvSearchDataProvider._decimal(raw, "competition_index", row_number, issues)
        low_bid = CsvSearchDataProvider._decimal(raw, "low_bid", row_number, issues)
        high_bid = CsvSearchDataProvider._decimal(raw, "high_bid", row_number, issues)

        if year is not None and not 2000 <= year <= 2200:
            issues.append(
                CsvValidationIssue(row_number, "year", "Year must be between 2000 and 2200.")
            )
        if month is not None and not 1 <= month <= 12:
            issues.append(
                CsvValidationIssue(row_number, "month", "Month must be between 1 and 12.")
            )
        if searches is not None and searches < 0:
            issues.append(
                CsvValidationIssue(row_number, "searches", "Searches must be non-negative.")
            )
        if competition is not None and not Decimal(0) <= competition <= Decimal(100):
            issues.append(
                CsvValidationIssue(
                    row_number,
                    "competition_index",
                    "Competition index must be between 0 and 100.",
                )
            )
        for column, value in (("low_bid", low_bid), ("high_bid", high_bid)):
            if value is not None and value < 0:
                issues.append(CsvValidationIssue(row_number, column, "Bid must be non-negative."))
        if low_bid is not None and high_bid is not None and high_bid < low_bid:
            issues.append(
                CsvValidationIssue(
                    row_number,
                    "high_bid",
                    "High bid must be greater than or equal to low bid.",
                )
            )

        if issues:
            return issues, None
        assert year is not None
        assert month is not None
        assert searches is not None
        assert competition is not None
        assert low_bid is not None
        assert high_bid is not None
        return issues, _CsvRow(keyword, year, month, searches, competition, low_bid, high_bid)

    @staticmethod
    def _integer(
        raw: dict[str, str | None],
        column: str,
        row: int,
        issues: list[CsvValidationIssue],
    ) -> int | None:
        value = (raw.get(column) or "").strip()
        try:
            return int(value)
        except ValueError:
            issues.append(CsvValidationIssue(row, column, "Expected an integer.", value))
            return None

    @staticmethod
    def _decimal(
        raw: dict[str, str | None],
        column: str,
        row: int,
        issues: list[CsvValidationIssue],
    ) -> Decimal | None:
        value = (raw.get(column) or "").strip()
        try:
            result = Decimal(value)
            if not result.is_finite():
                raise InvalidOperation
            return result
        except InvalidOperation:
            issues.append(CsvValidationIssue(row, column, "Expected a finite number.", value))
            return None

    def _aggregate(self, rows: list[_CsvRow]) -> dict[str, KeywordMetrics]:
        grouped: defaultdict[str, list[_CsvRow]] = defaultdict(list)
        for row in rows:
            grouped[normalize_keyword(row.keyword)].append(row)

        result: dict[str, KeywordMetrics] = {}
        for normalized, keyword_rows in grouped.items():
            ordered = sorted(keyword_rows, key=lambda row: (row.year, row.month))
            count = Decimal(len(ordered))
            competition_index = sum((row.competition_index for row in ordered), Decimal(0)) / count
            low_bid = sum((row.low_bid for row in ordered), Decimal(0)) / count
            high_bid = sum((row.high_bid for row in ordered), Decimal(0)) / count
            average = round(sum(row.searches for row in ordered) / len(ordered))
            competition_value = float(competition_index)
            competition = (
                "LOW" if competition_value < 34 else "MEDIUM" if competition_value < 67 else "HIGH"
            )
            result[normalized] = KeywordMetrics(
                keyword=ordered[0].keyword,
                avg_monthly_searches=average,
                competition=competition,
                competition_index=competition_index,
                low_top_page_bid=low_bid,
                high_top_page_bid=high_bid,
                currency=self.currency,
                monthly_volumes=tuple(
                    MonthlyMetric(year=row.year, month=row.month, searches=row.searches)
                    for row in ordered
                ),
                raw_data={
                    "source": "csv",
                    "row_count": len(ordered),
                    "rows": [
                        {
                            "keyword": row.keyword,
                            "year": row.year,
                            "month": row.month,
                            "searches": row.searches,
                            "competition_index": str(row.competition_index),
                            "low_bid": str(row.low_bid),
                            "high_bid": str(row.high_bid),
                        }
                        for row in ordered
                    ],
                },
            )
        return result
