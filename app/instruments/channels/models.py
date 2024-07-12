from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
from sqlalchemy import JSON, Column
from typing import TYPE_CHECKING, Optional, Any
import datetime

if TYPE_CHECKING:
    from app.instruments.models.experiment import InstrumentExperiment
    from app.instruments.models.data import InstrumentExperimentData


class InstrumentExperimentChannelBase(SQLModel):
    channel_name: str = Field(nullable=False)
    experiment_id: UUID = Field(
        foreign_key="instrumentexperiment.id", nullable=False
    )
    baseline_spline: dict = Field(default={}, sa_column=Column(JSON))
    baseline_points: list = Field(default=[], sa_column=Column(JSON))


class InstrumentExperimentChannel(InstrumentExperimentChannelBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    iterator: int = Field(
        default=None, nullable=False, primary_key=True, index=True
    )
    id: UUID = Field(default_factory=uuid4, index=True, nullable=False)

    experiment: "InstrumentExperiment" = Relationship(
        back_populates="channels",
        sa_relationship_kwargs={
            "lazy": "selectin",
        },
    )
    data: list["InstrumentExperimentData"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={
            "lazy": "selectin",
        },
    )


class ExperimentWithData(SQLModel):
    name: str | None
    date: datetime.datetime | None
    filename: str | None
    id: UUID
    last_updated: datetime.datetime | None
    data: Any


class InstrumentExperimentChannelRead(InstrumentExperimentChannelBase):
    id: UUID
    experiment: Any
    data: Any


class InstrumentExperimentChannelUpdate(InstrumentExperimentChannelBase):
    pass


class InstrumentExperimentChannelCreate(InstrumentExperimentChannelBase):
    pass
