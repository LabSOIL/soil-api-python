from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship, Column
from typing import TYPE_CHECKING, Any
from uuid import uuid4, UUID
import datetime
import shapely


if TYPE_CHECKING:
    from app.soil.types.models import SoilType


class SoilProfileBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
    )
    description_horizon: str | None = Field(
        default=None,
    )
    weather: str | None = Field(
        default=None,
    )
    topography: str | None = Field(
        default=None,
    )
    vegetation_type: str | None = Field(
        default=None,
    )
    aspect: float | None = Field(
        default=None,
    )
    slope: float | None = Field(
        default=None,
    )
    lythology_surficial_deposit: str | None = Field(
        default=None,
    )
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    soil_type_id: UUID = Field(
        foreign_key="soiltype.id",
        default=None,
        index=True,
    )


class SoilProfile(SoilProfileBase, table=True):
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
    geom: Any = Field(
        default=None, sa_column=Column(Geometry("POINTZ", srid=2056))
    )

    soil_type: "SoilType" = Relationship(
        back_populates="soil_profiles",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SoilProfileRead(SoilProfileBase):
    id: UUID
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: "SoilProfileRead",
    ) -> dict:
        """Form the geometry from the X and Y coordinates"""

        if isinstance(values.geom, WKBElement):
            if values.geom is not None:
                shapely_obj = shapely.wkb.loads(str(values.geom))
                if shapely_obj is not None:
                    mapping = shapely.geometry.mapping(shapely_obj)
                    values.coord_srid = values.geom.srid
                    values.coord_x = mapping["coordinates"][1]
                    values.coord_y = mapping["coordinates"][0]
                    values.coord_z = mapping["coordinates"][2]
                    values.geom = mapping
        elif isinstance(values.geom, dict):
            if values.geom is not None:
                values.coord_y = values.geom["coordinates"][0]
                values.coord_x = values.geom["coordinates"][1]
                values.coord_z = values.geom["coordinates"][2]
                values.geom = values.geom
        else:
            values.coord_x = None
            values.coord_y = None
            values.coord_z = None

        return values


class SoilProfileCreate(SoilProfileBase):
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


class SoilProfileUpdate(SoilProfileBase):
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
