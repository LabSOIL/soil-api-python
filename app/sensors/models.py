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

if TYPE_CHECKING:
    from app.areas.models import Area


class SensorBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    elevation: float | None = Field(default=None)
    time_recorded_at_utc: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
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
    time_ingested_at_utc: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True,
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
    instrument_seq: int = Field(  # The iterator integer in the instrument
        index=True,
        nullable=False,
    )
    time: datetime.datetime = Field(
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


class SensorData(SensorDataBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    iterator: int = Field(
        nullable=False,
        primary_key=True,
        index=True,
    )
    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
    )

    sensor_id: UUID = Field(
        default=None, foreign_key="sensor.id", nullable=False, index=True
    )

    sensor: Sensor = Relationship(
        back_populates="data",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SensorDataRead(SensorDataBase):
    id: UUID
    sensor_id: UUID


class SensorRead(SensorBase):
    id: UUID
    area_id: UUID
    geom: Any | None
    geom: Any | None = None
    coord_x: float | None = None
    coord_y: float | None = None
    coord_z: float | None = None
    coord_srid: int | None = None

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
                    values.coord_y = mapping["coordinates"][0]
                    values.coord_x = mapping["coordinates"][1]
                    values.coord_z = mapping["coordinates"][2]
                    values.geom = mapping
        elif isinstance(values.geom, dict):
            if values.geom is not None:
                values.coord_y = values.geom["coordinates"][0]
                values.coord_x = values.geom["coordinates"][1]
                values.coord_z = values.geom["coordinates"][2]
                values.geom = values.geom
        else:
            values.coord_y = None
            values.coord_x = None
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
    coord_y: float | None = None
    coord_x: float | None = None
    coord_z: float | None = None

    latitude: float | None = None
    longitude: float | None = None

    geom: Any | None = None

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
    instrumentdata: str | None = None


class SensorCreateFromGPX(SQLModel):
    # Model to accept the data from the GPSX file. Data stored in Base64 of gpx
    area_id: UUID
    gpsx_files: list[Any] | None = None
