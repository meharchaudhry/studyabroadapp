"""add_career_lifestyle_fields

Revision ID: f1a2b3c4d5e6
Revises: ebe6c6559505
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'ebe6c6559505'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('career_goal', sa.String(), nullable=True))
    op.add_column('users', sa.Column('study_priority', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_environment', sa.String(), nullable=True))
    op.add_column('users', sa.Column('learning_style', sa.String(), nullable=True))
    op.add_column('users', sa.Column('living_preference', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'living_preference')
    op.drop_column('users', 'learning_style')
    op.drop_column('users', 'preferred_environment')
    op.drop_column('users', 'study_priority')
    op.drop_column('users', 'career_goal')
