from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from typing import Any
from uuid import UUID, uuid4
import shapely
import datetime
from app.areas.models import Area, AreaRead
from app.soil.types.models import SoilType


class PlotBase(SQLModel):
    plot_iterator: int = Field(
        description=(
            "The ID given by the scientist to the plot and forms part "
            "of the field ID. ie. 1 will become the 1 in BF01"
        ),
        default=None,
        index=True,
    )
    description_horizon: str | None = Field(
        default=None,
    )
    area_id: UUID = Field(
        nullable=False,
        index=True,
        foreign_key="area.id",
    )
    soil_type_id: UUID | None = Field(
        default=None,
        nullable=True,
        index=True,
        foreign_key="soiltype.id",
    )
    gradient: str | None = Field(
        default=None,
        index=True,
        nullable=False,
    )
    vegetation_type: str | None = Field(
        default=None,
    )
    topography: str | None = Field(
        default=None,
    )
    aspect: str | None = Field(
        default=None,
    )
    created_on: datetime.datetime | None = Field(
        None,
    )
    slope: float | None = Field(
        default=None,
    )


class Plot(PlotBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint(
            "plot_iterator", "area_id", "gradient", name="unique_plot"
        ),
    )
    iterator: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
    )

    geom: Any = Field(
        default=None, sa_column=Column(Geometry("POINTZ", srid=2056))
    )
    area: "Area" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
        back_populates="plots",
    )
    soil_type: "SoilType" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
        back_populates="plots",
    )


class PlotRead(PlotBase):
    id: UUID
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None

    area: AreaRead

    name: str | None = None

    @model_validator(mode="after")
    def create_identifier(cls, values: "PlotRead") -> "PlotRead":
        """Create the identifier

        A combination of the area name, gradient and plot ID

        ie. BF01 is:
            Area: Binntal
            Gradient: Flats
            Plot ID: 01
        """

        values.name = (
            f"{values.area.name.upper()[0]}"
            f"{values.gradient.upper()[0]}{values.plot_iterator:02d}"
        )

        return values

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: "PlotRead",
    ) -> dict:
        """Form the geometry from the X and Y coordinates"""

        if isinstance(values.geom, WKBElement):
            if values.geom is not None:
                shapely_obj = shapely.wkb.loads(str(values.geom))
                if shapely_obj is not None:
                    mapping = shapely.geometry.mapping(shapely_obj)
                    values.coord_srid = values.geom.srid
                    values.coord_x = mapping["coordinates"][0]
                    values.coord_y = mapping["coordinates"][1]
                    values.coord_z = mapping["coordinates"][2]
                    values.geom = mapping
        elif isinstance(values.geom, dict):
            if values.geom is not None:
                values.coord_x = values.geom["coordinates"][0]
                values.coord_y = values.geom["coordinates"][1]
                values.coord_z = values.geom["coordinates"][2]
                values.geom = values.geom
        else:
            values.coord_x = None
            values.coord_y = None
            values.coord_z = None

        return values


class PlotCreate(PlotBase):
    coord_x: float | None
    coord_y: float | None
    coord_z: float | None

    geom: Any | None = None

    @model_validator(mode="after")
    def convert_x_y_to_wkt(cls, values: Any) -> Any:
        """Convert the X and Y coordinates to a WKT geometry"""

        # Encode the SRID into the WKT
        values.geom = shapely.wkt.dumps(
            shapely.geometry.Point(
                values.coord_x, values.coord_y, values.coord_z
            ),
        )

        return values


class PlotUpdate(PlotBase):
    coord_x: float | None
    coord_y: float | None
    coord_z: float | None

    geom: Any | None = None

    @model_validator(mode="after")
    def convert_x_y_to_wkt(cls, values: Any) -> Any:
        """Convert the X and Y coordinates to a WKT geometry"""

        point = shapely.geometry.Point(
            values.coord_x, values.coord_y, values.coord_z
        )
        values.geom = point.wkt

        return values
