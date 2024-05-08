from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
import shapely
from pydantic import model_validator
from typing import TYPE_CHECKING
from app.sensors.models import SensorRead
from app.projects.models import Project
import pyproj

if TYPE_CHECKING:
    from app.plots.models import Plot
    from app.sensors.models import Sensor
    from app.soil.profiles.models import SoilProfile


class AreaBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str
    project_id: UUID = Field(
        nullable=False, index=True, foreign_key="project.id"
    )


class Area(AreaBase, table=True):
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
    geom: Any = Field(sa_column=Column(Geometry("POLYGON", srid=2056)))

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


class AreaRead(AreaBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any
    project: Project

    @model_validator(mode="after")
    def convert_wkb_to_json(cls, values: Any) -> Any:
        """Convert the WKBElement to a shapely mapping"""

        if isinstance(values.geom, WKBElement):

            values.geom = shapely.geometry.mapping(
                shapely.wkb.loads(str(values.geom))
            )
        return values


class AreaCreate(AreaBase):
    geom: Any

    @model_validator(mode="after")
    def convert_json_to_wkt(cls, values: Any) -> Any:
        """Convert the WKBElement to a shapely mapping"""

        if isinstance(values.geom, list):
            polygon = shapely.geometry.Polygon(values.geom)
            oriented_polygon = shapely.geometry.polygon.orient(
                polygon, sign=1.0
            )
            values.geom = oriented_polygon.wkt

        return values


class AreaUpdate(AreaBase):
    pass
