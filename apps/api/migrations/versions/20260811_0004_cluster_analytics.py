"""Store run-scoped deterministic cluster analytics.

Revision ID: 20260811_0004
Revises: 20260810_0003
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260811_0004"
down_revision: str | None = "20260810_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("clusters") as batch_op:
        batch_op.add_column(sa.Column("discovery_run_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "algorithm_version",
                sa.String(length=64),
                nullable=False,
                server_default="tfidf-agglomerative-v1",
            )
        )
        batch_op.add_column(
            sa.Column("similarity_threshold", sa.Float(), nullable=False, server_default="0.15")
        )
        batch_op.add_column(
            sa.Column("total_volume", sa.BigInteger(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("median_volume", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("weighted_growth", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("median_competition", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("median_bid", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("keyword_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_foreign_key(
            "fk_clusters_discovery_run_id",
            "discovery_runs",
            ["discovery_run_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_clusters_discovery_run_id", ["discovery_run_id"])
        batch_op.create_check_constraint("ck_clusters_keyword_count", "keyword_count >= 0")
        batch_op.create_check_constraint("ck_clusters_total_volume", "total_volume >= 0")
        batch_op.create_check_constraint(
            "ck_clusters_similarity_threshold",
            "similarity_threshold >= 0 AND similarity_threshold <= 1",
        )


def downgrade() -> None:
    with op.batch_alter_table("clusters") as batch_op:
        batch_op.drop_constraint("ck_clusters_similarity_threshold", type_="check")
        batch_op.drop_constraint("ck_clusters_total_volume", type_="check")
        batch_op.drop_constraint("ck_clusters_keyword_count", type_="check")
        batch_op.drop_index("ix_clusters_discovery_run_id")
        batch_op.drop_constraint("fk_clusters_discovery_run_id", type_="foreignkey")
        batch_op.drop_column("keyword_count")
        batch_op.drop_column("median_bid")
        batch_op.drop_column("median_competition")
        batch_op.drop_column("weighted_growth")
        batch_op.drop_column("median_volume")
        batch_op.drop_column("total_volume")
        batch_op.drop_column("similarity_threshold")
        batch_op.drop_column("algorithm_version")
        batch_op.drop_column("discovery_run_id")
