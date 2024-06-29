from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
from pydantic import model_validator
from typing import TYPE_CHECKING
from app.projects.models import Project
from app.config import config
from sqlalchemy.sql import func
from app.sensors.models import Sensor, SensorRead
from app.plots.models import Plot, PlotRead
import shapely
import datetime
import pyproj

if TYPE_CHECKING:
    from app.soil.profiles.models import SoilProfile, SoilProfileRead
    from app.transects.models.transects import Transect


class AreaBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
        nullable=False,
    )
    description: str | None = Field(
        default=None,
        nullable=True,
    )
    project_id: UUID = Field(
        nullable=False, index=True, foreign_key="project.id"
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


class Area(AreaBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint("name", "project_id", name="name_project_id"),
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
    sensors: list["Sensor"] = Relationship(
        back_populates="area",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    project: Project = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
        back_populates="areas",
    )

    plots: list["Plot"] = Relationship(
        back_populates="area",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    soil_profiles: list["SoilProfile"] = Relationship(
        back_populates="area",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    transects: list["Transect"] = Relationship(
        back_populates="area",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class GenericNameIDModel(SQLModel):
    name: str
    id: UUID


class GenericNameIDPointModel(GenericNameIDModel):
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    coord_srid: int | None = None

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: Any,
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


class AreaRead(AreaBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any | None = None
    project: Project

    soil_profiles: list[GenericNameIDPointModel] = []
    plots: list[GenericNameIDPointModel] = []
    sensors: list[GenericNameIDPointModel] = []
    transects: list[Any] = []

    @model_validator(mode="after")
    def convert_wkb_to_json(cls, values: Any) -> Any:
        """Convert the WKBElement to a shapely mapping"""

        if isinstance(values.geom, WKBElement):

            values.geom = shapely.geometry.mapping(
                shapely.wkb.loads(str(values.geom))
            )
        return values


class AreaCreate(AreaBase):
    pass


class AreaUpdate(AreaBase):
    pass
