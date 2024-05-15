"""Add last_updated to models

Revision ID: 182698c00e97
Revises: ae31aa270f11
Create Date: 2024-05-15 11:45:45.105125

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "182698c00e97"
down_revision: Union[str, None] = "ae31aa270f11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "area",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "plot",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "plotsample", sa.Column("created_on", sa.Date(), nullable=True)
    )
    op.add_column(
        "plotsample",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "project",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "sensor",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "soilprofile",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    op.add_column(
        "soiltype",
        sa.Column(
            "last_updated",
            sa.DateTime(),
            nullable=False,
            server_default=func.now(),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("soiltype", "last_updated")
    op.drop_column("soilprofile", "last_updated")
    op.drop_column("sensor", "last_updated")
    op.drop_column("project", "last_updated")
    op.drop_column("plotsample", "last_updated")
    op.drop_column("plotsample", "created_on")
    op.drop_column("plot", "last_updated")
    op.drop_column("area", "last_updated")
    # ### end Alembic commands ###
