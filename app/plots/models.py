import shapely
import datetime
import pyproj
from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4
from app.soil.types.models import SoilType
from app.areas.models import Area, AreaRead
from app.config import config
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.plots.samples.models import PlotSample


class PlotBase(SQLModel):
    name: str = Field(
        index=True,
    )
    plot_iterator: int = Field(
        description=(
            "The ID given by the scientist to the plot and forms part "
            "of the field ID. ie. 1 will become the 1 in BF01"
        ),
        default=None,
        index=True,
    )
    area_id: UUID = Field(
        nullable=False,
        index=True,
        foreign_key="area.id",
    )
    gradient: str = Field(
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
    created_on: datetime.date | None = Field(
        None,
    )
    slope: str | None = Field(
        default=None,
    )
    weather: str | None = Field(
        default=None,
    )
    lithology: str | None = Field(
        default=None,
    )
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )


class Plot(PlotBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint(
            "plot_iterator",
            "area_id",
            "gradient",
            name="unique_plot",
        ),
        UniqueConstraint(
            "name",
            name="unique_plot_name",
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
        default=None, sa_column=Column(Geometry("POINTZ", srid=config.SRID))
    )
    area: Area = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
        back_populates="plots",
    )
    samples: list["PlotSample"] = Relationship(
        back_populates="plot",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class PlotRead(PlotBase):
    id: UUID
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None
    latitude: float | None = None
    longitude: float | None = None

    area: AreaRead

    name: str | None = None

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

                    # Set the latitude and longitude by reprojecting to WGS84
                    transformer = pyproj.Transformer.from_crs(
                        f"EPSG:{str(config.SRID)}", "EPSG:4326", always_xy=True
                    )
                    values.longitude, values.latitude, _ = (
                        transformer.transform(
                            values.coord_x, values.coord_y, values.coord_z
                        )
                    )

        elif isinstance(values.geom, dict):
            if values.geom is not None:
                values.coord_x = values.geom["coordinates"][0]
                values.coord_y = values.geom["coordinates"][1]
                values.coord_z = values.geom["coordinates"][2]
                values.geom = values.geom

                # Set the latitude and longitude by reprojecting to WGS84
                transformer = pyproj.Transformer.from_crs(
                    f"EPSG:{str(config.SRID)}", "EPSG:4326", always_xy=True
                )
                values.longitude, values.latitude, _ = transformer.transform(
                    values.coord_x, values.coord_y, values.coord_z
                )

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

    name: str | None = None  # Set null to allow endpoint func to gen. name

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


class PlotCreateBatch(SQLModel):
    attachment: str  # Base64 encoded attachment


class PlotCreateBatchRead(SQLModel):
    success: bool
    message: str
    errors: list[Any] = []
    qty_added: int
