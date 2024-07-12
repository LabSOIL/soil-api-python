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
    time_values: list = Field(default=[], sa_column=Column(JSON))
    raw_values: list = Field(default=[], sa_column=Column(JSON))
    baseline_spline: list = Field(default=[], sa_column=Column(JSON))
    baseline_values: list = Field(default=[], sa_column=Column(JSON))


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


class InstrumentExperimentChannelRead(InstrumentExperimentChannelBase):
    id: UUID


class InstrumentExperimentChannelUpdate(SQLModel):
    baseline_values: list


class InstrumentExperimentChannelCreate(InstrumentExperimentChannelBase):
    pass
