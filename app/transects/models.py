from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship, Column
from app.generic.models import ReactAdminDBModel
from typing import TYPE_CHECKING, Any
from uuid import UUID
import datetime
import shapely


class TransectBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
    )
    description: str | None = Field(
        default=None,
    )
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )


class Transect(TransectBase, ReactAdminDBModel, table=True):
    nodes: list["TransectNode"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class TransectRead(TransectBase):
    id: UUID


class TransectCreate(TransectBase):
    pass


class TransectUpdate(TransectBase):
    pass


# Transect Node
class TransectNodeBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
    )
    description: str | None = Field(
        default=None,
    )
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    parent_id: UUID = Field(
        foreign_key="transect.id",
        default=None,
        index=True,
    )


class TransectNode(TransectNodeBase, ReactAdminDBModel, table=True):
    geom: Any = Field(
        default=None, sa_column=Column(Geometry("POINTZ", srid=2056))
    )
    parent_transect: "Transect" = Relationship(
        back_populates="nodes",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class TransectNodeRead(TransectNodeBase):
    id: UUID
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: "TransectNodeRead",
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


class TransectNodeCreate(TransectNodeBase):
    coord_x: float | None
    coord_y: float | None
    coord_z: float | None

    geom: Any | None = None

    @model_validator(mode="after")
    def convert_x_y_to_wkt(
        cls,
        values: "TransectNodeCreate",
    ) -> Any:
        """Convert the X and Y coordinates to a WKT geometry"""

        # Encode the SRID into the WKT
        values.geom = shapely.wkt.dumps(
            shapely.geometry.Point(
                values.coord_x, values.coord_y, values.coord_z
            ),
        )

        return values


class TransectNodeUpdate(TransectNodeBase):
    coord_x: float | None
    coord_y: float | None
    coord_z: float | None

    geom: Any | None = None

    @model_validator(mode="after")
    def convert_x_y_to_wkt(
        cls,
        values: "TransectNodeUpdate",
    ) -> Any:
        """Convert the X and Y coordinates to a WKT geometry"""

        point = shapely.geometry.Point(
            values.coord_x, values.coord_y, values.coord_z
        )
        values.geom = point.wkt

        return values
