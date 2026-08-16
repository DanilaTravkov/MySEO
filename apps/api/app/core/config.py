from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Search Demand Intelligence API"
    app_env: str = "local"
    database_url: str = (
        "postgresql+psycopg://search_intelligence:local_development_only@localhost:5432/"
        "search_intelligence"
    )
    cors_origins: str = "http://localhost:3000"
    score_weight_demand: float = 0.20
    score_weight_growth: float = 0.15
    score_weight_commercial: float = 0.15
    score_weight_low_competition: float = 0.15
    score_weight_tool_intent: float = 0.15
    score_weight_buildability: float = 0.15
    score_weight_stability: float = 0.05
    recommendation_watch_min: float = 40
    recommendation_investigate_min: float = 60
    recommendation_strong_min: float = 75
    recommendation_build_min: float = 85
    clustering_similarity_threshold: float = Field(default=0.15, ge=0, le=1)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
