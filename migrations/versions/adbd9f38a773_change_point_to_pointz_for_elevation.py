"""Change POINT to POINTZ for elevation

Revision ID: adbd9f38a773
Revises: c74a1a3e6885
Create Date: 2024-04-09 16:45:45.463655

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "adbd9f38a773"
down_revision: Union[str, None] = "c74a1a3e6885"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "sensor",
        "geom",
        existing_type=Geometry(
            geometry_type="POINT",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        type_=Geometry(
            geometry_type="POINTZ",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        existing_nullable=True,
    )
    op.add_column(
        "soilprofile",
        sa.Column(
            "description_horizon",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "soilprofile",
        sa.Column(
            "vegetation_type",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "soilprofile", sa.Column("aspect", sa.Float(), nullable=True)
    )
    op.add_column("soilprofile", sa.Column("slope", sa.Float(), nullable=True))
    op.add_column(
        "soilprofile",
        sa.Column(
            "lythology_surficial_deposit",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.alter_column(
        "soilprofile",
        "geom",
        existing_type=Geometry(
            geometry_type="POINT",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        type_=Geometry(
            geometry_type="POINTZ",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        existing_nullable=True,
    )
    op.drop_column("soilprofile", "description")


def downgrade() -> None:
    op.add_column(
        "soilprofile",
        sa.Column(
            "description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.alter_column(
        "soilprofile",
        "geom",
        existing_type=Geometry(
            geometry_type="POINTZ",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        type_=Geometry(
            geometry_type="POINT",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        existing_nullable=True,
    )
    op.drop_column("soilprofile", "lythology_surficial_deposit")
    op.drop_column("soilprofile", "slope")
    op.drop_column("soilprofile", "aspect")
    op.drop_column("soilprofile", "vegetation_type")
    op.drop_column("soilprofile", "description_horizon")
    op.alter_column(
        "sensor",
        "geom",
        existing_type=Geometry(
            geometry_type="POINTZ",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        type_=Geometry(
            geometry_type="POINT",
            srid=2056,
            from_text="ST_GeomFromEWKT",
            name="geometry",
            _spatial_index_reflected=True,
        ),
        existing_nullable=True,
    )
