from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
import shapely
from pydantic import model_validator
from typing import TYPE_CHECKING
from app.projects.models import Project
from app.config import config

if TYPE_CHECKING:
    from app.plots.models import Plot
    from app.sensors.models import Sensor
    from app.soil.profiles.models import SoilProfile


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


class AreaRead(AreaBase):
    id: UUID  # We use the UUID as the return ID
    geom: Any | None = None
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
    pass


class AreaUpdate(AreaBase):
    pass
