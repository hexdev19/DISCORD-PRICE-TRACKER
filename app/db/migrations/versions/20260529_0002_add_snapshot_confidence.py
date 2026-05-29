"""add snapshot confidence

Revision ID: 0002_snapshot_confidence
Revises: 0001_initial
Create Date: 2026-05-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_snapshot_confidence"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("price_snapshots", sa.Column("confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("price_snapshots", "confidence")
