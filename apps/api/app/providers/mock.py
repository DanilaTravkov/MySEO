import hashlib
import math
import random
from datetime import date
from decimal import Decimal

from app.models.keyword import normalize_keyword
from app.providers.base import KeywordIdea, KeywordMetrics, MonthlyMetric

MOCK_GENERATOR_VERSION = "mock-v1"
MOCK_DATASET_SIZE = 500
MOCK_MONTHS = 12

_ACTIONS = (
    "analyzer",
    "calculator",
    "checker",
    "compressor",
    "converter",
    "editor",
    "extractor",
    "formatter",
    "generator",
    "maker",
    "optimizer",
    "parser",
    "previewer",
    "scanner",
    "template",
    "tester",
    "to csv",
    "to json",
    "to markdown",
    "to pdf",
    "validator",
    "viewer",
    "visualizer",
    "workflow",
    "writer",
)

_QUALIFIERS = (
    "api",
    "batch",
    "browser",
    "bulk",
    "desktop",
    "extension",
    "fast",
    "for agencies",
    "for developers",
    "for ecommerce",
    "for freelancers",
    "for students",
    "free",
    "no signup",
    "offline",
    "online",
    "open source",
    "plugin",
    "privacy first",
    "simple",
    "software",
    "tool",
    "web app",
    "with api",
    "without login",
)

_PROFILES = (
    "stable",
    "declining",
    "growing",
    "spike",
    "seasonal",
    "noisy",
    "high_cpc_low_volume",
    "high_volume_low_intent",
)


def _seed_for(value: str) -> int:
    digest = hashlib.sha256(f"{MOCK_GENERATOR_VERSION}:{value}".encode()).digest()
    return int.from_bytes(digest[:8])


def _month_at(offset: int) -> tuple[int, int]:
    start = date(2025, 8, 1)
    month_index = start.year * 12 + start.month - 1 + offset
    return month_index // 12, month_index % 12 + 1


class MockSearchDataProvider:
    """Deterministic provider containing varied, non-Gaussian demand patterns."""

    async def discover_keywords(
        self,
        seeds: list[str],
        language: str,
        geo: str,
        limit: int,
    ) -> list[KeywordIdea]:
        del language, geo
        clean_seeds = list(dict.fromkeys(normalize_keyword(seed) for seed in seeds if seed.strip()))
        if not clean_seeds:
            raise ValueError("At least one non-empty seed is required.")

        ideas: list[KeywordIdea] = []
        for index in range(limit):
            seed = clean_seeds[index % len(clean_seeds)]
            combination = index // len(clean_seeds)
            action = _ACTIONS[combination % len(_ACTIONS)]
            qualifier = _QUALIFIERS[(combination // len(_ACTIONS)) % len(_QUALIFIERS)]
            cycle = combination // (len(_ACTIONS) * len(_QUALIFIERS))
            suffix = f" {cycle + 2}" if cycle else ""
            ideas.append(KeywordIdea(text=f"{seed} {action} {qualifier}{suffix}"))
        return ideas

    async def historical_metrics(
        self,
        keywords: list[str],
        language: str,
        geo: str,
    ) -> list[KeywordMetrics]:
        del language, geo
        return [self._metrics_for(keyword) for keyword in keywords]

    def _metrics_for(self, keyword: str) -> KeywordMetrics:
        rng = random.Random(_seed_for(normalize_keyword(keyword)))
        profile = _PROFILES[rng.randrange(len(_PROFILES))]
        base = int(math.exp(rng.uniform(math.log(40), math.log(180_000))))

        if profile == "high_cpc_low_volume":
            base = rng.randint(25, 420)
            low_bid = Decimal(str(round(rng.uniform(7.5, 18), 2)))
            high_bid = low_bid + Decimal(str(round(rng.uniform(4, 20), 2)))
            competition_index = Decimal(str(round(rng.uniform(72, 98), 2)))
        elif profile == "high_volume_low_intent":
            base = rng.randint(80_000, 650_000)
            low_bid = Decimal(str(round(rng.uniform(0.03, 0.22), 2)))
            high_bid = low_bid + Decimal(str(round(rng.uniform(0.08, 0.45), 2)))
            competition_index = Decimal(str(round(rng.uniform(4, 28), 2)))
        else:
            low_bid = Decimal(str(round(rng.uniform(0.15, 5.5), 2)))
            high_bid = low_bid + Decimal(str(round(rng.uniform(0.25, 7.5), 2)))
            competition_index = Decimal(str(round(rng.uniform(12, 92), 2)))

        volumes = tuple(
            MonthlyMetric(year=year, month=month, searches=self._volume(profile, base, index, rng))
            for index in range(MOCK_MONTHS)
            for year, month in [_month_at(index)]
        )
        average = round(sum(item.searches for item in volumes) / len(volumes))
        competition_value = float(competition_index)
        competition = (
            "LOW" if competition_value < 34 else "MEDIUM" if competition_value < 67 else "HIGH"
        )

        return KeywordMetrics(
            keyword=keyword,
            avg_monthly_searches=average,
            competition=competition,
            competition_index=competition_index,
            low_top_page_bid=low_bid,
            high_top_page_bid=high_bid,
            currency="USD",
            monthly_volumes=volumes,
            raw_data={
                "source": "deterministic_fixture",
                "generator_version": MOCK_GENERATOR_VERSION,
                "profile": profile,
            },
        )

    @staticmethod
    def _volume(profile: str, base: int, index: int, rng: random.Random) -> int:
        noise = rng.uniform(-0.06, 0.06)
        if profile == "declining":
            factor = 1.5 - 0.075 * index + noise
        elif profile == "growing":
            factor = 0.5 + 0.105 * index + noise
        elif profile == "spike":
            factor = (4.6 if index == 10 else 2.5 if index == 11 else 1.0) + noise
        elif profile == "seasonal":
            factor = 1 + 0.55 * math.sin((index + 1) * math.tau / 12) + noise
        elif profile == "noisy":
            factor = 1 + rng.uniform(-0.58, 0.68)
        else:
            factor = 1 + noise
        return max(0, round(base * factor))
