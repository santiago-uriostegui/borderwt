"""create border_time_imports table

Revision ID: 60cbd78cb9a5
Revises: a9abc59d2bea
Create Date: 2026-07-09 18:15:21.756557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60cbd78cb9a5'
down_revision: Union[str, Sequence[str], None] = 'a9abc59d2bea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "border_time_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("borderport_total", sa.Integer(), nullable=False),
        sa.Column("waittime_total", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_border_time_imports_id"), "border_time_imports", ["id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_border_time_imports_id"), table_name="border_time_imports")
    op.drop_table("border_time_imports")
