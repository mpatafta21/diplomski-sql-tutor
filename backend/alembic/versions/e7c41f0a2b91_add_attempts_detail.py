"""add attempts.detail

Faza 4.3 Stage 0b: nullable TEXT kolona za EvaluationOutcome.detail —
Coordinator gradi feedback iz attempts reda pa detail pripada tamo.
Bez backfilla: postojeći redovi ostaju NULL (legitimno — detail nije
bio persistiran prije ove migracije).

Revision ID: e7c41f0a2b91
Revises: 9dbaef3db432
Create Date: 2026-07-13 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c41f0a2b91'
down_revision: Union[str, Sequence[str], None] = '9dbaef3db432'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('attempts', sa.Column('detail', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('attempts', 'detail')
