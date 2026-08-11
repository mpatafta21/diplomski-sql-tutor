"""faza-5: hint_requests + attempts.sqlstate + CHECK error_type

Revision ID: 15a84352666f
Revises: e7c41f0a2b91
Create Date: 2026-08-11 16:40:48.769108

Faza 5.0, sekcija B. Tri promjene, sve u jednoj reviziji:

1. ``hint_requests`` — 17. tablica. Telemetrija zahtjeva za hintom; nosi izračun
   limita (5 hintova, +1 svaka 4 h, računato pri čitanju, bez crona).
2. ``attempts.sqlstate`` — VARCHAR(5) NULL, ostaje PRAZAN u 5.0. Puni ga 5.1.
   Odluka A1-dop-1: SQLSTATE je jedini signal koji ``execution_error`` smije
   poslati LLM-u, jer sirovi ``detail`` ondje nosi doslovni redak studentovog
   upita (izmjereno, docs/faza-5-korak-0.md §A1).
3. ``ck_attempts_error_type_when_incorrect`` — netočan pokušaj mora nositi tip
   greške. Provjera A2 je prošla nad svim piscima: 0 redaka u živoj bazi krši
   uvjet, svi testni pisci postavljaju tip.

🔴 CHECK-ovi se pišu RUČNO — Alembic autogenerate ih ne detektira.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15a84352666f'
down_revision: Union[str, Sequence[str], None] = 'e7c41f0a2b91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('hint_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('after_attempt_id', sa.Integer(), nullable=False),
    sa.Column('error_type', sa.String(length=100), nullable=False),
    sa.Column('source', sa.String(length=16), nullable=False),
    sa.Column('hint_id', sa.Integer(), nullable=True),
    sa.Column('hint_text', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("source = 'unavailable' OR hint_text IS NOT NULL", name='ck_hint_requests_text_or_unavailable'),
    sa.CheckConstraint("source IN ('llm', 'fallback', 'unavailable')", name='ck_hint_requests_source'),
    sa.ForeignKeyConstraint(['after_attempt_id'], ['attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['hint_id'], ['hints.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'idx_hint_requests_user_created',
        'hint_requests',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
    )
    op.add_column('attempts', sa.Column('sqlstate', sa.String(length=5), nullable=True))

    # Ručno (autogenerate ne vidi CHECK-ove). Postojeći redci su provjereni u A2:
    # 13 netočnih, svi s error_type; 21 točan, svi bez njega → 0 kršenja.
    op.create_check_constraint(
        'ck_attempts_error_type_when_incorrect',
        'attempts',
        'is_correct = true OR error_type IS NOT NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'ck_attempts_error_type_when_incorrect', 'attempts', type_='check'
    )
    op.drop_column('attempts', 'sqlstate')
    op.drop_index('idx_hint_requests_user_created', table_name='hint_requests')
    op.drop_table('hint_requests')
