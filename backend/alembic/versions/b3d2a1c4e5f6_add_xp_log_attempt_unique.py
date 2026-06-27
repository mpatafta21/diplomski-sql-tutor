"""add partial-unique index on xp_log.attempt_id (idempotencija XP-a po attemptu)

Partial unique: blokira dvostruki XP red za isti attempt_id, ali dopušta više
redova s attempt_id IS NULL (badge-rewardi nemaju attempt_id).

Revision ID: b3d2a1c4e5f6
Revises: 158909aa016b
Create Date: 2026-06-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3d2a1c4e5f6'
down_revision: Union[str, Sequence[str], None] = '158909aa016b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEX_NAME = "uq_xp_log_attempt_id"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        _INDEX_NAME,
        "xp_log",
        ["attempt_id"],
        unique=True,
        postgresql_where="attempt_id IS NOT NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(_INDEX_NAME, table_name="xp_log")
