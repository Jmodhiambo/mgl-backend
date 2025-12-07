"""several table updates

Revision ID: 09cfa1f7b1ed
Revises: 54b350d51ff7
Create Date: 2025-12-07 07:20:30.611679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09cfa1f7b1ed'
down_revision: Union[str, Sequence[str], None] = '54b350d51ff7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
