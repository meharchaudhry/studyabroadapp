"""Restore profile sync tables

Revision ID: 8b4d7f1c2a6e
Revises: 7d91b7b13011
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b4d7f1c2a6e'
down_revision: Union[str, Sequence[str], None] = '7d91b7b13011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_degrees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('degree_level', sa.String(), nullable=True),
        sa.Column('specialization', sa.String(), nullable=True),
        sa.Column('cgpa', sa.Float(), nullable=True),
        sa.Column('institution', sa.String(), nullable=True),
        sa.Column('year_graduated', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_degrees_id'), 'user_degrees', ['id'], unique=False)
    op.create_index(op.f('ix_user_degrees_user_id'), 'user_degrees', ['user_id'], unique=False)

    op.create_table(
        'user_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('test_date', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_tests_id'), 'user_tests', ['id'], unique=False)
    op.create_index(op.f('ix_user_tests_user_id'), 'user_tests', ['user_id'], unique=False)

    op.add_column('users', sa.Column('career_goal', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_environment', sa.String(), nullable=True))
    op.add_column('users', sa.Column('study_priority', sa.String(), nullable=True))
    op.add_column('users', sa.Column('learning_style', sa.String(), nullable=True))
    op.add_column('users', sa.Column('living_preference', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'living_preference')
    op.drop_column('users', 'learning_style')
    op.drop_column('users', 'study_priority')
    op.drop_column('users', 'preferred_environment')
    op.drop_column('users', 'career_goal')

    op.drop_index(op.f('ix_user_tests_user_id'), table_name='user_tests')
    op.drop_index(op.f('ix_user_tests_id'), table_name='user_tests')
    op.drop_table('user_tests')

    op.drop_index(op.f('ix_user_degrees_user_id'), table_name='user_degrees')
    op.drop_index(op.f('ix_user_degrees_id'), table_name='user_degrees')
    op.drop_table('user_degrees')