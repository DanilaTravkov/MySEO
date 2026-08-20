"""Add search monitors, scheduled discovery runs, and derived change signals.

Revision ID: 20260820_0006
Revises: 20260820_0005
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0006"
down_revision: str | None = "20260820_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "search_monitors",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("geo", sa.String(length=16), nullable=False),
        sa.Column("seeds_json", sa.JSON(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "frequency IN ('manual', 'monthly')",
            name="ck_search_monitors_frequency",
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_search_monitors_workspace_id",
        "search_monitors",
        ["workspace_id"],
    )
    op.create_index(
        "ix_search_monitors_next_run_at",
        "search_monitors",
        ["next_run_at"],
    )

    with op.batch_alter_table("discovery_runs") as batch_op:
        batch_op.add_column(sa.Column("monitor_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("trigger", sa.String(length=16), nullable=False, server_default="manual")
        )
        batch_op.add_column(sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            "fk_discovery_runs_monitor_id",
            "search_monitors",
            ["monitor_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_discovery_runs_monitor_id", ["monitor_id"])
        batch_op.create_check_constraint(
            "ck_discovery_runs_trigger",
            "trigger IN ('manual', 'scheduled')",
        )
        batch_op.create_unique_constraint(
            "uq_discovery_runs_monitor_scheduled_for",
            ["monitor_id", "scheduled_for"],
        )

    op.create_table(
        "monitor_signals",
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column("previous_run_id", sa.Uuid(), nullable=True),
        sa.Column("current_run_id", sa.Uuid(), nullable=False),
        sa.Column("signal_type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("entity_key", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("magnitude", sa.Float(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "signal_type IN ('new_keyword', 'demand_growth', 'demand_decline', "
            "'competition_shift', 'new_cluster', 'opportunity_shift')",
            name="ck_monitor_signals_type",
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_monitor_signals_severity",
        ),
        sa.ForeignKeyConstraint(
            ["monitor_id"], ["search_monitors.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["previous_run_id"], ["discovery_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["current_run_id"], ["discovery_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitor_signals_monitor_id", "monitor_signals", ["monitor_id"])
    op.create_index(
        "ix_monitor_signals_previous_run_id",
        "monitor_signals",
        ["previous_run_id"],
    )
    op.create_index(
        "ix_monitor_signals_current_run_id",
        "monitor_signals",
        ["current_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_monitor_signals_current_run_id", table_name="monitor_signals")
    op.drop_index("ix_monitor_signals_previous_run_id", table_name="monitor_signals")
    op.drop_index("ix_monitor_signals_monitor_id", table_name="monitor_signals")
    op.drop_table("monitor_signals")

    with op.batch_alter_table("discovery_runs") as batch_op:
        batch_op.drop_constraint(
            "uq_discovery_runs_monitor_scheduled_for", type_="unique"
        )
        batch_op.drop_constraint("ck_discovery_runs_trigger", type_="check")
        batch_op.drop_index("ix_discovery_runs_monitor_id")
        batch_op.drop_constraint("fk_discovery_runs_monitor_id", type_="foreignkey")
        batch_op.drop_column("scheduled_for")
        batch_op.drop_column("trigger")
        batch_op.drop_column("monitor_id")

    op.drop_index("ix_search_monitors_next_run_at", table_name="search_monitors")
    op.drop_index("ix_search_monitors_workspace_id", table_name="search_monitors")
    op.drop_table("search_monitors")
