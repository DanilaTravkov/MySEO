"""Create the Search Demand Intelligence domain model.

Revision ID: 20260810_0002
Revises: 20260810_0001
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0002"
down_revision: str | None = "20260810_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "keywords",
        sa.Column("normalized_text", sa.String(length=512), nullable=False),
        sa.Column("display_text", sa.String(length=512), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("geo", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_text",
            "language",
            "geo",
            name="uq_keywords_normalized_language_geo",
        ),
    )
    op.create_index("ix_keywords_display_text", "keywords", ["display_text"], unique=False)
    op.create_table(
        "clusters",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "discovery_runs",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("geo", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_discovery_runs_status",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_discovery_runs_workspace_id",
        "discovery_runs",
        ["workspace_id"],
        unique=False,
    )
    op.create_table(
        "keyword_observations",
        sa.Column("keyword_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("avg_monthly_searches", sa.Integer(), nullable=True),
        sa.Column("competition", sa.String(length=32), nullable=True),
        sa.Column("competition_index", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("low_top_page_bid", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("high_top_page_bid", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "avg_monthly_searches IS NULL OR avg_monthly_searches >= 0",
            name="ck_keyword_observations_avg_searches_nonnegative",
        ),
        sa.CheckConstraint(
            "competition_index IS NULL OR (competition_index >= 0 AND competition_index <= 100)",
            name="ck_keyword_observations_competition_index_range",
        ),
        sa.CheckConstraint(
            "high_top_page_bid IS NULL OR high_top_page_bid >= 0",
            name="ck_keyword_observations_high_bid_nonnegative",
        ),
        sa.CheckConstraint(
            "low_top_page_bid IS NULL OR high_top_page_bid IS NULL OR "
            "high_top_page_bid >= low_top_page_bid",
            name="ck_keyword_observations_bid_order",
        ),
        sa.CheckConstraint(
            "low_top_page_bid IS NULL OR low_top_page_bid >= 0",
            name="ck_keyword_observations_low_bid_nonnegative",
        ),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_keyword_observations_keyword_observed",
        "keyword_observations",
        ["keyword_id", "observed_at"],
        unique=False,
    )
    op.create_table(
        "keyword_analyses",
        sa.Column("keyword_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_version", sa.String(length=32), nullable=False),
        sa.Column("growth_3m", sa.Float(), nullable=True),
        sa.Column("growth_6m", sa.Float(), nullable=True),
        sa.Column("normalized_slope", sa.Float(), nullable=True),
        sa.Column("volatility", sa.Float(), nullable=True),
        sa.Column("z_score", sa.Float(), nullable=True),
        sa.Column("robust_z_score", sa.Float(), nullable=True),
        sa.Column("historical_percentile", sa.Float(), nullable=True),
        sa.Column("skewness", sa.Float(), nullable=True),
        sa.Column("kurtosis", sa.Float(), nullable=True),
        sa.Column("normality_p_value", sa.Float(), nullable=True),
        sa.Column("demand_score", sa.Float(), nullable=True),
        sa.Column("growth_score", sa.Float(), nullable=True),
        sa.Column("commercial_score", sa.Float(), nullable=True),
        sa.Column("competition_score", sa.Float(), nullable=True),
        sa.Column("stability_score", sa.Float(), nullable=True),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "commercial_score IS NULL OR (commercial_score >= 0 AND commercial_score <= 100)",
            name="ck_keyword_analyses_commercial_score",
        ),
        sa.CheckConstraint(
            "competition_score IS NULL OR (competition_score >= 0 AND competition_score <= 100)",
            name="ck_keyword_analyses_competition_score",
        ),
        sa.CheckConstraint(
            "demand_score IS NULL OR (demand_score >= 0 AND demand_score <= 100)",
            name="ck_keyword_analyses_demand_score",
        ),
        sa.CheckConstraint(
            "growth_score IS NULL OR (growth_score >= 0 AND growth_score <= 100)",
            name="ck_keyword_analyses_growth_score",
        ),
        sa.CheckConstraint(
            "historical_percentile IS NULL OR "
            "(historical_percentile >= 0 AND historical_percentile <= 100)",
            name="ck_keyword_analyses_historical_percentile",
        ),
        sa.CheckConstraint(
            "normality_p_value IS NULL OR "
            "(normality_p_value >= 0 AND normality_p_value <= 1)",
            name="ck_keyword_analyses_normality_p_value",
        ),
        sa.CheckConstraint(
            "stability_score IS NULL OR (stability_score >= 0 AND stability_score <= 100)",
            name="ck_keyword_analyses_stability_score",
        ),
        sa.CheckConstraint(
            "volatility IS NULL OR volatility >= 0",
            name="ck_keyword_analyses_volatility_nonnegative",
        ),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("keyword_id", "analysis_version"),
    )
    op.create_index(
        "ix_keyword_analyses_calculated_at",
        "keyword_analyses",
        ["calculated_at"],
        unique=False,
    )
    op.create_table(
        "cluster_keywords",
        sa.Column("cluster_id", sa.Uuid(), nullable=False),
        sa.Column("keyword_id", sa.Uuid(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=True),
        sa.CheckConstraint(
            "similarity IS NULL OR (similarity >= 0 AND similarity <= 1)",
            name="ck_cluster_keywords_similarity",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_id", "keyword_id"),
    )
    op.create_table(
        "monthly_search_volumes",
        sa.Column("keyword_observation_id", sa.Uuid(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("searches", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="ck_monthly_volumes_month"),
        sa.CheckConstraint("searches >= 0", name="ck_monthly_volumes_searches_nonnegative"),
        sa.CheckConstraint("year >= 2000 AND year <= 2200", name="ck_monthly_volumes_year"),
        sa.ForeignKeyConstraint(
            ["keyword_observation_id"],
            ["keyword_observations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "keyword_observation_id",
            "year",
            "month",
            name="uq_monthly_volumes_observation_period",
        ),
    )
    op.create_index(
        "ix_monthly_search_volumes_keyword_observation_id",
        "monthly_search_volumes",
        ["keyword_observation_id"],
        unique=False,
    )
    op.create_table(
        "opportunities",
        sa.Column("cluster_id", sa.Uuid(), nullable=False),
        sa.Column("demand_score", sa.Float(), nullable=False),
        sa.Column("growth_score", sa.Float(), nullable=False),
        sa.Column("commercial_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("tool_intent_score", sa.Float(), nullable=False),
        sa.Column("buildability_score", sa.Float(), nullable=False),
        sa.Column("stability_score", sa.Float(), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=32), nullable=False),
        sa.Column("score_version", sa.String(length=32), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "buildability_score >= 0 AND buildability_score <= 100",
            name="ck_opportunities_buildability_score",
        ),
        sa.CheckConstraint(
            "commercial_score >= 0 AND commercial_score <= 100",
            name="ck_opportunities_commercial_score",
        ),
        sa.CheckConstraint(
            "competition_score >= 0 AND competition_score <= 100",
            name="ck_opportunities_competition_score",
        ),
        sa.CheckConstraint(
            "demand_score >= 0 AND demand_score <= 100",
            name="ck_opportunities_demand_score",
        ),
        sa.CheckConstraint(
            "growth_score >= 0 AND growth_score <= 100",
            name="ck_opportunities_growth_score",
        ),
        sa.CheckConstraint(
            "opportunity_score >= 0 AND opportunity_score <= 100",
            name="ck_opportunities_opportunity_score",
        ),
        sa.CheckConstraint(
            "recommendation IN ('build', 'consider', 'skip')",
            name="ck_opportunities_recommendation",
        ),
        sa.CheckConstraint(
            "stability_score >= 0 AND stability_score <= 100",
            name="ck_opportunities_stability_score",
        ),
        sa.CheckConstraint(
            "tool_intent_score >= 0 AND tool_intent_score <= 100",
            name="ck_opportunities_tool_intent_score",
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "score_version", name="uq_opportunities_cluster_version"),
    )
    op.create_index(
        "ix_opportunities_cluster_id",
        "opportunities",
        ["cluster_id"],
        unique=False,
    )
    op.create_table(
        "seeds",
        sa.Column("discovery_run_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(length=512), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["discovery_run_id"],
            ["discovery_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discovery_run_id", "text", name="uq_seeds_run_text"),
    )
    op.create_index("ix_seeds_discovery_run_id", "seeds", ["discovery_run_id"], unique=False)
    op.create_table(
        "product_hypotheses",
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("target_user", sa.Text(), nullable=False),
        sa.Column("input_description", sa.Text(), nullable=False),
        sa.Column("output_description", sa.Text(), nullable=False),
        sa.Column("features_json", sa.JSON(), nullable=False),
        sa.Column("monetization_json", sa.JSON(), nullable=False),
        sa.Column("risks_json", sa.JSON(), nullable=False),
        sa.Column("estimated_complexity", sa.String(length=16), nullable=False),
        sa.Column("build_brief_markdown", sa.Text(), nullable=True),
        sa.Column("llm_provider", sa.String(length=64), nullable=True),
        sa.Column("llm_model", sa.String(length=128), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "estimated_complexity IN ('low', 'medium', 'high')",
            name="ck_product_hypotheses_complexity",
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_hypotheses_opportunity_id",
        "product_hypotheses",
        ["opportunity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_product_hypotheses_opportunity_id", table_name="product_hypotheses")
    op.drop_table("product_hypotheses")
    op.drop_index("ix_seeds_discovery_run_id", table_name="seeds")
    op.drop_table("seeds")
    op.drop_index("ix_opportunities_cluster_id", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index(
        "ix_monthly_search_volumes_keyword_observation_id",
        table_name="monthly_search_volumes",
    )
    op.drop_table("monthly_search_volumes")
    op.drop_table("cluster_keywords")
    op.drop_index("ix_keyword_analyses_calculated_at", table_name="keyword_analyses")
    op.drop_table("keyword_analyses")
    op.drop_index(
        "ix_keyword_observations_keyword_observed",
        table_name="keyword_observations",
    )
    op.drop_table("keyword_observations")
    op.drop_index("ix_discovery_runs_workspace_id", table_name="discovery_runs")
    op.drop_table("discovery_runs")
    op.drop_table("clusters")
    op.drop_index("ix_keywords_display_text", table_name="keywords")
    op.drop_table("keywords")
    op.drop_table("workspaces")
