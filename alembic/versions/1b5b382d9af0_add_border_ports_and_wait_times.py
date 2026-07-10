"""add border ports and wait times

Revision ID: 1b5b382d9af0
Revises: 85a7ad8991ad
Create Date: 2026-07-09 16:52:36.704811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b5b382d9af0'
down_revision: Union[str, Sequence[str], None] = '85a7ad8991ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "border_ports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("port_number", sa.String(), nullable=False),
        sa.Column("border", sa.String(), nullable=True),
        sa.Column("port_name", sa.String(), nullable=True),
        sa.Column("hours", sa.String(), nullable=True),
        sa.Column("port_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_border_ports_id"), "border_ports", ["id"], unique=False)
    op.create_index(
        op.f("ix_border_ports_port_number"),
        "border_ports",
        ["port_number"],
        unique=True,
    )

    op.create_table(
        "wait_times",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operational_status", sa.String(), nullable=True),
        sa.Column("update_time", sa.String(), nullable=True),
        sa.Column("delay_minutes", sa.Integer(), nullable=True),
        sa.Column("lanes_open", sa.Integer(), nullable=True),
        sa.Column(
            "primary_lane_type",
            sa.Enum(
                "COMMERCIAL_LANE",
                "VEHICLE_LANE",
                "PEDESTRIAN_LANE",
                name="primarylanetype",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "secondary_lane_type",
            sa.Enum(
                "STANDARD_LANE",
                "READY_LANE",
                "NEXUS_LANE",
                "FAST_LANE",
                name="secondarylanetype",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wait_times_id"), "wait_times", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_wait_times_id"), table_name="wait_times")
    op.drop_table("wait_times")
    op.drop_index(op.f("ix_border_ports_port_number"), table_name="border_ports")
    op.drop_index(op.f("ix_border_ports_id"), table_name="border_ports")
    op.drop_table("border_ports")
