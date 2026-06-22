"""add source_id to tasks

Revision ID: ccea7b154aec
Revises: ac6a5eeac6e5
Create Date: 2026-06-22 22:40:18.006260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccea7b154aec'
down_revision: Union[str, Sequence[str], None] = 'ac6a5eeac6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('source_id', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_tasks_source_id', 'tasks', ['source_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_tasks_source_id', 'tasks', type_='unique')
    op.drop_column('tasks', 'source_id')
