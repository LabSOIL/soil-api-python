from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship
from uuid import uuid4, UUID
from typing import List, TYPE_CHECKING
from app.sensors.models import SensorRead

if TYPE_CHECKING:
    from app.soil.profiles.models import SoilProfile


class SoilTypeBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str


class SoilType(SoilTypeBase, table=True):
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
    soil_profiles: "SoilProfile" = Relationship(
        back_populates="soil_type",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SoilTypeRead(SoilTypeBase):
    id: UUID  # We use the UUID as the return ID
    sensors: List["SensorRead"]


class SoilTypeCreate(SoilTypeBase):
    pass


class SoilTypeUpdate(SoilTypeBase):
    pass
