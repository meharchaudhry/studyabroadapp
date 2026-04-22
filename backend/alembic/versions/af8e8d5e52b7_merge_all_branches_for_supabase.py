"""merge_all_branches_for_supabase

Revision ID: af8e8d5e52b7
Revises: 3c9f58d8f91f, f1a2b3c4d5e6
Create Date: 2026-04-22 17:52:23.189548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af8e8d5e52b7'
down_revision: Union[str, Sequence[str], None] = ('3c9f58d8f91f', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
