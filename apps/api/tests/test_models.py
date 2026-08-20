from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Cluster,
    ClusterKeyword,
    DiscoveryRun,
    Keyword,
    KeywordAnalysis,
    KeywordObservation,
    MonthlySearchVolume,
    Opportunity,
    ProductHypothesis,
    Seed,
    Workspace,
)
from app.models.keyword import normalize_keyword

EXPECTED_TABLES = {
    "cluster_keywords",
    "clusters",
    "discovery_runs",
    "keyword_analyses",
    "keyword_observations",
    "keywords",
    "monthly_search_volumes",
    "opportunities",
    "product_hypotheses",
    "seeds",
    "user_sessions",
    "users",
    "workspaces",
}


def test_all_stage_two_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_raw_observations_and_calculated_metrics_have_separate_boundaries() -> None:
    observation_columns = set(KeywordObservation.__table__.columns.keys())
    analysis_columns = set(KeywordAnalysis.__table__.columns.keys())

    assert "raw_json" in observation_columns
    assert "growth_3m" not in observation_columns
    assert "raw_json" not in analysis_columns
    assert {"growth_3m", "robust_z_score", "demand_score"} <= analysis_columns


def test_keyword_normalization_is_stable_and_unicode_aware() -> None:
    assert normalize_keyword("  JSON\t Formatter  ") == "json formatter"
    assert normalize_keyword("ＪＳＯＮ Formatter") == "json formatter"


def test_complete_model_graph_can_be_persisted() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    workspace = Workspace(name="Local workspace")
    run = DiscoveryRun(
        workspace=workspace,
        provider="mock",
        status="completed",
        language="en",
        geo="US",
        config_json={"limit": 500},
        seeds=[Seed(text="json")],
    )
    keyword = Keyword(
        normalized_text=normalize_keyword("JSON formatter"),
        display_text="JSON formatter",
        language="en",
        geo="US",
    )
    observation = KeywordObservation(
        keyword=keyword,
        provider="mock",
        avg_monthly_searches=12_000,
        competition="MEDIUM",
        competition_index=Decimal("55.00"),
        low_top_page_bid=Decimal("0.8000"),
        high_top_page_bid=Decimal("2.1000"),
        currency="USD",
        raw_json={"fixture": True},
        monthly_volumes=[MonthlySearchVolume(year=2026, month=1, searches=12_000)],
    )
    analysis = KeywordAnalysis(
        keyword=keyword,
        analysis_version="v1",
        growth_3m=0.25,
        demand_score=80,
        growth_score=70,
        commercial_score=60,
        competition_score=45,
        stability_score=75,
    )
    cluster = Cluster(name="JSON developer tools", description="Developer utilities")
    cluster_link = ClusterKeyword(cluster=cluster, keyword=keyword, similarity=0.96)
    opportunity = Opportunity(
        cluster=cluster,
        demand_score=80,
        growth_score=70,
        commercial_score=60,
        competition_score=45,
        tool_intent_score=95,
        buildability_score=92,
        stability_score=75,
        opportunity_score=84,
        recommendation="BUILD",
        score_version="v1",
    )
    hypothesis = ProductHypothesis(
        opportunity=opportunity,
        title="JSON to typed schema",
        problem="Schema creation is repetitive.",
        target_user="TypeScript developers",
        input_description="JSON document",
        output_description="Typed validation schema",
        features_json=[{"name": "converter"}],
        monetization_json=[],
        risks_json=[],
        estimated_complexity="low",
        llm_provider="mock",
        llm_model="deterministic",
    )

    with Session(engine) as session:
        session.add_all([run, observation, analysis, cluster_link, hypothesis])
        session.commit()

        assert session.query(Workspace).count() == 1
        assert session.query(KeywordObservation).count() == 1
        assert session.query(KeywordAnalysis).count() == 1
        assert session.query(ProductHypothesis).count() == 1
