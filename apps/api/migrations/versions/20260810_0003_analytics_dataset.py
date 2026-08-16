"""Associate analytics with discovery datasets and update recommendations.

Revision ID: 20260810_0003
Revises: 20260810_0002
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_0003"
down_revision: str | None = "20260810_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("keyword_observations") as batch_op:
        batch_op.add_column(sa.Column("discovery_run_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_keyword_observations_discovery_run_id",
            "discovery_runs",
            ["discovery_run_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_keyword_observations_discovery_run_id",
            ["discovery_run_id"],
        )

    op.execute(
        sa.text(
            """
            UPDATE keyword_observations
            SET discovery_run_id = (
                SELECT discovery_runs.id
                FROM discovery_runs
                WHERE discovery_runs.provider = keyword_observations.provider
                ORDER BY discovery_runs.started_at DESC
                LIMIT 1
            )
            WHERE discovery_run_id IS NULL
            """
        )
    )

    with op.batch_alter_table("keyword_analyses") as batch_op:
        batch_op.add_column(sa.Column("discovery_run_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_keyword_analyses_discovery_run_id",
            "discovery_runs",
            ["discovery_run_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_keyword_analyses_discovery_run_id", ["discovery_run_id"])

    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_constraint("ck_opportunities_recommendation", type_="check")
        batch_op.create_check_constraint(
            "ck_opportunities_recommendation",
            "recommendation IN ('IGNORE', 'WATCH', 'INVESTIGATE', 'STRONG', 'BUILD')",
        )


def downgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_constraint("ck_opportunities_recommendation", type_="check")
        batch_op.create_check_constraint(
            "ck_opportunities_recommendation",
            "recommendation IN ('build', 'consider', 'skip')",
        )

    with op.batch_alter_table("keyword_analyses") as batch_op:
        batch_op.drop_index("ix_keyword_analyses_discovery_run_id")
        batch_op.drop_constraint("fk_keyword_analyses_discovery_run_id", type_="foreignkey")
        batch_op.drop_column("discovery_run_id")

    with op.batch_alter_table("keyword_observations") as batch_op:
        batch_op.drop_index("ix_keyword_observations_discovery_run_id")
        batch_op.drop_constraint("fk_keyword_observations_discovery_run_id", type_="foreignkey")
        batch_op.drop_column("discovery_run_id")
