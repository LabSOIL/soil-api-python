from sqlmodel import SQLModel, Field, Column, Relationship, UniqueConstraint
from geoalchemy2 import Geometry, WKBElement
from uuid import uuid4, UUID
from typing import Any
from pydantic import model_validator
import shapely
from typing import TYPE_CHECKING
import datetime
import pyproj
from app.config import config
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.areas.models import Area


class SensorBase(SQLModel):
    name: str | None = Field(default=None, index=True)
    description: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    serial_number: str | None = Field(default=None)
    manufacturer: str | None = Field(default=None)
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )


class Sensor(SensorBase, table=True):
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

    geom: Any = Field(sa_column=Column(Geometry("POINTZ", srid=config.SRID)))
    area_id: UUID = Field(default=None, foreign_key="area.id")

    area: "Area" = Relationship(
        back_populates="sensors", sa_relationship_kwargs={"lazy": "selectin"}
    )
    data: list["SensorData"] = Relationship(
        back_populates="sensor",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SensorDataBase(SQLModel):
    """Matching the data structure from the Tomst TMS data logger
    https://tomst.com/web/en/systems/tms/data/

    Where the date structure is as follows:
    0;31.10.2013 11:45;0;21.5625;22.0625;23.125;148;1;0

    0 	                index of the measure
    31.10.2013 11:45    date and time in UTC
    0 	                time zone
    21.5625 	        T1
    22.0625             T2
    23.125              T3
    148 	            soil moisture count (raw moisture data)
    1 	                shake
    0 	                errFlag
    """

    instrument_seq: int = Field(  # The iterator integer in the instrument
        index=True,
        nullable=False,
    )
    time_utc: datetime.datetime = Field(
        index=True,
        nullable=False,
    )
    time_zone: int | None = Field(
        index=False,
        nullable=True,
    )
    temperature_1: float | None = Field(
        index=True,
        nullable=True,
    )
    temperature_2: float | None = Field(
        index=True,
        nullable=True,
    )
    temperature_3: float | None = Field(
        index=True,
        nullable=True,
    )
    soil_moisture_count: float | None = Field(
        index=True,
        nullable=True,
    )
    shake: int | None = Field(
        index=False,
        nullable=True,
    )
    error_flat: int | None = Field(
        index=False,
        nullable=True,
    )

    sensor_id: UUID = Field(
        default=None,
        foreign_key="sensor.id",
        nullable=False,
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


class SensorData(SensorDataBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint("instrument_seq", "sensor_id"),
        UniqueConstraint("time_utc", "sensor_id"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )

    sensor: Sensor = Relationship(
        back_populates="data",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SensorDataRead(SensorDataBase):
    id: UUID
    sensor: Any


class SensorRead(SensorBase):
    id: UUID
    area_id: UUID
    geom: Any | None
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None

    area: Any | None = None

    @model_validator(mode="after")
    def convert_wkb_to_x_y(
        cls,
        values: "SensorRead",
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


class SensorDataSummary(SQLModel):
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    qty_records: int | None = None


class SensorReadWithDataSummary(SensorRead):
    data: SensorDataSummary


class SensorReadWithDataSummaryAndPlot(SensorRead):
    data: SensorDataSummary | None
    temperature_plot: list[SensorDataRead] | None = None


class SensorCreate(SensorBase):
    area_id: UUID
    coord_y: float
    coord_x: float
    coord_z: float

    latitude: float | None = None
    longitude: float | None = None

    geom: Any | None = None
    data_base64: str | None = None  # Base64 encoded CSV data

    @model_validator(mode="after")
    def convert_x_y_to_wkt(cls, values: Any) -> Any:
        """Convert the X and Y coordinates to a WKT geometry"""

        # Convert coordinates to WKT geom. Prioritize x and y, then lat and lon
        # Conversion from 4326 to Swiss coordinates
        if values.coord_y and values.coord_x:
            point = shapely.geometry.Point(
                values.coord_x, values.coord_y, values.coord_z
            )
            values.geom = point.wkt
        elif values.latitude and values.longitude:
            # If no x and y, try lat and lon. Convert to Swiss coordinates
            pyproj_crs = pyproj.CRS("EPSG:4326")
            pyproj_crs_swiss = pyproj.CRS(f"EPSG:{str(config.SRID)}")
            project = pyproj.Transformer.from_crs(
                pyproj_crs, pyproj_crs_swiss, always_xy=True
            ).transform
            values.coord_x, values.coord_y = project(
                values.latitude, values.longitude
            )
            point = shapely.geometry.Point(
                values.coord_x, values.coord_y, values.coord_z
            )
            values.geom = point.wkt
        else:
            values.geom = None

        return values


class SensorUpdate(SensorCreate):
    data_base64: str | None = None  # Base64 encoded CSV data
