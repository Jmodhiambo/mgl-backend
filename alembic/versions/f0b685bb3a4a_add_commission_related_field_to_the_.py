"""Add commission related field to the events table

Revision ID: f0b685bb3a4a
Revises: 68bb5b23855a
Create Date: 2026-06-21 00:46:33.663455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0b685bb3a4a'
down_revision: Union[str, Sequence[str], None] = '68bb5b23855a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # commission_rate — NOT NULL, no application-level default. The
    # server_default here is ONLY to backfill existing rows so the ALTER
    # succeeds; it's dropped immediately after so the column has no
    # fallback going forward — every insert must supply this explicitly.
    op.add_column(
        'events',
        sa.Column(
            'commission_rate', sa.Numeric(precision=5, scale=2),
            nullable=False, server_default='7.0',
            comment='Platform fee % locked in at event creation time',
        )
    )
    op.alter_column('events', 'commission_rate', server_default=None)

    # commission_source — NOT NULL, keeps its default ('platform_default')
    # both at the model level and the DB level, so server_default stays.
    op.add_column(
        'events',
        sa.Column(
            'commission_source', sa.String(length=20),
            nullable=False, server_default='platform_default',
            comment='platform_default | negotiated',
        )
    )

    # Nullable columns — no backfill needed.
    op.add_column('events', sa.Column('commission_approved_by', sa.Integer(), nullable=True, comment='Admin user ID who approved a negotiated rate'))
    op.add_column('events', sa.Column('commission_approved_by_name', sa.String(length=100), nullable=True, comment='Denormalised admin display name — avoids a join on every read'))
    op.add_column('events', sa.Column('commission_approved_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when the negotiated rate was approved'))

    op.create_foreign_key(
        'events_commission_approved_by_fkey',
        'events', 'users', ['commission_approved_by'], ['id'], ondelete='SET NULL'
    )
    op.drop_column('events', 'is_active')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('events', sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='true'))
    op.alter_column('events', 'is_active', server_default=None)

    op.drop_constraint('events_commission_approved_by_fkey', 'events', type_='foreignkey')
    op.drop_column('events', 'commission_approved_at')
    op.drop_column('events', 'commission_approved_by_name')
    op.drop_column('events', 'commission_approved_by')
    op.drop_column('events', 'commission_source')
    op.drop_column('events', 'commission_rate')