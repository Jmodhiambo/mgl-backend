"""Merge multiple heads

Revision ID: 8572d0d0125b
Revises: 610ad9891c11, 797fce54b88b, 991de3b3599a
Create Date: 2026-05-25 04:46:36.590612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8572d0d0125b'
down_revision: Union[str, Sequence[str], None] = ('610ad9891c11', '797fce54b88b', '991de3b3599a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
