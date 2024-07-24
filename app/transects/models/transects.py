from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
import datetime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Any
from app.transects.models.nodes import TransectNode
from pydantic import model_validator
import shapely
import pyproj
from geoalchemy2 import WKBElement
from app.config import config

if TYPE_CHECKING:
    from app.plots.models import Plot
    from app.areas.models import Area


class TransectBase(SQLModel):
    name: str | None = Field(
        default=None,
        index=True,
        nullable=True,
    )
    description: str | None = Field(
        default=None,
    )
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
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
    area_id: UUID = Field(
        nullable=False,
        index=True,
        foreign_key="area.id",
    )


class Transect(TransectBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
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

    nodes: list["Plot"] = Relationship(
        back_populates="transects",
        sa_relationship_kwargs={"lazy": "selectin"},
        link_model=TransectNode,
    )
    area: "Area" = Relationship(
        back_populates="transects",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class PlotSimple(SQLModel):
    # We only need the id of the plot
    id: UUID
    name: str | None = None
    geom: Any
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    coord_srid: int | None = None

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: "PlotSimple",
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


class TransectRead(TransectBase):
    id: UUID
    nodes: list[PlotSimple]
    area: Any


class TransectCreate(TransectBase):
    nodes: list[PlotSimple]


class TransectUpdate(TransectBase):
    pass
