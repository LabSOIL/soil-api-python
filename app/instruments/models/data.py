from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.instruments.models.experiment import InstrumentExperiment
    from app.instruments.models.channel import InstrumentExperimentChannel


class InstrumentExperimentDataBase(SQLModel):
    experiment_id: UUID = Field(
        foreign_key="instrumentexperiment.id", nullable=False
    )
    channel_id: UUID = Field(
        foreign_key="instrumentexperimentchannel.id", nullable=False
    )
    time: float = Field(nullable=False)
    value: float = Field(nullable=False)
    baseline_corrected: bool = Field(default=False)


class InstrumentExperimentData(InstrumentExperimentDataBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    iterator: int = Field(
        default=None, nullable=False, primary_key=True, index=True
    )
    id: UUID = Field(default_factory=uuid4, index=True, nullable=False)

    experiment: "InstrumentExperiment" = Relationship(back_populates="data")
    channel: "InstrumentExperimentChannel" = Relationship(
        back_populates="data",
        sa_relationship_kwargs={
            "lazy": "selectin",
        },
    )


class InstrumentExperimentDataRead(InstrumentExperimentDataBase):
    id: UUID


class InstrumentExperimentDataUpdate(InstrumentExperimentDataBase):
    pass


class InstrumentExperimentDataCreate(InstrumentExperimentDataBase):
    pass
