"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-04
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

import app.models  # noqa: F401
from app.extensions import Base

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
