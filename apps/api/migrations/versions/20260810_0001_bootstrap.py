"""Create the Stage 1 migration baseline.

Revision ID: 20260810_0001
Revises:
Create Date: 2026-08-10
"""

from collections.abc import Sequence

revision: str = "20260810_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the migration baseline; Stage 2 introduces domain tables."""


def downgrade() -> None:
    """Remove the empty migration baseline."""

