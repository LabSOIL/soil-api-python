from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from typing import Any
from uuid import UUID, uuid4


class PlotSampleBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
    )
    upper_depth_cm: float = Field(
        default=None,
        nullable=False,
    )
    lower_depth_cm: float = Field(
        default=None,
        nullable=False,
    )

    plot_id: UUID = Field(
        nullable=False,
        index=True,
        foreign_key="plot.id",
    )


class PlotSample(PlotSampleBase, table=True):
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


class PlotSampleRead(PlotSampleBase):
    id: UUID


class PlotSampleCreate(PlotSampleBase):
    pass


class PlotSampleUpdate(PlotSampleBase):
    pass
