"""add_user_profile_fields_and_appointments

Revision ID: a1b2c3d4e5f6
Revises: 22a94df0111d
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '22a94df0111d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extend users table ───────────────────────────────────────────────────────
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('field_of_study', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_degree', sa.String(), nullable=True))
    op.add_column('users', sa.Column('english_score', sa.Float(), nullable=True))

    # ── Extend universities table ────────────────────────────────────────────────
    op.add_column('universities', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('universities', sa.Column('acceptance_rate', sa.Float(), nullable=True))
    op.add_column('universities', sa.Column('intake_months', sa.ARRAY(sa.String()), nullable=True))

    # ── Create appointments table ────────────────────────────────────────────────
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('consultation_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), server_default='30'),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('appointments')
    op.drop_column('universities', 'intake_months')
    op.drop_column('universities', 'acceptance_rate')
    op.drop_column('universities', 'description')
    op.drop_column('users', 'english_score')
    op.drop_column('users', 'preferred_degree')
    op.drop_column('users', 'field_of_study')
    op.drop_column('users', 'full_name')
