"""add user visa checklists table

Revision ID: 7d91b7b13011
Revises: 3c9f58d8f91f
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d91b7b13011"
down_revision: Union[str, Sequence[str], None] = "3c9f58d8f91f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_visa_checklists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("checklist_type", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("items_json", sa.Text(), nullable=False),
        sa.Column("checked_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "country", "checklist_type", name="uq_user_country_checklist_type"),
    )
    op.create_index(op.f("ix_user_visa_checklists_id"), "user_visa_checklists", ["id"], unique=False)
    op.create_index(op.f("ix_user_visa_checklists_user_id"), "user_visa_checklists", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_visa_checklists_country"), "user_visa_checklists", ["country"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_user_visa_checklists_country"), table_name="user_visa_checklists")
    op.drop_index(op.f("ix_user_visa_checklists_user_id"), table_name="user_visa_checklists")
    op.drop_index(op.f("ix_user_visa_checklists_id"), table_name="user_visa_checklists")
    op.drop_table("user_visa_checklists")
